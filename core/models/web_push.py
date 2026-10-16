"""Browser push subscriptions and durable idempotent notification delivery."""
from django.conf import settings
from django.db import models


class WebPushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='web_push_subscriptions')
    endpoint = models.URLField(max_length=2048, unique=True)
    p256dh = models.CharField(max_length=512)
    auth = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=['user'], name='webpush_user_idx')]


class WebPushDelivery(models.Model):
    """One send attempt lifecycle per notification and browser endpoint."""
    notification = models.ForeignKey('core.Notification', on_delete=models.CASCADE, related_name='web_push_deliveries')
    subscription = models.ForeignKey(WebPushSubscription, on_delete=models.CASCADE, related_name='deliveries')
    status = models.CharField(max_length=12, default='pending', choices=[('pending','Pending'),('sent','Sent'),('failed','Failed')])
    attempts = models.PositiveSmallIntegerField(default=0)
    retry_after = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['notification', 'subscription'], name='webpush_notification_subscription_once')]
        indexes = [models.Index(fields=['status', 'retry_after'], name='webpush_due_idx')]
