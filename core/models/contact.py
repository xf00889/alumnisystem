from django.db import models
from django.conf import settings
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _

class Address(models.Model):
    """
    Normalized address information for users
    """
    ADDRESS_TYPES = [
        ('HOME', 'Home'),
        ('WORK', 'Work'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='HOME')
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = CountryField(default='PH')
    postal_code = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ['-is_primary', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_primary']),
            models.Index(fields=['city', 'state', 'country']),
        ]

    def __str__(self):
        return f"{self.get_address_type_display()} address for {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary address per user
            Address.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class ContactInfo(models.Model):
    """
    Normalized contact information for users
    """
    CONTACT_TYPES = [
        ('PHONE', 'Phone Number'),
        ('EMAIL', 'Email Address'),
        ('LINKEDIN', 'LinkedIn Profile'),
        ('FACEBOOK', 'Facebook Profile'),
        ('TWITTER', 'Twitter Profile'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contact_info')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    contact_value = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Contact Information')
        verbose_name_plural = _('Contact Information')
        ordering = ['-is_primary', '-created_at']
        unique_together = [['user', 'contact_type', 'contact_value']]
        indexes = [
            models.Index(fields=['user', 'contact_type', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.get_contact_type_display()} for {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary contact per type per user
            ContactInfo.objects.filter(
                user=self.user,
                contact_type=self.contact_type,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    @property
    def display_value(self):
        """Return a formatted display value based on contact type"""
        if self.contact_type == 'PHONE':
            return PhoneNumberField().to_python(self.contact_value).as_national
        return self.contact_value 