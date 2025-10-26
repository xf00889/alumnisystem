from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from taggit.managers import TaggableManager
from django.utils import timezone

class AlumniGroup(models.Model):
    GROUP_TYPES = (
        ('AUTO', 'Automatic'),
        ('MANUAL', 'Manual'),
        ('HYBRID', 'Hybrid'),
    )

    VISIBILITY_CHOICES = (
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
        ('RESTRICTED', 'Restricted'),
    )

    CAMPUS_CHOICES = (
        ('MAIN', 'NORSU Main Campus'),
        ('GUIHULNGAN', 'NORSU Guihulngan Campus'),
        ('SIATON', 'NORSU Siaton Campus'),
        ('PAMPLONA', 'NORSU Pamplona Campus'),
        ('BAIS', 'NORSU Bais Campus'),
        ('BSC', 'NORSU BSC (Bayawan-Sta. Catalina) Campus'),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField()
    group_type = models.CharField(max_length=10, choices=GROUP_TYPES)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PUBLIC')
    
    # Group Criteria
    batch_start_year = models.IntegerField(null=True, blank=True)
    batch_end_year = models.IntegerField(null=True, blank=True)
    course = models.CharField(max_length=100, blank=True)
    campus = models.CharField(max_length=20, choices=CAMPUS_CHOICES, default='MAIN')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups'
    )
    
    # Group Settings
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    has_security_questions = models.BooleanField(default=False)
    require_post_approval = models.BooleanField(default=True)
    max_members = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)]
    )
    
    # Additional Features
    tags = TaggableManager(blank=True)
    cover_image = models.ImageField(upload_to='group_covers/%Y/%m/', blank=True, null=True)
    profile_photo = models.ImageField(upload_to='group_profiles/%Y/%m/', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name', 'group_type', 'visibility']),
            models.Index(fields=['batch_start_year', 'batch_end_year']),
            models.Index(fields=['course', 'campus']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Check if slug exists and append number if necessary
            original_slug = self.slug
            counter = 1
            while AlumniGroup.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        return self.memberships.count()

    @property
    def active_members_count(self):
        return self.memberships.filter(is_active=True).count()

    @property
    def pending_memberships(self):
        return self.memberships.filter(status='PENDING')

class GroupMembership(models.Model):
    ROLE_CHOICES = (
        ('MEMBER', 'Member'),
        ('MODERATOR', 'Moderator'),
        ('ADMIN', 'Admin'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('BLOCKED', 'Blocked'),
    )

    group = models.ForeignKey(AlumniGroup, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_active_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('group', 'user')
        indexes = [
            models.Index(fields=['group', 'user', 'role', 'status']),
        ]

class GroupEvent(models.Model):
    group = models.ForeignKey(AlumniGroup, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.CharField(max_length=255)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_participants = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    @property
    def location_point(self):
        if self.latitude and self.longitude:
            return {'latitude': float(self.latitude), 'longitude': float(self.longitude)}
        return None

class GroupDiscussion(models.Model):
    group = models.ForeignKey(AlumniGroup, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)

class GroupDiscussionComment(models.Model):
    discussion = models.ForeignKey(GroupDiscussion, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

class GroupActivity(models.Model):
    ACTIVITY_TYPES = (
        ('JOIN', 'Member Joined'),
        ('LEAVE', 'Member Left'),
        ('POST', 'New Post'),
        ('EVENT', 'New Event'),
        ('COMMENT', 'New Comment'),
        ('UPDATE', 'Group Updated'),
    )

    group = models.ForeignKey(AlumniGroup, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Group Activities'

class GroupFile(models.Model):
    group = models.ForeignKey(AlumniGroup, on_delete=models.CASCADE, related_name='files')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='group_files/%Y/%m/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    download_count = models.PositiveIntegerField(default=0)

class GroupAnalytics(models.Model):
    group = models.OneToOneField(AlumniGroup, on_delete=models.CASCADE, related_name='analytics')
    total_members = models.PositiveIntegerField(default=0)
    active_members = models.PositiveIntegerField(default=0)
    total_posts = models.PositiveIntegerField(default=0)
    total_events = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Group Analytics'

class SecurityQuestion(models.Model):
    group = models.ForeignKey(AlumniGroup, on_delete=models.CASCADE, related_name='security_questions')
    question = models.CharField(max_length=255)
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.group.name} - {self.question}"

class SecurityQuestionAnswer(models.Model):
    question = models.ForeignKey(SecurityQuestion, on_delete=models.CASCADE, related_name='answers')
    membership = models.ForeignKey(GroupMembership, on_delete=models.CASCADE, related_name='security_answers')
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviewed_answers'
    )

    def __str__(self):
        return f"Answer for {self.question.question} by {self.membership.user.get_full_name()}"

class GroupMessage(models.Model):
    group = models.ForeignKey('AlumniGroup', on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.created_at}"

class Post(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    group = models.ForeignKey('AlumniGroup', on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, through='PostLike', related_name='liked_posts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_posts'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.get_full_name()}'s post in {self.group.name} ({self.get_status_display()})"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def comments_count(self):
        return self.comments.count()

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.post}" 