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
    Model to represent direct conversations and group chats between connected users
    (separate from mentorship conversations)
    """
    CONVERSATION_TYPES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
    ]

    participants = models.ManyToManyField(
        User,
        related_name='direct_conversations'
    )
    conversation_type = models.CharField(
        max_length=10,
        choices=CONVERSATION_TYPES,
        default='direct'
    )
    group_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Name for group chats (required for group type)'
    )
    group_photo = models.ImageField(
        upload_to='connections/group_photos/',
        blank=True,
        null=True,
        help_text='Group photo for group chats'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_conversations',
        help_text='User who created this conversation'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Direct Conversation')
        verbose_name_plural = _('Direct Conversations')
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.conversation_type == 'group' and self.group_name:
            return f"Group: {self.group_name}"
        participants_names = [user.get_full_name() for user in self.participants.all()]
        return f"Conversation: {' <-> '.join(participants_names)}"
    
    @property
    def last_message(self):
        """Get the last message in this conversation"""
        return self.direct_messages.first()
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation (for direct messages only)"""
        if self.conversation_type == 'direct':
            return self.participants.exclude(id=user.id).first()
        return None

    def get_other_participants(self, user):
        """Get all other participants in the conversation (useful for group chats)"""
        return self.participants.exclude(id=user.id)

    @property
    def is_group_chat(self):
        """Check if this is a group chat"""
        return self.conversation_type == 'group'

    @property
    def display_name(self):
        """Get display name for the conversation"""
        if self.is_group_chat and self.group_name:
            return self.group_name
        elif self.conversation_type == 'direct':
            participants = list(self.participants.all())
            if len(participants) == 2:
                return f"{participants[0].get_full_name()} & {participants[1].get_full_name()}"
        return "Conversation"
    
    def get_unread_count_for_user(self, user):
        """Get count of unread messages for a specific user"""
        return self.direct_messages.filter(
            is_read=False
        ).exclude(sender=user).count()
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get or create a direct conversation between two users"""
        # Try to find existing direct conversation with both participants
        conversation = cls.objects.filter(
            participants=user1,
            conversation_type='direct'
        ).filter(
            participants=user2
        ).first()

        if not conversation:
            # Create new direct conversation
            conversation = cls.objects.create(conversation_type='direct')
            conversation.participants.add(user1, user2)

        return conversation

    @classmethod
    def create_group_chat(cls, creator, participants, group_name):
        """Create a new group chat"""
        if len(participants) < 2:
            raise ValueError("Group chat must have at least 2 participants (excluding creator)")

        # Create group conversation
        conversation = cls.objects.create(
            conversation_type='group',
            group_name=group_name,
            created_by=creator
        )

        # Add creator and all participants
        all_participants = [creator] + list(participants)
        conversation.participants.add(*all_participants)

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
