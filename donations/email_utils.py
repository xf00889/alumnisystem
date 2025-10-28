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
    Send confirmation email when a donation is created
    """
    try:
        # Get donor information
        if donation.donor:
            donor_name = donation.donor.get_full_name() or donation.donor.username
            donor_email = donation.donor.email
        else:
            donor_name = donation.donor_name or "Anonymous Donor"
            donor_email = donation.donor_email
        
        # Skip if no email address
        if not donor_email:
            logger.warning(f"No email address for donation {donation.pk}")
            return False
        
        # Log email attempt
        logger.info(f"Attempting to send confirmation email for donation {donation.pk} to {donor_email}")
        
        # Prepare context
        context = {
            'donor_name': donor_name,
            'donor_email': donor_email,
            'amount': donation.amount,
            'reference_number': donation.reference_number,
            'campaign_name': donation.campaign.name,
            'campaign_description': donation.campaign.description,
            'donation_date': donation.donation_date,
            'is_anonymous': donation.is_anonymous,
            'message': donation.message,
            'status_display': donation.get_status_display(),
        }
        
        # Render email templates
        subject = f"Thank You for Your Donation - {donation.campaign.name}"
        html_content = render_to_string('emails/donation_confirmation.html', context)
        
        # Create plain text version
        text_content = f"""
Dear {donor_name},

Thank you for your generous donation of ₱{donation.amount} to {donation.campaign.name}.

Donation Details:
- Amount: ₱{donation.amount}
- Reference Number: {donation.reference_number}
- Campaign: {donation.campaign.name}
- Date: {donation.donation_date.strftime('%B %d, %Y at %I:%M %p')}
- Status: {donation.get_status_display()}

Your donation is being processed and will be verified within 24 hours. You'll receive another email once the verification is complete.

Thank you for supporting the NORSU Alumni System!

Best regards,
The NORSU Alumni System Team
        """
        
        # Send email
        result = send_email_with_provider(
            subject=subject,
            message=text_content,
            recipient_list=[donor_email],
            html_message=html_content,
            fail_silently=False
        )
        
        if result:
            logger.info(f"Donation confirmation email sent to {donor_email} for donation {donation.pk}")
            return True
        else:
            logger.error(f"Failed to send donation confirmation email to {donor_email} for donation {donation.pk}")
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
            donor_email = donation.donor.email
        else:
            donor_name = donation.donor_name or "Anonymous Donor"
            donor_email = donation.donor_email
        
        # Skip if no email address
        if not donor_email:
            logger.warning(f"No email address for donation {donation.pk}")
            return False
        
        # Skip if status hasn't changed or is still pending payment
        if old_status == donation.status or donation.status == 'pending_payment':
            return True
        
        # Prepare context
        context = {
            'donor_name': donor_name,
            'donor_email': donor_email,
            'amount': donation.amount,
            'reference_number': donation.reference_number,
            'campaign_name': donation.campaign.name,
            'donation_date': donation.donation_date,
            'status': donation.status,
            'status_display': donation.get_status_display(),
            'verification_date': donation.verification_date,
            'verified_by': donation.verified_by,
            'verification_notes': donation.verification_notes,
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
- Reference Number: {donation.reference_number}
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
            fail_silently=False
        )
        
        if result:
            logger.info(f"Donation status update email sent to {donor_email} for donation {donation.pk}")
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
            donor_email = donation.donor.email
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
            'reference_number': donation.reference_number,
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
- Reference Number: {donation.reference_number}
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
            fail_silently=False
        )
        
        if result:
            logger.info(f"Donation receipt email sent to {donor_email} for donation {donation.pk}")
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
