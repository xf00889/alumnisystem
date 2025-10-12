from django.db import models
from django.utils.translation import gettext_lazy as _

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created' and 'modified' fields.
    """
    created = models.DateTimeField(
        _("Created"),
        auto_now_add=True,
        editable=False,
        help_text=_("The date and time this object was created.")
    )
    modified = models.DateTimeField(
        _("Modified"),
        auto_now=True,
        help_text=_("The date and time this object was last modified.")
    )

    class Meta:
        abstract = True
        ordering = ["-created"]

from .analytics import UserEngagement, EngagementScore
from .contact import Address, ContactInfo
from .content import Post, Comment, Reaction
from .notifications import Notification, NotificationPreference
from .page_content import SiteConfiguration, PageSection, Testimonial, StaffMember

__all__ = [
    'TimeStampedModel',
    'UserEngagement',
    'EngagementScore',
    'Address',
    'ContactInfo',
    'Post',
    'Comment',
    'Reaction',
    'Notification',
    'NotificationPreference',
    'SiteConfiguration',
    'PageSection',
    'Testimonial',
    'StaffMember',
]