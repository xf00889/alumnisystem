from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Donation, DonorRecognition
from .email_utils import send_donation_confirmation_email, send_donation_status_update_email, send_donation_receipt_email
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Donation)
def send_donation_emails(sender, instance, created, **kwargs):
    """
    Send appropriate emails when donation is created or status changes
    """
    try:
        if created:
            # Send confirmation email when donation is first created
            logger.info(f"Sending confirmation email for new donation {instance.pk}")
            try:
                send_donation_confirmation_email(instance)
            except Exception as e:
                logger.error(f"Failed to send confirmation email for new donation {instance.pk}: {str(e)}")
        elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
            # Send emails when status changes
            logger.info(f"Donation {instance.pk} status changed from {instance._old_status} to {instance.status}")
            
            # Send confirmation email when payment proof is submitted (status changes to pending_verification)
            if instance.status == 'pending_verification' and instance._old_status == 'pending_payment':
                logger.info(f"Sending confirmation email for donation {instance.pk} after payment proof submission")
                send_donation_confirmation_email(instance)
            
            # Send status update email for other status changes
            elif instance.status in ['completed', 'failed', 'disputed']:
                logger.info(f"Sending status update email for donation {instance.pk}")
                send_donation_status_update_email(instance, instance._old_status)
                
                # Send receipt email for completed donations
                if instance.status == 'completed' and not instance.receipt_sent:
                    logger.info(f"Sending receipt email for completed donation {instance.pk}")
                    send_donation_receipt_email(instance)
                    
    except Exception as e:
        logger.error(f"Error in donation email signals for donation {instance.pk}: {str(e)}")

@receiver(pre_save, sender=Donation)
def store_old_status(sender, instance, **kwargs):
    """
    Store the old status before saving to detect changes
    """
    if instance.pk:
        try:
            old_instance = Donation.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Donation.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None