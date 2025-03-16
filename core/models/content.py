from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['is_published']),
        ]

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return f'Comment by {self.author.get_full_name()} on {self.post.title}'

class Reaction(models.Model):
    REACTION_TYPES = [
        ('LIKE', '👍'),
        ('LOVE', '❤️'),
        ('HAHA', '😄'),
        ('WOW', '😮'),
        ('SAD', '😢'),
        ('ANGRY', '😠'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Reaction')
        verbose_name_plural = _('Reactions')
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'reaction_type']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'{self.get_reaction_type_display()} by {self.user.get_full_name()} on {self.post.title}' 