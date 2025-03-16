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
from django.db.models import Prefetch
from django.utils.timezone import now
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

# Create your views here.

class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'chat/chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Handle user search first
        search_query = self.request.GET.get('search', '').strip()
        search_users = []
        
        if search_query and len(search_query) >= 2:
            # Get blocked users
            blocked_users = set(UserBlock.objects.filter(
                blocker=self.request.user
            ).values_list('blocked_id', flat=True))
            
            # Search users
            search_users = User.objects.exclude(
                id__in=list(blocked_users) + [self.request.user.id]
            ).filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(alumni__course__icontains=search_query) |
                Q(alumni__college__icontains=search_query) |
                Q(alumni__campus__icontains=search_query) |
                Q(alumni__graduation_year__icontains=search_query)
            ).select_related(
                'profile',
                'alumni'
            ).distinct()[:20]

            # Annotate users with chat status
            for user in search_users:
                # Check if there's an existing conversation
                existing_chat = Conversation.objects.filter(
                    is_group_chat=False,
                    participants=self.request.user
                ).filter(
                    participants=user
                ).first()
                
                user.has_chat = bool(existing_chat)

        # Get conversations
        conversations = Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            Prefetch('messages', 
                    queryset=Message.objects.order_by('-timestamp'),
                    to_attr='latest_messages'),
            'participants'
        ).annotate(
            latest_message_time=Max('messages__timestamp'),
            unread_count=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=self.request.user)
            )
        ).order_by(
            Coalesce('latest_message_time', 'created_at').desc()
        )

        # Process conversations
        for conversation in conversations:
            if conversation.is_group_chat:
                conversation.display_name = conversation.name
                conversation.chat_type = 'group'
            else:
                other_user = conversation.get_other_participant(self.request.user)
                if other_user and other_user in conversation.participants.all():
                    conversation.display_name = other_user.get_full_name() or other_user.username
                    conversation.chat_type = 'private'
                    conversation.other_user = other_user
                else:
                    conversation.display_name = "Unknown User"
                    conversation.chat_type = 'private'
            
            conversation.last_message = conversation.latest_messages[0] if conversation.latest_messages else None

        # Get current conversation
        current_conversation = None
        chat_messages = []
        conversation_id = self.kwargs.get('conversation') or self.request.GET.get('conversation')
        
        if conversation_id:
            try:
                current_conversation = next(
                    (conv for conv in conversations if str(conv.id) == str(conversation_id)),
                    None
                )
                
                if current_conversation:
                    chat_messages = current_conversation.messages.select_related('sender').order_by('timestamp')
                    
                    chat_messages.filter(
                        is_read=False
                    ).exclude(
                        sender=self.request.user
                    ).update(is_read=True)
            except Exception as e:
                logger.error(f"Error retrieving conversation: {str(e)}")
                messages.error(self.request, "An error occurred while loading the conversation.")
                return redirect('chat:chat')

        context.update({
            'conversations': conversations,
            'current_conversation': current_conversation,
            'chat_messages': chat_messages,
            'search_users': search_users,
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
    file = request.FILES.get('file')
    
    if content or file:
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            file=file
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'file_url': message.file.url if message.file else None,
                    'file_name': message.file.name if message.file else None,
                    'file_size': message.file.size if message.file else None,
                    'timestamp': message.timestamp.strftime('%I:%M %p'),
                }
            })
    
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
    
    # Get existing conversation
    conversation = Conversation.objects.filter(
        is_group_chat=False,
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        # Create new conversation if none exists
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
            conversation_id=conversation_id
        ).select_related('sender')

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_pk')
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        serializer.save(sender=self.request.user, conversation=conversation)
        logger.info(f"Message sent in conversation {conversation_id}")

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
        # Check if there's an existing conversation
        existing_chat = Conversation.objects.filter(
            is_group_chat=False,
            participants=request.user
        ).filter(
            participants=user
        ).first()
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'profile_avatar': user.profile.avatar.url if user.profile.avatar else None,
            'alumni_info': None,
            'has_chat': bool(existing_chat)
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

@login_required
def conversation_list(request):
    # Get all conversations for the current user
    conversations = (Conversation.objects
        .filter(participants=request.user)
        .prefetch_related(
            Prefetch('messages', 
                    queryset=Message.objects.order_by('-timestamp'),
                    to_attr='latest_messages')
        )
        .prefetch_related('participants')
        .annotate(last_message_time=Max('messages__timestamp'))
        .order_by('-last_message_time'))

    for conv in conversations:
        # Add sender info for display
        if conv.latest_messages:
            conv.display_name = conv.name if conv.is_group_chat else conv.latest_messages[0].sender.get_full_name()
            conv.last_message = conv.latest_messages[0]
        else:
            other_participant = conv.get_other_participant(request.user)
            conv.display_name = conv.name if conv.is_group_chat else (other_participant.get_full_name() if other_participant else "Unknown")
            conv.last_message = None

    return render(request, 'chat/chat.html', {
        'conversations': conversations,
    })

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation.objects.prefetch_related('participants', 'messages'), id=conversation_id)
    
    if request.user not in conversation.participants.all():
        return redirect('chat:conversation_list')
    
    # Mark messages as read
    conversation.messages.filter(sender__in=conversation.participants.exclude(id=request.user.id)).update(is_read=True)
    
    # Get display name based on conversation type
    if conversation.is_group_chat:
        display_name = conversation.name
        chat_type = 'group'
    else:
        latest_message = conversation.messages.order_by('-timestamp').first()
        if latest_message:
            display_name = latest_message.sender.get_full_name()
        else:
            other_participant = conversation.get_other_participant(request.user)
            display_name = other_participant.get_full_name() if other_participant else "Unknown"
        chat_type = 'private'
    
    context = {
        'conversation': conversation,
        'display_name': display_name,
        'chat_type': chat_type,
        'messages': conversation.messages.order_by('timestamp'),
    }
    
    return render(request, 'chat/chat.html', context)
