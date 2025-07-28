from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone


class Connection(models.Model):
    """
    Model to represent connections/friendships between alumni users
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('BLOCKED', 'Blocked'),
    ]
    
    requester = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_connection_requests'
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_connection_requests'
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Connection')
        verbose_name_plural = _('Connections')
        unique_together = ['requester', 'receiver']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.requester.get_full_name()} -> {self.receiver.get_full_name()} ({self.status})"
    
    def clean(self):
        """Validate that users cannot connect to themselves"""
        if self.requester == self.receiver:
            raise ValidationError("Users cannot connect to themselves.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def are_connected(cls, user1, user2):
        """Check if two users are connected (accepted connection)"""
        return cls.objects.filter(
            models.Q(
                requester=user1, 
                receiver=user2, 
                status='ACCEPTED'
            ) | models.Q(
                requester=user2, 
                receiver=user1, 
                status='ACCEPTED'
            )
        ).exists()
    
    @classmethod
    def get_connection_status(cls, user1, user2):
        """Get the connection status between two users"""
        try:
            connection = cls.objects.get(
                models.Q(
                    requester=user1, 
                    receiver=user2
                ) | models.Q(
                    requester=user2, 
                    receiver=user1
                )
            )
            return connection.status
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_user_connections(cls, user, status='ACCEPTED'):
        """Get all connections for a user with specified status"""
        connections = cls.objects.filter(
            models.Q(requester=user) | models.Q(receiver=user),
            status=status
        )
        
        connected_users = []
        for connection in connections:
            if connection.requester == user:
                connected_users.append(connection.receiver)
            else:
                connected_users.append(connection.requester)
        
        return connected_users
    
    @classmethod
    def get_connections(cls, user):
        """Get all accepted connections for a user (alias for get_user_connections)"""
        return cls.get_user_connections(user, status='ACCEPTED')
    
    def accept(self):
        """Accept a pending connection request"""
        if self.status == 'PENDING':
            self.status = 'ACCEPTED'
            self.accepted_at = timezone.now()
            self.save()
        else:
            raise ValidationError("Only pending connections can be accepted.")
    
    def reject(self):
        """Reject a pending connection request"""
        if self.status == 'PENDING':
            self.status = 'REJECTED'
            self.save()
        else:
            raise ValidationError("Only pending connections can be rejected.")
    
    def block(self):
        """Block a connection"""
        self.status = 'BLOCKED'
        self.save()
    
    def get_other_user(self, user):
        """Get the other user in this connection"""
        if self.requester == user:
            return self.receiver
        elif self.receiver == user:
            return self.requester
        else:
            return None


class DirectConversation(models.Model):
    """
    Model to represent direct conversations between connected users
    (separate from mentorship conversations)
    """
    participants = models.ManyToManyField(
        User, 
        related_name='direct_conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Direct Conversation')
        verbose_name_plural = _('Direct Conversations')
        ordering = ['-updated_at']
    
    def __str__(self):
        participants_names = [user.get_full_name() for user in self.participants.all()]
        return f"Conversation: {' <-> '.join(participants_names)}"
    
    @property
    def last_message(self):
        """Get the last message in this conversation"""
        return self.direct_messages.first()
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()
    
    def get_unread_count_for_user(self, user):
        """Get count of unread messages for a specific user"""
        return self.direct_messages.filter(
            is_read=False
        ).exclude(sender=user).count()
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get or create a conversation between two users"""
        # Try to find existing conversation with both participants
        conversation = cls.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        ).first()
        
        if not conversation:
            # Create new conversation
            conversation = cls.objects.create()
            conversation.participants.add(user1, user2)
        
        return conversation


class DirectMessage(models.Model):
    """
    Model to represent individual messages in direct conversations
    """
    conversation = models.ForeignKey(
        DirectConversation, 
        on_delete=models.CASCADE, 
        related_name='direct_messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_direct_messages'
    )
    content = models.TextField()
    attachment = models.FileField(
        upload_to='connections/messages/', 
        blank=True, 
        null=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Direct Message')
        verbose_name_plural = _('Direct Messages')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} at {self.created_at}"
    
    def save(self, *args, **kwargs):
        """Update conversation's updated_at when a new message is saved"""
        super().save(*args, **kwargs)
        self.conversation.save()
