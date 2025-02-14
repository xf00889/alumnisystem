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
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)
    priority_level = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='ALL')
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
    
    def is_visible_to(self, user):
        """
        Check if the announcement is visible to the given user.
        """
        # Staff members can see all announcements
        if user.is_staff:
            return True
            
        # Check if announcement is active
        if not self.is_active:
            return False
            
        # Handle target audience restrictions
        if self.target_audience == 'ALL':
            return True
        elif self.target_audience == 'RECENT':
            # Get the user's graduation year from their profile
            try:
                graduation_year = user.profile.education_set.filter(is_primary=True).first().graduation_year
                current_year = timezone.now().year
                return (current_year - graduation_year) <= 5  # Consider "recent" as within 5 years
            except (AttributeError, TypeError):
                return False
        elif self.target_audience == 'DEPARTMENT':
            # Get the user's department from their profile
            try:
                user_program = user.profile.education_set.filter(is_primary=True).first().program
                return user_program == self.category.name
            except (AttributeError, TypeError):
                return False
                
        return True  # Default to visible if no restrictions apply