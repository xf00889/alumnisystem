from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Connection, DirectConversation, DirectMessage
from .forms import DirectMessageForm
from alumni_directory.models import Alumni

@login_required
def test_search(request):
    """Test page for search functionality"""
    return render(request, 'connections/test_search.html')


@login_required
@require_http_methods(["POST"])
def send_connection_request(request, user_id):
    """Send a connection request to another user"""
    receiver = get_object_or_404(User, id=user_id)
    
    # Check if user is trying to connect to themselves
    if receiver == request.user:
        return JsonResponse({
            'success': False,
            'message': 'You cannot send a connection request to yourself.'
        })
    
    # Check if connection already exists
    existing_connection = Connection.objects.filter(
        Q(requester=request.user, receiver=receiver) |
        Q(requester=receiver, receiver=request.user)
    ).first()
    
    if existing_connection:
        if existing_connection.status == 'PENDING':
            return JsonResponse({
                'success': False,
                'message': 'Connection request already sent.'
            })
        elif existing_connection.status == 'ACCEPTED':
            return JsonResponse({
                'success': False,
                'message': 'You are already connected with this user.'
            })
        elif existing_connection.status == 'REJECTED':
            return JsonResponse({
                'success': False,
                'message': 'Connection request was previously rejected.'
            })
        elif existing_connection.status == 'BLOCKED':
            return JsonResponse({
                'success': False,
                'message': 'Unable to send connection request.'
            })
    else:
        # Create new connection request
        Connection.objects.create(
            requester=request.user,
            receiver=receiver,
            status='PENDING'
        )
        return JsonResponse({
            'success': True,
            'message': f'Connection request sent to {receiver.get_full_name() or receiver.username}.'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'An error occurred. Please try again.'
    })


@login_required
def connection_requests(request):
    """View pending connection requests"""
    # Incoming requests (requests sent to current user)
    incoming_requests = Connection.objects.filter(
        receiver=request.user,
        status='PENDING'
    ).select_related('requester', 'requester__profile')
    
    # Outgoing requests (requests sent by current user)
    outgoing_requests = Connection.objects.filter(
        requester=request.user,
        status='PENDING'
    ).select_related('receiver', 'receiver__profile')
    
    context = {
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
    }
    return render(request, 'connections/connection_requests.html', context)


@login_required
@require_http_methods(["POST"])
def accept_connection_request(request, connection_id):
    """Accept a connection request"""
    connection = get_object_or_404(
        Connection,
        id=connection_id,
        receiver=request.user,
        status='PENDING'
    )
    
    connection.accept()
    return JsonResponse({
        'success': True,
        'message': f'You are now connected with {connection.requester.get_full_name() or connection.requester.username}.'
    })


@login_required
@require_http_methods(["POST"])
def reject_connection_request(request, connection_id):
    """Reject a connection request"""
    connection = get_object_or_404(
        Connection,
        id=connection_id,
        receiver=request.user,
        status='PENDING'
    )
    
    connection.reject()
    return JsonResponse({
        'success': True,
        'message': 'Connection request rejected.'
    })


@login_required
def my_connections(request):
    """View all accepted connections"""
    # Get Connection objects instead of User objects
    connections = Connection.objects.filter(
        Q(requester=request.user) | Q(receiver=request.user),
        status='ACCEPTED'
    )
    
    # Paginate connections
    paginator = Paginator(connections, 12)  # Show 12 connections per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'connections': page_obj,
        'current_user': request.user,
    }
    return render(request, 'connections/my_connections.html', context)


@login_required
def direct_messages(request, user_id=None):
    """View direct messages with a connected user"""
    if user_id:
        other_user = get_object_or_404(User, id=user_id)
        
        # Check if users are connected
        if not Connection.are_connected(request.user, other_user):
            messages.error(request, "You can only message users you are connected with.")
            return redirect('connections:my_connections')
        
        # Get or create conversation
        conversation = DirectConversation.get_or_create_conversation(request.user, other_user)
        
        # Get messages
        messages_list = DirectMessage.objects.filter(
            conversation=conversation
        ).select_related('sender').order_by('created_at')
        
        # Mark messages as read (messages not sent by current user)
        DirectMessage.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        # Handle message sending
        if request.method == 'POST':
            form = DirectMessageForm(request.POST, request.FILES)
            if form.is_valid():
                message = form.save(commit=False)
                message.conversation = conversation
                message.sender = request.user
                message.save()

                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': {
                            'content': message.content,
                            'sender': message.sender.get_full_name() or message.sender.username,
                            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M')
                        }
                    })
                
                return redirect('connections:direct_messages', user_id=user_id)
        else:
            form = DirectMessageForm()
        
        context = {
            'conversation': conversation,
            'other_user': other_user,
            'messages': messages_list,
            'form': form,
        }
        
        # Check if this is an HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'connections/partials/conversation_detail.html', context)
        
        return render(request, 'connections/direct_messages.html', context)
    
    else:
        # Show list of conversations
        conversations = DirectConversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'direct_messages').order_by('-updated_at')
        
        # Prepare conversation data with other participant info
        conversation_data = []
        for conversation in conversations:
            other_user = conversation.get_other_participant(request.user)
            last_message = conversation.last_message
            unread_count = conversation.get_unread_count_for_user(request.user)
            
            conversation_data.append({
                'conversation': conversation,
                'other_user': other_user,
                'last_message': last_message,
                'unread_count': unread_count,
            })
        
        context = {
            'conversations': conversation_data,
        }
        return render(request, 'connections/conversations_list.html', context)


@login_required
@require_http_methods(["POST"])
def send_message(request, user_id):
    """Handle sending messages via HTMX"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if users are connected
    if not Connection.are_connected(request.user, other_user):
        return JsonResponse({
            'success': False,
            'message': 'You can only message users you are connected with.'
        })
    
    # Get or create conversation
    conversation = DirectConversation.get_or_create_conversation(request.user, other_user)
    
    form = DirectMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()
        
        # Return the new message HTML for HTMX
        from django.template.loader import render_to_string
        message_html = render_to_string('connections/partials/message_item.html', {
            'message': message,
            'request': request
        })
        
        return JsonResponse({
            'success': True,
            'message_html': message_html
        })
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    })


@login_required
@require_http_methods(["POST"])
def remove_connection(request, user_id):
    """Remove a connection between users"""
    try:
        other_user = get_object_or_404(User, id=user_id)
        
        # Find the connection (could be in either direction)
        connection = Connection.objects.filter(
            Q(requester=request.user, receiver=other_user) |
            Q(requester=other_user, receiver=request.user),
            status='ACCEPTED'
        ).first()
        
        if connection:
            connection.delete()
            return JsonResponse({
                'success': True,
                'message': f'Connection with {other_user.get_full_name()} has been removed.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No connection found to remove.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while removing the connection.'
        })

@login_required
def pending_requests_count(request):
    """Get the count of pending connection requests for the current user"""
    count = Connection.objects.filter(
        receiver=request.user,
        status='PENDING'
    ).count()
    
    return JsonResponse({'count': count})


@login_required
def connection_status(request, user_id):
    """Get connection status with another user (for AJAX requests)"""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        return JsonResponse({'status': 'self'})
    
    connection = Connection.objects.filter(
        Q(requester=request.user, receiver=other_user) |
        Q(requester=other_user, receiver=request.user)
    ).first()
    
    if connection:
        return JsonResponse({
            'status': connection.status,
            'is_requester': connection.requester == request.user
        })
    else:
        return JsonResponse({'status': 'none'})
