"""
Email utilities for donation-related notifications
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from core.email_utils import send_email_with_provider
import logging

logger = logging.getLogger(__name__)

def send_donation_confirmation_email(donation):
    """
    Send payment-proof acknowledgement after a submitted GCash transaction
    """
    try:
        # Get donor information
        if donation.donor:
            donor_name = donation.donor.get_full_name() or donation.donor.username
            donor_email = donation.donor.email or donation.donor_email
        else:
            donor_name = donation.donor_name or "Anonymous Donor"
            donor_email = donation.donor_email
        
        # Skip if no email address
        if not donor_email:
            logger.warning(f"No email address for donation {donation.pk}")
            return False
        
        # Log the donation identifier, never personal details or full receipts.
        logger.info('Preparing proof acknowledgement for donation %s (status=%s)', donation.pk, donation.status)
        
        if not donation.reference_number or not donation.payment_proof:
            logger.error('Donation %s is missing persisted GCash proof/reference; acknowledgement not sent', donation.pk)
            return False

        # Prepare context
        context = {
            'donor_name': donor_name,
            'donor_email': donor_email,
            'amount': donation.amount,
            'reference_number': donation.reference_number or 'Not provided',
            'campaign_name': donation.campaign.name,
            'campaign_description': donation.campaign.description,
            'donation_date': donation.donation_date,
            'is_anonymous': donation.is_anonymous,
            'message': donation.message,
            'status_display': donation.get_status_display(),
        }
        
        # Render email templates
        subject = f"Payment proof received — awaiting verification: {donation.campaign.name}"
        html_content = render_to_string('emails/donation_confirmation.html', context)
        
        # Create plain text version
        text_content = f"""
Dear {donor_name},

We received your payment proof for a proposed donation of ₱{donation.amount} to {donation.campaign.name}. This is not confirmation of payment.

Donation Details:
- Amount: ₱{donation.amount}
- Reference Number: {donation.reference_number or 'Not provided'}
- Campaign: {donation.campaign.name}
- Date: {donation.donation_date.strftime('%B %d, %Y at %I:%M %p')}
- Status: {donation.get_status_display()}

Our alumni office will reconcile the GCash transaction. You will receive a status update after review.

Thank you for supporting the NORSU Alumni System!

Best regards,
The NORSU Alumni System Team
        """
        
        # Send email using email provider
        logger.info('Sending donation acknowledgement through configured backend for donation %s', donation.pk)
        result = send_email_with_provider(
            subject=subject,
            message=text_content,
            recipient_list=[donor_email],
            html_message=html_content,
            fail_silently=False,
            require_delivery=True,
        )
        
        logger.info('Donation acknowledgement backend result for donation %s: %s', donation.pk, bool(result))
        
        if result:
            logger.info('Donation proof notification handled by configured email backend for donation %s', donation.pk)
            return True
        else:
            logger.error('Donation proof notification was not accepted by email backend for donation %s', donation.pk)
            return False
            
    except Exception as e:
        logger.error(f"Error sending donation confirmation email for donation {donation.pk}: {str(e)}")
        return False

def send_donation_status_update_email(donation, old_status=None):
    """
    Send status update email when donation status changes
    """
    try:
        # Get donor information
        if donation.donor:
            donor_name = donation.donor.get_full_name() or donation.donor.username
            donor_email = donation.donor.email or donation.donor_email
        else:
            donor_name = donation.donor_name or "Anonymous Donor"
            donor_email = donation.donor_email
        
        # Skip if no email address
        if not donor_email:
            logger.warning(f"No email address for donation {donation.pk}")
            return False
        
        # No email for unchanged state; do notify on an admin status reset.
        if old_status == donation.status:
            return True
        
        # Prepare context
        context = {
            'donor_name': donor_name,
            'donor_email': donor_email,
            'amount': donation.amount,
            'reference_number': donation.reference_number or 'Not provided',
            'campaign_name': donation.campaign.name,
            'donation_date': donation.donation_date,
            'status': donation.status,
            'status_display': donation.get_status_display(),
            'verification_date': donation.verification_date,
            'verified_by': donation.verified_by,
        }
        
        # Render email templates
        subject = f"Donation Status Update - {donation.campaign.name}"
        html_content = render_to_string('emails/donation_status_update.html', context)
        
        # Create plain text version
        text_content = f"""
Dear {donor_name},

Your donation status has been updated.

