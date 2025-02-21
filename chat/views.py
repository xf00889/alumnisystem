from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count, Max, F, Exists, OuterRef
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Conversation, Message, UserBlock
from .serializers import (
    ConversationSerializer,
    MessageSerializer,
    UserSerializer,
    UserBlockSerializer
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from alumni_directory.models import Alumni
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'chat/chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get conversations
        conversations = Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'messages'
        ).annotate(
            latest_message_time=Max('messages__timestamp'),
            unread_count=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=self.request.user)
            )
        ).order_by(
            Coalesce('latest_message_time', 'created_at').desc()
        )
        
        # Add last message to each conversation
        for conversation in conversations:
            conversation.last_message = conversation.messages.filter(
                is_deleted=False
            ).order_by('-timestamp').first()
        
        # Get current conversation if specified
        conversation_id = self.kwargs.get('conversation') or self.request.GET.get('conversation')
        current_conversation = None
        chat_messages = []
        if conversation_id:
            current_conversation = get_object_or_404(
                conversations,
                id=conversation_id
            )
            chat_messages = Message.objects.filter(
                conversation=current_conversation,
                is_deleted=False
            ).select_related('sender')
            
            # Mark messages as read
            Message.objects.filter(
                conversation=current_conversation,
                is_read=False
            ).exclude(
                sender=self.request.user
            ).update(is_read=True)
        
        # Get users
        filter_type = self.request.GET.get('filter', 'all')
        query = self.request.GET.get('q', '').strip()
        
        # Get blocked users
        blocked_users = set(UserBlock.objects.filter(
            blocker=self.request.user
        ).values_list('blocked_id', flat=True))
        
        # Base queryset
        users = User.objects.exclude(
            id__in=list(blocked_users) + [self.request.user.id]
        ).select_related('alumni', 'profile')
        
        # Apply filter
        if filter_type == 'alumni':
            users = users.filter(alumni__isnull=False)
        elif filter_type == 'online':
            users = users.filter(is_active=True)
        
        # Apply search if query exists
        if query:
            users = users.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(alumni__course__icontains=query) |
                Q(alumni__college__icontains=query) |
                Q(alumni__campus__icontains=query) |
                Q(alumni__graduation_year__icontains=query)
            ).distinct()
        
        # Annotate with chat existence
        users = users.annotate(
            has_chat=Exists(
                Conversation.objects.filter(
                    is_group_chat=False,
                    participants=self.request.user
                ).filter(
                    participants=OuterRef('pk')
                )
            )
        ).order_by('first_name', 'last_name')[:50]
        
        context.update({
            'conversations': conversations,
            'current_conversation': current_conversation,
            'chat_messages': chat_messages,
            'users': users,
        })
        return context

@login_required
def new_conversation(request):
    if request.method == 'POST':
        participant_ids = request.POST.getlist('participants')
        is_group = request.POST.get('is_group') == 'true'
        name = request.POST.get('name') if is_group else None
        
        if not participant_ids:
            messages.error(request, 'Please select at least one participant')
            return redirect('chat:chat')
        
        try:
            # Create conversation
            conversation = Conversation.objects.create(
                name=name,
                is_group_chat=is_group,
                created_by=request.user
            )
            conversation.participants.add(request.user, *participant_ids)
            
            return redirect('chat:chat_with_id', conversation=conversation.id)
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            messages.error(request, 'An error occurred while creating the conversation')
            return redirect('chat:chat')
    
    # Get users for selection
    blocked_users = set(UserBlock.objects.filter(
        blocker=request.user
    ).values_list('blocked_id', flat=True))
    
    users = User.objects.exclude(
        id__in=list(blocked_users) + [request.user.id]
    ).select_related('alumni', 'profile').order_by('first_name', 'last_name')
    
    return render(request, 'chat/new_conversation.html', {
        'users': users
    })

@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    content = request.POST.get('content', '').strip()
    if content:
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
    
    return redirect('chat:chat_with_id', conversation=conversation.id)

