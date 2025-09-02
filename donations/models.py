from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import random
import string

# Create your models here.

class CampaignType(models.Model):
    """Model for different types of fundraising campaigns"""
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        verbose_name = _("Campaign Type")
        verbose_name_plural = _("Campaign Types")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Campaign(models.Model):
    """Model for fundraising campaigns"""
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('paused', _('Paused')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    )
    
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=220, unique=True)
    campaign_type = models.ForeignKey(
        CampaignType, 
        on_delete=models.PROTECT,
        related_name='campaigns',
        verbose_name=_("Campaign Type")
    )
    description = models.TextField(_("Description"))
    short_description = models.CharField(_("Short Description"), max_length=255)
    featured_image = models.ImageField(_("Featured Image"), upload_to='campaign_images/', blank=True, null=True)
    goal_amount = models.DecimalField(_("Goal Amount"), max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(_("Current Amount"), max_digits=12, decimal_places=2, default=0)
    start_date = models.DateTimeField(_("Start Date"), default=timezone.now)
    end_date = models.DateTimeField(_("End Date"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(_("Featured"), default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_campaigns',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate a slug from the name
            original_slug = slugify(self.name)
            
            # Check if the slug exists
            queryset = Campaign.objects.all()
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
            # If the slug already exists, add a number suffix until it's unique
            slug = original_slug
            counter = 1
            while queryset.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('donations:campaign_detail', kwargs={'slug': self.slug})
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def progress_percentage(self):
        if self.goal_amount <= 0:
            return 0
        progress = (float(self.current_amount) / float(self.goal_amount)) * 100
        return min(round(progress), 100)  # Cap at 100%
    
    @property
    def days_remaining(self):
        if not self.end_date:
            return None
        remaining = (self.end_date - timezone.now()).days
        return max(0, remaining)
    
    @property
    def donors_count(self):
        return self.donations.filter(status='completed').count()


class CampaignUpdate(models.Model):
    """Model for updates/news about campaigns"""
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='updates',
        verbose_name=_("Campaign")
    )
    title = models.CharField(_("Title"), max_length=200)
    content = models.TextField(_("Content"))
    image = models.ImageField(_("Image"), upload_to='campaign_updates/', blank=True, null=True)
    is_featured = models.BooleanField(_("Featured"), default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='campaign_updates',
        verbose_name=_("Created By")
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    updated = models.DateTimeField(_("Updated"), auto_now=True)
    
    class Meta:
        verbose_name = _("Campaign Update")
        verbose_name_plural = _("Campaign Updates")
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.title} - {self.campaign.name}"


class Donation(models.Model):
    """Model for donations made to campaigns"""
    STATUS_CHOICES = (
        ('pending_payment', _('Pending Payment')),
        ('pending_verification', _('Pending Verification')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('disputed', _('Disputed')),
    )

    PAYMENT_METHOD_CHOICES = (
        ('gcash', _('GCash')),
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='donations',
        verbose_name=_("Campaign")
    )
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations',
        verbose_name=_("Donor")
    )
    donor_name = models.CharField(_("Donor Name"), max_length=200, blank=True)
    donor_email = models.EmailField(_("Donor Email"), blank=True)
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    donation_date = models.DateTimeField(_("Donation Date"), default=timezone.now)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES, default='gcash')
    is_anonymous = models.BooleanField(_("Anonymous"), default=False)
    message = models.TextField(_("Message"), blank=True)

    # Enhanced reference and verification fields
    reference_number = models.CharField(_("Reference Number"), max_length=30, unique=True, blank=True)
    payment_proof = models.ImageField(_("Payment Proof"), upload_to='payment_proofs/', blank=True, null=True)
    gcash_transaction_id = models.CharField(_("GCash Transaction ID"), max_length=50, blank=True)
    verification_notes = models.TextField(_("Verification Notes"), blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_donations',
        verbose_name=_("Verified By")
    )
    verification_date = models.DateTimeField(_("Verification Date"), null=True, blank=True)

    receipt_sent = models.BooleanField(_("Receipt Sent"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Donation")
        verbose_name_plural = _("Donations")
        ordering = ['-donation_date']
    
    def __str__(self):
        if self.is_anonymous:
            return f"Anonymous donation of {self.amount} to {self.campaign.name}"
        elif self.donor:
            return f"Donation by {self.donor.get_full_name()} to {self.campaign.name}"
        else:
            return f"Donation by {self.donor_name} to {self.campaign.name}"

    def generate_reference_number(self):
        """Generate unique reference number in format NORSU-YYYY-HHMMSS-XXX"""
        now = timezone.now()
        year = now.strftime('%Y')
        time_part = now.strftime('%H%M%S')

        # Generate random 3-character suffix
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

        # Create reference number
        reference = f"NORSU-{year}-{time_part}-{random_suffix}"

        # Ensure uniqueness
        counter = 1
        original_reference = reference
        while Donation.objects.filter(reference_number=reference).exists():
            reference = f"{original_reference}-{counter:02d}"
            counter += 1

        return reference
    
    def save(self, *args, **kwargs):
        # Generate reference number if not set
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()

        # If this is a completed donation and it's a new record or the status has changed
        is_new = self.pk is None
        if not is_new:
            old_status = Donation.objects.get(pk=self.pk).status
            status_changed = old_status != self.status
        else:
            status_changed = False

        # Set verification date when status changes to completed
        if self.status == 'completed' and (is_new or status_changed) and not self.verification_date:
            self.verification_date = timezone.now()

        super().save(*args, **kwargs)

        # Update campaign amount if status is completed
        if self.status == 'completed' and (is_new or status_changed):
            self.campaign.current_amount = self.campaign.donations.filter(
                status='completed'
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            self.campaign.save()

        # If status changed from completed to something else, recalculate
        if not is_new and status_changed and old_status == 'completed' and self.status != 'completed':
            self.campaign.current_amount = self.campaign.donations.filter(
                status='completed'
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            self.campaign.save()
    
    def get_absolute_url(self):
        return reverse('donations:donation_confirmation', kwargs={'pk': self.pk})


class DonorRecognition(models.Model):
    """Model for recognizing donors at different levels"""
    name = models.CharField(_("Level Name"), max_length=100)
    description = models.TextField(_("Description"))
    minimum_amount = models.DecimalField(_("Minimum Amount"), max_digits=10, decimal_places=2)
    badge_image = models.ImageField(_("Badge Image"), upload_to='donor_badges/', blank=True, null=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Donor Recognition")
        verbose_name_plural = _("Donor Recognitions")
        ordering = ['minimum_amount']

    def __str__(self):
        return f"{self.name} (₱{self.minimum_amount}+)"


class GCashConfig(models.Model):
    """Model for storing GCash payment configuration"""
    name = models.CharField(_("Configuration Name"), max_length=100, default="Default GCash")
    gcash_number = models.CharField(_("GCash Number"), max_length=15)
    account_name = models.CharField(_("Account Name"), max_length=100)
    qr_code_image = models.ImageField(_("QR Code Image"), upload_to='gcash_qr/')
    is_active = models.BooleanField(_("Active"), default=True)
    instructions = models.TextField(_("Payment Instructions"), blank=True, help_text=_("Additional instructions for donors"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("GCash Configuration")
        verbose_name_plural = _("GCash Configurations")
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} - {self.gcash_number}"

    @classmethod
    def get_active_config(cls):
        """Get the active GCash configuration that has a QR code uploaded"""
        return cls.objects.filter(is_active=True).exclude(qr_code_image='').first()


class FraudAlert(models.Model):
    """Model for tracking fraud alerts and suspicious activities"""
    ALERT_TYPES = (
        ('duplicate_image', _('Duplicate Payment Image')),
        ('suspicious_amount', _('Suspicious Amount Pattern')),
        ('rapid_donations', _('Rapid Multiple Donations')),
        ('unusual_location', _('Unusual Location')),
        ('blacklisted_user', _('Blacklisted User')),
        ('manual_review', _('Manual Review Required')),
    )

    SEVERITY_LEVELS = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    )

    STATUS_CHOICES = (
        ('pending', _('Pending Review')),
        ('investigating', _('Under Investigation')),
        ('resolved', _('Resolved')),
        ('false_positive', _('False Positive')),
    )

    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='fraud_alerts')
    alert_type = models.CharField(_("Alert Type"), max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(_("Severity"), max_length=10, choices=SEVERITY_LEVELS, default='medium')
    status = models.CharField(_("Status"), max_length=15, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(_("Description"))
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_fraud_alerts',
        verbose_name=_("Reviewed By")
    )
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    resolution_notes = models.TextField(_("Resolution Notes"), blank=True)

    class Meta:
        verbose_name = _("Fraud Alert")
        verbose_name_plural = _("Fraud Alerts")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.donation.reference_number}"


class BlacklistedEntity(models.Model):
    """Model for managing blacklisted users, emails, IPs, etc."""
    ENTITY_TYPES = (
        ('email', _('Email Address')),
        ('ip', _('IP Address')),
        ('phone', _('Phone Number')),
        ('name', _('Name Pattern')),
        ('gcash_number', _('GCash Number')),
    )

    entity_type = models.CharField(_("Entity Type"), max_length=15, choices=ENTITY_TYPES)
    value = models.CharField(_("Value"), max_length=255)
    reason = models.TextField(_("Reason for Blacklisting"))
    is_active = models.BooleanField(_("Active"), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_blacklists',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Blacklisted Entity")
        verbose_name_plural = _("Blacklisted Entities")
        unique_together = ['entity_type', 'value']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_entity_type_display()}: {self.value}"

    def is_expired(self):
        """Check if blacklist entry has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
