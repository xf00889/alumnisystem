from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from accounts.models import MentorshipRequest

User = get_user_model()

class Conversation(models.Model):
    """
    Model to represent a conversation between users
    Can be either mentorship-based or direct conversation
    """
    # Optional mentorship relationship (for mentorship conversations)
    mentorship = models.OneToOneField(
        MentorshipRequest, 
        on_delete=models.CASCADE, 
        related_name='conversation',
        blank=True,
        null=True
    )
    
    # Direct conversation participants (for non-mentorship conversations)
    participant_1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_1',
        blank=True,
        null=True
    )
    participant_2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant_2',
        blank=True,
        null=True
    )
    
    # Conversation type
    CONVERSATION_TYPES = [
        ('mentorship', 'Mentorship'),
        ('direct', 'Direct Message'),
    ]
    conversation_type = models.CharField(
        max_length=20,
        choices=CONVERSATION_TYPES,
        default='mentorship'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-updated_at']
        # Ensure unique direct conversations between two users
        constraints = [
            models.UniqueConstraint(
                fields=['participant_1', 'participant_2'],
                condition=models.Q(conversation_type='direct'),
                name='unique_direct_conversation'
            )
        ]
    
    def __str__(self):
        if self.conversation_type == 'mentorship' and self.mentorship:
            return f"Mentorship Conversation: {self.mentorship.mentee.get_full_name()} <-> {self.mentorship.mentor.user.get_full_name()}"
        elif self.conversation_type == 'direct':
            return f"Direct Conversation: {self.participant_1.get_full_name()} <-> {self.participant_2.get_full_name()}"
        return f"Conversation {self.id}"
    
    @property
    def participants(self):
        """Return both participants in the conversation"""
        if self.conversation_type == 'mentorship' and self.mentorship:
            return [self.mentorship.mentee, self.mentorship.mentor.user]
        elif self.conversation_type == 'direct':
            return [self.participant_1, self.participant_2]
        return []
    
    @property
    def last_message(self):
        """Get the last message in this conversation"""
        return self.messages.first()
    
    def get_unread_count_for_user(self, user):
        """Get count of unread messages for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if self.conversation_type == 'mentorship' and self.mentorship:
            if user == self.mentorship.mentee:
                return self.mentorship.mentor.user
            return self.mentorship.mentee
        elif self.conversation_type == 'direct':
            if user == self.participant_1:
                return self.participant_2
            return self.participant_1
        return None
    
    def save(self, *args, **kwargs):
        """Ensure data consistency when saving"""
        if self.conversation_type == 'direct':
            # Ensure participant_1 has lower ID than participant_2 for consistency
            if self.participant_1 and self.participant_2 and self.participant_1.id > self.participant_2.id:
                self.participant_1, self.participant_2 = self.participant_2, self.participant_1
        super().save(*args, **kwargs)

class Message(models.Model):
    """
    Model to represent individual messages in a conversation
    """
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    content = models.TextField()
    attachment = models.FileField(
        upload_to='mentorship/messages/', 
        blank=True, 
        null=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} at {self.created_at}"
    
    def save(self, *args, **kwargs):
        """Update conversation's updated_at when a new message is saved"""
        super().save(*args, **kwargs)
        self.conversation.save()  # This will update the updated_at field