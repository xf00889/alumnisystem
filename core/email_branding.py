"""Reusable HTML presentation for outgoing NORSU transactional emails.

Never modify the plain-text message, transport, recipient, or security token.
Django's escaping and urlize filter keep supplied plain-text content as text.
"""
from django.template.loader import render_to_string
from django.utils.html import urlize
from django.utils.safestring import mark_safe


def brand_transactional_email(subject, message, html_message=None):
    """Return HTML with a shared university header and footer.

    Existing designed templates render their own branded frame; don't nest a
    document inside another. Legacy HTML remains unchanged for compatibility.
    All plain-text-only senders receive the standard responsive HTML version.
    """
    if html_message:
        return html_message
    # urlize escapes non-URL text when autoescape=True. No caller-provided HTML
    # is trusted; line breaks are added only after HTML escaping.
    safe_lines = urlize(message or '', autoescape=True).replace('\n', '<br>\n')
    return render_to_string('emails/plain_message.html', {
        'email_subject': subject,
        'email_body_html': mark_safe(safe_lines),
    })
