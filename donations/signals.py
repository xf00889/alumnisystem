from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Donation, DonorRecognition

# TODO: Implement proper donor recognition tracking
# The current DonorRecognition model is for recognition levels, not individual recognitions
# These signals are commented out until a proper DonorRecognitionRecord model is created

# @receiver(post_save, sender=Donation)
# def create_donor_recognition(sender, instance, created, **kwargs):
#     """
#     Create donor recognition records when a donation is completed
#     """
#     if created and instance.status == 'completed':
#         # Create thank you email recognition
#         DonorRecognition.objects.create(
#             donation=instance,
#             recognition_type='thank_you_email',
#             status='pending'
#         )
#
#         # Create public acknowledgment recognition if not anonymous
#         if not instance.is_anonymous:
#             DonorRecognition.objects.create(
#                 donation=instance,
#                 recognition_type='public_acknowledgment',
#                 status='pending'
#             )

# @receiver(post_save, sender=Donation)
# def update_donation_status(sender, instance, **kwargs):
#     """
#     Update donation status based on changes
#     """
#     # If donation status changed to completed, update recognition records
#     if instance.status == 'completed' and not instance.receipt_sent:
#         # Find all pending recognitions for this donation
#         recognitions = DonorRecognition.objects.filter(
#             donation=instance,
#             status='pending'
#         )
#
#         # Update them to sent
#         for recognition in recognitions:
#             recognition.status = 'sent'
#             recognition.date_sent = timezone.now()
#             recognition.save()