@login_required
@require_POST
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if conversation already exists
    existing_chat = Conversation.objects.filter(
        is_group_chat=False,
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if existing_chat:
        return redirect('chat:chat_with_id', conversation=existing_chat.id)
    
    # Create new conversation
    conversation = Conversation.objects.create(
        is_group_chat=False,
        created_by=request.user
    )
    conversation.participants.add(request.user, other_user)
    
    return redirect('chat:chat_with_id', conversation=conversation.id)

@login_required
def open_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Get existing conversation or create new one
    conversation = Conversation.objects.filter(
        is_group_chat=False,
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create(
            is_group_chat=False,
            created_by=request.user
        )
        conversation.participants.add(request.user, other_user)
    
    return redirect('chat:chat_with_id', conversation=conversation.id)

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get conversations with latest message and unread count
        return Conversation.objects.filter(
            participants=self.request.user
        ).annotate(
            latest_message_time=Max('messages__timestamp'),
            unread_count=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=self.request.user)
            )
        ).order_by(
            Coalesce('latest_message_time', 'created_at').desc()
        )

    def perform_create(self, serializer):
        try:
            # Create conversation
            conversation = serializer.save(created_by=self.request.user)
            conversation.participants.add(self.request.user)
            
            # Add other participants
            participant_ids = self.request.data.get('participant_ids', [])
            if not participant_ids:
                raise ValueError("No participants specified")
            
            # For private chats, ensure only one participant
            if not conversation.is_group_chat and len(participant_ids) > 1:
                raise ValueError("Private chats can only have one participant")
            
            # Check if private chat already exists
            if not conversation.is_group_chat:
                existing_chat = Conversation.objects.filter(
                    is_group_chat=False,
                    participants=self.request.user
                ).filter(
                    participants__id=participant_ids[0]
                ).first()
                
                if existing_chat:
                    conversation.delete()
                    return existing_chat
            
            # Add participants
            conversation.participants.add(*participant_ids)
            logger.info(f"Created {'group' if conversation.is_group_chat else 'private'} chat: {conversation}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise

    @action(detail=False, methods=['get'])
    def search_users(self, request):
        query = request.query_params.get('q', '').strip()
        filter_type = request.query_params.get('filter', 'all')
        logger.info(f"Searching users with query: '{query}', filter: {filter_type}")
        
        try:
            # Get blocked users
            blocked_users = set(UserBlock.objects.filter(
                blocker=request.user
            ).values_list('blocked_id', flat=True))
            logger.info(f"Found {len(blocked_users)} blocked users")
            
            # Base queryset
            base_qs = User.objects.exclude(
                id__in=list(blocked_users) + [request.user.id]
            ).select_related('alumni', 'profile')
            logger.info(f"Initial user count: {base_qs.count()}")
            
            # Apply filter
            if filter_type == 'alumni':
                base_qs = base_qs.filter(alumni__isnull=False)
                logger.info(f"After alumni filter: {base_qs.count()} users")
            elif filter_type == 'online':
                base_qs = base_qs.filter(is_active=True)
                logger.info(f"After online filter: {base_qs.count()} users")
            
            # Apply search if query exists
            if query:
                # Search in User model
                user_results = base_qs.filter(
                    Q(username__icontains=query) |
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query)
                )
                logger.info(f"Found {user_results.count()} users by name/email")
                
                # Search in Alumni model
                alumni_results = base_qs.filter(
                    Q(alumni__course__icontains=query) |
                    Q(alumni__college__icontains=query) |
                    Q(alumni__campus__icontains=query) |
                    Q(alumni__graduation_year__icontains=query)
                )
                logger.info(f"Found {alumni_results.count()} users by alumni info")
                
                # Combine results
                results = (user_results | alumni_results).distinct()
                logger.info(f"Total unique users found: {results.count()}")
            else:
                results = base_qs
                logger.info(f"No search query, returning all users: {results.count()}")
            
            # Annotate with chat existence and order results
            results = results.annotate(
                has_chat=Exists(
                    Conversation.objects.filter(
                        is_group_chat=False,
                        participants=request.user
                    ).filter(
                        participants=OuterRef('pk')
                    )
                )
            ).order_by('first_name', 'last_name')[:50]
            
            serializer = UserSerializer(results, many=True, context={'request': request})
            logger.info(f"Returning {len(serializer.data)} serialized users")
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An error occurred while searching users'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_pk')
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        
        # Mark messages as read
        Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(
            sender=self.request.user
        ).update(is_read=True)
        
        return Message.objects.filter(
            conversation_id=conversation_id,
            is_deleted=False
        ).select_related('sender')

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_pk')
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        serializer.save(sender=self.request.user, conversation=conversation)
        logger.info(f"Message sent in conversation {conversation_id}")

    @action(detail=True, methods=['post'])
    def delete_message(self, request, pk=None, conversation_pk=None):
        message = self.get_object()
        if message.sender != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        message.soft_delete()
        logger.info(f"Message {pk} deleted by {request.user.username}")
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserBlockViewSet(viewsets.ModelViewSet):
    serializer_class = UserBlockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBlock.objects.filter(blocker=self.request.user)

    def perform_create(self, serializer):
        blocked_user_id = self.request.data.get('blocked_id')
        blocked_user = get_object_or_404(User, id=blocked_user_id)
        serializer.save(blocker=self.request.user, blocked=blocked_user)

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        block = self.get_object()
        block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@login_required
