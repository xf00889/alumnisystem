"""Session-scoped push subscription removal on sign-out."""
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver


@receiver(user_logged_out)
def remove_push_subscription_for_signed_out_session(sender, request, user, **kwargs):
    if request is None or user is None:
        return
    endpoint = request.session.get('web_push_endpoint')
    if endpoint:
        from core.models import WebPushSubscription
        WebPushSubscription.objects.filter(user=user, endpoint=endpoint).delete()
