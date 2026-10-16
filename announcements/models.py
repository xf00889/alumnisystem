from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Clear cache when category is updated
        cache.delete('announcement_categories')
        super().save(*args, **kwargs)

class Announcement(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    TARGET_CHOICES = [
        ('ALL', 'All Alumni'),
        ('RECENT', 'Recent Graduates'),
        ('DEPARTMENT', 'Specific Department'),
        ('BATCH', 'Graduation Batch'),
        ('COLLEGE', 'College'),
        ('PROGRAM', 'Degree Program'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)
    priority_level = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='ALL')
    target_value = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Batch year, college code, or degree-program code/name for a targeted announcement.',
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='announcements')
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-date_posted']
        indexes = [
            models.Index(fields=['-date_posted']),
            models.Index(fields=['category', '-date_posted']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('announcement-detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Clear cache when announcement is updated
        cache.delete(f'announcement_{self.pk}')
        cache.delete('announcement_list')
        super().save(*args, **kwargs)
    
    @property
    def target_description(self):
        """Safe human-readable target for the admin directory and preview."""
        from .audience import audience_label
        return audience_label(self)

    def is_visible_to(self, user):
        """Use the same audience rules for cards, details, searches and emails."""
        from .audience import visible_announcements_for
        return visible_announcements_for(user).filter(pk=self.pk).exists()