def search_users(request):
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse([])
    
    # Get blocked users
    blocked_users = set(UserBlock.objects.filter(
        blocker=request.user
    ).values_list('blocked_id', flat=True))
    
    # Base queryset
    users = User.objects.exclude(
        id__in=list(blocked_users) + [request.user.id]
    ).select_related('alumni', 'profile')
    
    # Apply search
    users = users.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query) |
        Q(alumni__course__icontains=query) |
        Q(alumni__college__icontains=query) |
        Q(alumni__campus__icontains=query) |
        Q(alumni__graduation_year__icontains=query)
    ).distinct()[:20]  # Limit to 20 results
    
    # Format results
    results = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'profile_avatar': user.profile.avatar.url if user.profile.avatar else None,
            'alumni_info': None
        }
        
        if hasattr(user, 'alumni') and user.alumni:
            alumni_info = [user.alumni.course]
            if user.alumni.college:
                alumni_info.append(user.alumni.get_college_display())
            if user.alumni.graduation_year:
                alumni_info.append(f"Batch {user.alumni.graduation_year}")
            user_data['alumni_info'] = ' • '.join(alumni_info)
        
        results.append(user_data)
    
    return JsonResponse(results, safe=False)

@login_required
@require_POST
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user owns the message
    if message.sender != request.user:
        messages.error(request, "You don't have permission to delete this message.")
        return redirect('chat:chat_with_id', conversation=message.conversation.id)
    
    conversation_id = message.conversation.id
    message.soft_delete()  # Use soft delete to maintain conversation history
    
    messages.success(request, "Message deleted successfully.")
    return redirect('chat:chat_with_id', conversation=conversation_id)

@login_required
@require_POST
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is part of the conversation
    if request.user not in conversation.participants.all():
        messages.error(request, "You don't have permission to delete this conversation.")
        return redirect('chat:chat')
    
    # Remove user from conversation participants
    conversation.participants.remove(request.user)
    
    # If no participants left, delete the conversation
    if conversation.participants.count() == 0:
        conversation.delete()
    
    messages.success(request, "Conversation deleted successfully.")
    return redirect('chat:chat')

@login_required
@require_POST
def create_group(request):
    try:
        name = request.POST.get('name', '').strip()
        member_ids = request.POST.get('member_ids', '').split(',')
        photo = request.FILES.get('photo')
        
        if not name:
            messages.error(request, 'Group name is required')
            return redirect('chat:chat')
        
        if not member_ids or member_ids[0] == '':
            messages.error(request, 'Please select at least one member')
            return redirect('chat:chat')
        
        # Create group conversation
        conversation = Conversation.objects.create(
            name=name,
            is_group_chat=True,
            created_by=request.user,
            photo=photo
        )
        
        # Add creator and members
        member_ids = [int(id) for id in member_ids if id]
        users = User.objects.filter(id__in=member_ids)
        conversation.participants.add(request.user, *users)
        
        # Create welcome message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=f'Group "{name}" created'
        )
        
        messages.success(request, 'Group created successfully')
        return redirect('chat:chat_with_id', conversation=conversation.id)
        
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        messages.error(request, 'An error occurred while creating the group')
        return redirect('chat:chat')
