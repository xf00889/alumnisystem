from django import template
from accounts.email_login_mfa import _stage, email_enabled, verified_email

register = template.Library()

@register.simple_tag(takes_context=True)
def can_try_email_login(context):
    request = context.get('request')
    if not request:
        return False
    stage = _stage(request)
    return bool(stage and email_enabled(stage.login.user) and verified_email(stage.login.user))
