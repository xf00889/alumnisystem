from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings
from django.utils.translation import gettext_lazy as _

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
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', _('Credit Card')),
        ('bank_transfer', _('Bank Transfer')),
        ('paypal', _('PayPal')),
        ('cash', _('Cash')),
        ('check', _('Check')),
        ('other', _('Other')),
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
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHOD_CHOICES, default='credit_card')
    is_anonymous = models.BooleanField(_("Anonymous"), default=False)
    message = models.TextField(_("Message"), blank=True)
    reference_number = models.CharField(_("Reference Number"), max_length=100, blank=True)
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
    
    def save(self, *args, **kwargs):
        # If this is a completed donation and it's a new record or the status has changed
        is_new = self.pk is None
        if not is_new:
            old_status = Donation.objects.get(pk=self.pk).status
            status_changed = old_status != self.status
        else:
            status_changed = False
            
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
