from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, Case, When, IntegerField
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import MentorshipRequest
from .messaging_models import Conversation, Message
from .messaging_forms import MessageForm

User = get_user_model()

@login_required
def conversation_list_view(request):
    """
    View to render the conversation list sidebar for messaging
    """
    user = request.user
    
    conversations = []
    
    # Get all mentorship requests where user is either mentor or mentee
    # and status is APPROVED (active mentorships)
    mentorship_requests = MentorshipRequest.objects.filter(
        Q(mentee=user) | Q(mentor__user=user),
        status='APPROVED'
    ).select_related(
        'mentor__user__profile',
        'mentee__profile'
    ).prefetch_related('conversation__messages')
    
    for mentorship in mentorship_requests:
        # Get or create conversation for this mentorship
        conversation, created = Conversation.objects.get_or_create(
            mentorship=mentorship,
            defaults={'conversation_type': 'mentorship'}
        )
        
        # Determine the other participant
        if user == mentorship.mentee:
            other_user = mentorship.mentor.user
        else:
            other_user = mentorship.mentee
        
        # Get last message
        last_message = conversation.messages.first()
        
        # Get unread count for current user
        unread_count = conversation.get_unread_count_for_user(user)
        
        conversations.append({
            'conversation': conversation,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
            'mentorship': mentorship,
            'conversation_type': 'mentorship'
        })
    
    # Get all direct conversations where user is a participant
    direct_conversations = Conversation.objects.filter(
        Q(participant_1=user) | Q(participant_2=user),
        conversation_type='direct'
    ).select_related(
        'participant_1__profile',
        'participant_2__profile'
    ).prefetch_related('messages')
    
    for conversation in direct_conversations:
        # Determine the other participant
        other_user = conversation.get_other_participant(user)
        
        # Get last message
        last_message = conversation.messages.first()
        
        # Get unread count for current user
        unread_count = conversation.get_unread_count_for_user(user)
        
        conversations.append({
            'conversation': conversation,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
            'mentorship': None,
            'conversation_type': 'direct'
        })
    
    # Sort conversations by last message time (most recent first)
    conversations.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else x['conversation'].created_at,
        reverse=True
    )
    
    context = {
        'conversations': conversations,
        'user': user
    }
    
    # Return partial template for HTMX requests
    if request.htmx:
        return render(request, 'mentorship/messaging/partials/conversation_list.html', context)
    
    # Return full page for regular requests
    return render(request, 'mentorship/messaging/conversation_list.html', context)

