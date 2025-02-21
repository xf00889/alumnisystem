from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Conversation(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)  # For group chats
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    is_group_chat = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_conversations')
    photo = models.ImageField(upload_to='chat/group_photos/', null=True, blank=True)  # Add photo field

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.is_group_chat:
            return f"{self.name} (Group)"
        return f"Chat between {', '.join(self.participants.values_list('username', flat=True))}"

    def get_other_participant(self, user=None):
        """Get the other participant in a private chat.
        
        Args:
            user: The user to get the other participant for. If not provided,
                 assumes we want the other participant relative to created_by.
        
        Returns:
            User: The other participant in the conversation.
            None: If this is a group chat or if user is not in the conversation.
        """
        if self.is_group_chat:
            return None
            
        if user is None:
            user = self.created_by
            
        try:
            return self.participants.exclude(id=user.id).first()
        except User.DoesNotExist:
            return None

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

class UserBlock(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"