Donation Details:
- Amount: ₱{donation.amount}
- Reference Number: {donation.reference_number or 'Not provided'}
- Campaign: {donation.campaign.name}
- Date: {donation.donation_date.strftime('%B %d, %Y at %I:%M %p')}
- Status: {donation.get_status_display()}

"""
        
        # Add status-specific message
        if donation.status == 'completed':
            text_content += """
Congratulations! Your donation has been successfully verified and processed. Thank you for your generous contribution!
            """
        elif donation.status == 'failed':
            text_content += """
Unfortunately, we were unable to verify your payment. Please contact our support team for assistance.
            """
        elif donation.status == 'pending_verification':
            text_content += """
Your donation is currently being reviewed by our verification team. This process typically takes 24 hours.
            """
        elif donation.status == 'disputed':
            text_content += """
Your donation has been flagged for manual review to ensure everything is in order. Our team will review it and contact you if needed.
            """
        
        elif donation.status == 'refunded':
            text_content += """
Your donation was marked refunded. Contact our alumni office if you need details about the refund transaction.
            """
        elif donation.status == 'cancelled':
            text_content += """
Your unpaid donation request was cancelled. If you already sent a GCash transfer, contact the alumni office immediately.
            """
        elif donation.status == 'pending_payment':
            text_content += """
Your donation is awaiting payment. Please follow the original payment instructions before uploading proof.
            """

        text_content += """

If you have any questions, please contact our support team.

Best regards,
The NORSU Alumni System Team
        """
        
        # Send email
        result = send_email_with_provider(
            subject=subject,
            message=text_content,
            recipient_list=[donor_email],
            html_message=html_content,
            fail_silently=False,
            require_delivery=True,
        )
        
        if result:
            logger.info('Donation status notification accepted by delivery backend for donation %s', donation.pk)
            return True
        else:
            logger.error(f"Failed to send donation status update email to {donor_email} for donation {donation.pk}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending donation status update email for donation {donation.pk}: {str(e)}")
        return False

def send_donation_receipt_email(donation):
    """
    Send receipt email for completed donations
    """
    try:
        # Only send for completed donations
        if donation.status != 'completed':
            return False
        
        # Get donor information
        if donation.donor:
            donor_name = donation.donor.get_full_name() or donation.donor.username
            donor_email = donation.donor.email or donation.donor_email
        else:
            donor_name = donation.donor_name or "Anonymous Donor"
            donor_email = donation.donor_email
        
        # Skip if no email address
        if not donor_email:
            logger.warning(f"No email address for donation {donation.pk}")
            return False
        
        # Prepare context
        context = {
            'donor_name': donor_name,
            'donor_email': donor_email,
            'amount': donation.amount,
            'reference_number': donation.reference_number or 'Not provided',
            'campaign_name': donation.campaign.name,
            'campaign_description': donation.campaign.description,
            'donation_date': donation.donation_date,
            'verification_date': donation.verification_date,
            'is_anonymous': donation.is_anonymous,
            'message': donation.message,
        }
        
        # Render email templates
        subject = f"Donation Receipt - {donation.campaign.name}"
        html_content = render_to_string('emails/donation_receipt.html', context)
        
        # Create plain text version
        text_content = f"""
Dear {donor_name},

Thank you for your donation! Here is your official receipt.

DONATION RECEIPT
================

Donation Details:
- Amount: ₱{donation.amount}
- Reference Number: {donation.reference_number or 'Not provided'}
- Campaign: {donation.campaign.name}
- Date: {donation.donation_date.strftime('%B %d, %Y at %I:%M %p')}
- Verified: {donation.verification_date.strftime('%B %d, %Y at %I:%M %p') if donation.verification_date else 'N/A'}

This receipt serves as proof of your charitable contribution to the NORSU Alumni System.

Thank you for your generous support!

Best regards,
The NORSU Alumni System Team
        """
        
        # Send email
        result = send_email_with_provider(
            subject=subject,
            message=text_content,
            recipient_list=[donor_email],
            html_message=html_content,
            fail_silently=False,
            require_delivery=True,
        )
        
        if result:
            logger.info('Donation receipt accepted by delivery backend for donation %s', donation.pk)
            # Mark receipt as sent
            donation.receipt_sent = True
            donation.save(update_fields=['receipt_sent'])
            return True
        else:
            logger.error(f"Failed to send donation receipt email to {donor_email} for donation {donation.pk}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending donation receipt email for donation {donation.pk}: {str(e)}")
        return False