@login_required
def conversation_detail_view(request, conversation_id):
    """
    View to render the conversation detail (messages) for the right panel
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    user = request.user
    
    # Check if user is participant in this conversation
    if user not in conversation.participants:
        if request.htmx:
            # Return error message as HTML for HTMX requests
            return render(request, 'mentorship/messaging/partials/error_message.html', {
                'error_message': 'Access denied to this conversation.'
            }, status=403)
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Mark messages as read for current user
    conversation.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
    
    # Get messages (already ordered by created_at desc)
    messages = conversation.messages.select_related('sender__profile').all()

    # Get the other participant
    other_user = conversation.get_other_participant(user)

    # Get upcoming scheduled meetings for this mentorship if it exists
    meetings = []
    if hasattr(conversation, 'mentorship') and conversation.mentorship:
        from .models import MentorshipMeeting
        from django.utils import timezone

        # Only show meetings that are scheduled and in the future
        meetings = MentorshipMeeting.objects.filter(
            mentorship=conversation.mentorship,
            status='SCHEDULED',
            meeting_date__gt=timezone.now()
        ).order_by('meeting_date')

    context = {
        'conversation': conversation,
        'messages': messages,
        'other_user': other_user,
        'user': user,
        'meetings': meetings
    }
    
    # Return partial template for HTMX requests
    if request.htmx:
        return render(request, 'mentorship/messaging/partials/conversation_detail.html', context)
    
    # Return full conversation view
    return render(request, 'mentorship/messaging/conversation_detail.html', context)

@login_required
def messaging_page(request):
    """
    Main messaging page entry point
    """
    # Get conversation ID from query parameter if provided
    conversation_id = request.GET.get('conversation')
    
    context = {}
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            # Verify user has access to this conversation
            if request.user in [conversation.mentorship.mentor.user, conversation.mentorship.mentee]:
                context['selected_conversation_id'] = conversation_id
        except Conversation.DoesNotExist:
            pass
    
    if request.htmx:
        # Return just the content for HTMX requests
        return render(request, 'mentorship/messaging/partials/messaging_content.html', context)
    
    return render(request, 'mentorship/messaging/messaging_page.html', context)

@login_required
@require_POST
def send_message(request, conversation_id):
    """
    Handle sending a new message via HTMX POST
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is participant in this conversation
    if request.user not in [conversation.mentorship.mentor.user, conversation.mentorship.mentee]:
        if request.htmx:
            # Return error message as HTML for HTMX requests
            return render(request, 'mentorship/messaging/partials/error_message.html', {
                'error_message': 'Unauthorized access to this conversation.'
            }, status=403)
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    form = MessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        if request.htmx:
            # Return the new message as HTML for JavaScript to append
            message_html = render(request, 'mentorship/messaging/partials/message_item.html', {
                'message': message,
                'user': request.user
            }).content.decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'message_html': message_html,
                'message_id': message.id
            })
        else:
            # Redirect to messaging page with this conversation selected
            return redirect(reverse('mentorship:messaging_page') + f'?conversation={conversation_id}')
    
    # If form is invalid, return error
    if request.htmx:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    # Redirect to messaging page with this conversation selected for non-HTMX requests
    return redirect(reverse('mentorship:messaging_page') + f'?conversation={conversation_id}')

@login_required
def create_conversation(request, mentorship_id):
    """
    Create a new conversation for a mentorship and redirect to messaging page
    """
    mentorship = get_object_or_404(MentorshipRequest, id=mentorship_id, status='APPROVED')
    
    # Check if user is participant in this mentorship
    if request.user not in [mentorship.mentor.user, mentorship.mentee]:
        if request.htmx:
            # Return error message as HTML for HTMX requests
            return render(request, 'mentorship/messaging/partials/error_message.html', {
                'error_message': 'Unauthorized access to this mentorship.'
            }, status=403)
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get or create conversation for this mentorship
    conversation, created = Conversation.objects.get_or_create(
        mentorship=mentorship
    )
    
    # Redirect to messaging page with this conversation selected
    return redirect(reverse('mentorship:messaging_page') + f'?conversation={conversation.id}')

@login_required
@require_POST
def create_direct_message(request):
    """
    Create a direct conversation between users and send the first message
    """
    recipient_id = request.POST.get('recipient_id')
    content = request.POST.get('content')
    
    if not recipient_id or not content:
        return JsonResponse({
            'success': False,
            'error': 'Recipient and message content are required.'
        }, status=400)
    
    try:
        recipient = User.objects.get(id=recipient_id)
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Recipient not found.'
        }, status=404)
    
    # Prevent users from messaging themselves
    if recipient == request.user:
        return JsonResponse({
            'success': False,
            'error': 'You cannot send a message to yourself.'
        }, status=400)
    
    # Get or create direct conversation between these users
    # Ensure consistent ordering of participants
    participant_1 = request.user if request.user.id < recipient.id else recipient
    participant_2 = recipient if request.user.id < recipient.id else request.user
    
    conversation, created = Conversation.objects.get_or_create(
        conversation_type='direct',
        participant_1=participant_1,
        participant_2=participant_2,
        defaults={
            'conversation_type': 'direct'
        }
    )
    
    # Create the message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content
    )
    
    # Update conversation timestamp
    conversation.updated_at = timezone.now()
    conversation.save()
    
    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id,
        'message_id': message.id
    })