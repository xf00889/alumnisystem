from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.utils.http import content_disposition_header
from django_ratelimit.decorators import ratelimit
import mimetypes
import json
import os
from .models import Connection, DirectConversation, DirectMessage
from core.models import Notification, NotificationPreference
from .forms import DirectMessageForm, GroupPhotoUploadForm
from alumni_directory.models import Alumni
from core.file_validators import validate_message_attachment, sanitize_filename
from core.rate_limiters import rate_limit_messages

@login_required
def test_search(request):
    """Test page for search functionality"""
    return render(request, 'connections/test_search.html')

@login_required
def test_search_api(request):
    """Test API endpoint that returns JSON for connected users search"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({
            'success': True,
            'users': [],
            'message': 'Query too short'
        })

    try:
        # Get connected users
        connected_users = Connection.get_user_connections(request.user, status='ACCEPTED')

        # Filter connected users by search query
        filtered_users = []
        for user in connected_users:
            if (query.lower() in user.first_name.lower() or
                query.lower() in user.last_name.lower() or
                query.lower() in user.get_full_name().lower() or
                query.lower() in user.username.lower()):
                filtered_users.append(user)

        # Limit to 10 results
        filtered_users = filtered_users[:10]

        users_data = [{
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'avatar_url': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else '/static/images/default-avatar.png',
            'title': user.profile.current_position if hasattr(user, 'profile') and user.profile.current_position else 'Alumni'
        } for user in filtered_users]

        return JsonResponse({
            'success': True,
            'users': users_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error searching connected users'
        })

@login_required
def test_inline_interface(request):
    """Test page for inline interface functionality"""
    return render(request, 'connections/test_inline_interface.html')


@login_required
@require_http_methods(["POST"])
def send_connection_request(request, user_id):
    """Send a connection request to another user"""
    receiver = get_object_or_404(User, id=user_id)

    # Block requests to unregistered/inactive users (e.g. imported alumni who haven't signed up)
    if not receiver.is_active:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'This alumni has not registered yet and cannot receive connection requests.'
        })

    # Check if user is trying to connect to themselves
    if receiver == request.user:
        return JsonResponse({
            'status': 'error',
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
                'status': 'error',
                'success': False,
                'message': 'Connection request already sent.'
            })
        elif existing_connection.status == 'ACCEPTED':
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': 'You are already connected with this user.'
            })
        elif existing_connection.status == 'REJECTED':
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': 'Connection request was previously rejected.'
            })
        elif existing_connection.status == 'BLOCKED':
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': 'Unable to send connection request.'
            })
    else:
        # Create new connection request
        connection = Connection.objects.create(
            requester=request.user,
            receiver=receiver,
            status='PENDING'
        )
        if not NotificationPreference.objects.filter(user=receiver, app_connections=False).exists():
            Notification.create_notification(
                recipient=receiver, sender=request.user, notification_type='connection_request',
                title='New connection request',
                message=f'{request.user.get_full_name() or request.user.username} wants to connect with you.',
                content_object=connection,
                action_url=reverse('connections:connection_requests'),
            )
        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'Connection request sent to {receiver.get_full_name() or receiver.username}.'
        })
    
    return JsonResponse({
        'status': 'error',
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
    try:
        connection = Connection.objects.get(
            id=connection_id,
            receiver=request.user,
            status='PENDING'
        )
        
        connection.accept()
        Notification.objects.filter(
            recipient=request.user, notification_type='connection_request',
            object_id=connection.pk, is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        if not NotificationPreference.objects.filter(user=connection.requester, app_connections=False).exists():
            Notification.create_notification(
                recipient=connection.requester, sender=request.user,
                notification_type='connection_accepted', title='Connection accepted',
                message=f'{request.user.get_full_name() or request.user.username} accepted your connection request.',
                content_object=connection,
                action_url=reverse('connections:my_connections'),
            )
        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': f'You are now connected with {connection.requester.get_full_name() or connection.requester.username}.',
            'user_id': connection.requester.id
        })
    except Connection.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Connection request not found or already processed.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'An error occurred while accepting the connection request.'
        }, status=400)


@login_required
@require_http_methods(["POST"])
def reject_connection_request(request, connection_id):
    """Reject a connection request"""
    try:
        connection = Connection.objects.get(
            id=connection_id,
            receiver=request.user,
            status='PENDING'
        )
        
        connection.reject()
        Notification.objects.filter(
            recipient=request.user, notification_type='connection_request',
            object_id=connection.pk, is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': 'Connection request rejected.',
            'user_id': connection.requester.id
        })
    except Connection.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Connection request not found or already processed.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'An error occurred while rejecting the connection request.'
        }, status=400)


@login_required
@require_http_methods(["POST"])
def cancel_connection_request(request, connection_id):
    """Cancel a pending connection request sent by the current user"""
    try:
        connection = Connection.objects.get(
            id=connection_id,
            requester=request.user,
            status='PENDING'
        )
        receiver_id = connection.receiver.id
        Notification.objects.filter(
            recipient=connection.receiver, notification_type='connection_request',
            object_id=connection.pk,
        ).delete()
        connection.delete()
        return JsonResponse({
            'status': 'success',
            'success': True,
            'message': 'Connection request cancelled.',
            'user_id': receiver_id
        })
    except Connection.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'Connection request not found or already processed.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'success': False,
            'message': 'An error occurred while cancelling the connection request.'
        }, status=400)


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




def mark_chat_activity_read(user, action_url):
    """Clear only this conversation's message notices when the chat is opened."""
    Notification.objects.filter(
        recipient=user, notification_type='new_message',
        action_url=action_url, is_read=False,
    ).update(is_read=True, read_at=timezone.now())

@login_required
def direct_messages(request, user_id=None):
    """View direct messages with a connected user"""
    if user_id:
        other_user = get_object_or_404(User, id=user_id)
        
        # Only connected users may start new conversations or send new messages.
        # Former connections may read existing shared history, never create new history.
        can_send = Connection.are_connected(request.user, other_user)
        if can_send:
            conversation = DirectConversation.get_or_create_conversation(request.user, other_user)
        else:
            conversation = DirectConversation.objects.filter(
                conversation_type='direct', participants=request.user
            ).filter(participants=other_user).first()
            # Blocking is stronger than disconnecting: do not expose archived history.
            is_blocked = Connection.objects.filter(
                Q(requester=request.user, receiver=other_user) |
                Q(requester=other_user, receiver=request.user),
                status='BLOCKED',
            ).exists()
            if is_blocked or not conversation or conversation.participants.count() != 2:
                if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HttpResponseForbidden('This conversation is unavailable.')
                messages.error(request, 'This conversation is unavailable.')
                return redirect('connections:conversations_list')
            if request.method == 'POST':
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status':'error','success':False,'message':'Reconnect before sending messages.'}, status=403)
                messages.error(request, 'Reconnect before sending messages.')
                return redirect('connections:conversations_list')
        
        # Get messages (ordered newest first for column-reverse display)
        messages_list = DirectMessage.objects.filter(
            conversation=conversation
        ).select_related('sender').order_by('-created_at')
        
        mark_chat_activity_read(request.user, reverse('connections:direct_messages', args=[other_user.id]))
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
                if message.attachment:
                    message.attachment_display_name = sanitize_filename(message.attachment.name)
                message.save()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': {
                            'content': message.content,
                            'sender': message.sender.get_full_name() or message.sender.username,
                            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
                            'attachment_download_url': message.attachment_access_url,
                            'attachment_is_image': message.attachment_is_image,
                            'attachment_display_name': message.attachment_label,
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
            'can_send': can_send,
        }
        
        # Check if this is an HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'connections/partials/conversation_detail.html', context)
        
        return render(request, 'connections/direct_messages.html', context)
    
    else:
        # Optional profile-to-inbox deep link. Validate the target before creating
        # an empty conversation; unrelated or blocked users cannot be opened.
        selected_conversation_user_id = None
        recipient_id = request.GET.get('with', '').strip()
        if recipient_id:
            if not recipient_id.isdecimal():
                return redirect('connections:conversations_list')
            recipient = get_object_or_404(User, pk=int(recipient_id))
            if recipient.pk == request.user.pk or not Connection.are_connected(request.user, recipient):
                return HttpResponseForbidden('A direct conversation requires an active connection.')
            DirectConversation.get_or_create_conversation(request.user, recipient)
            selected_conversation_user_id = recipient.pk

        # Show list of conversations
        conversations = DirectConversation.objects.filter(
            participants=request.user
        ).prefetch_related('participants', 'direct_messages').order_by('-updated_at')
        
        # Prepare conversation data with participant info
        conversation_data = []
        for conversation in conversations:
            last_message = conversation.last_message
            unread_count = conversation.get_unread_count_for_user(request.user)

            if conversation.is_group_chat:
                # For group chats
                conversation_data.append({
                    'conversation': conversation,
                    'other_user': None,
                    'is_group_chat': True,
                    'group_name': conversation.group_name,
                    'participant_count': conversation.participants.count(),
                    'last_message': last_message,
                    'unread_count': unread_count,
                })
            else:
                # For direct messages
                other_user = conversation.get_other_participant(request.user)
                conversation_data.append({
                    'conversation': conversation,
                    'other_user': other_user,
                    'is_group_chat': False,
                    'last_message': last_message,
                    'unread_count': unread_count,
                })
        
        context = {
            'conversations': conversation_data,
            'selected_conversation_user_id': selected_conversation_user_id,
        }
        return render(request, 'connections/conversations_list.html', context)


@login_required
@require_http_methods(["POST"])
@rate_limit_messages(max_messages=20, time_window=60)
def send_message(request, user_id):
    """Handle sending messages via HTMX"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if users are connected. Former contacts already have a read-only
    # notice in the conversation, so their rejected send need not produce a toast.
    if not Connection.are_connected(request.user, other_user):
        shared_history = DirectConversation.objects.filter(
            conversation_type='direct', participants=request.user,
        ).filter(participants=other_user).exists()
        is_blocked = Connection.objects.filter(
            Q(requester=request.user, receiver=other_user) |
            Q(requester=other_user, receiver=request.user),
            status='BLOCKED',
        ).exists()
        if shared_history and not is_blocked:
            return JsonResponse({
                'success': False,
                'code': 'conversation_read_only',
                'silent': True,
                'message': '',
            }, status=403)
        return JsonResponse({
            'success': False,
            'message': 'You can only message users you are connected with.'
        }, status=403)
    
    # Get or create conversation
    conversation = DirectConversation.get_or_create_conversation(request.user, other_user)
    
    form = DirectMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        
        # Validate attachment if present
        if message.attachment:
            try:
                validate_message_attachment(message.attachment)
                message.attachment_display_name = sanitize_filename(message.attachment.name)
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'attachment': str(e)}
                })
        
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
                'status': 'success',
                'success': True,
                'message': f'Connection with {other_user.get_full_name()} has been removed.'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'success': False,
                'message': 'No connection found to remove.'
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
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


# Group Chat API Endpoints

@login_required
@require_http_methods(["POST"])
def create_group_chat(request):
    """Create a new group chat"""
    try:
        data = json.loads(request.body)
        group_name = data.get('group_name', '').strip()
        participant_ids = data.get('participant_ids', [])

        # Validate input
        if not group_name:
            return JsonResponse({'success': False, 'error': 'Group name is required'})

        if len(participant_ids) < 2:
            return JsonResponse({'success': False, 'error': 'At least 2 participants are required'})

        # Get participant users and verify they are connected to the creator
        participants = []
        for user_id in participant_ids:
            try:
                user = User.objects.get(id=user_id)
                # Check if creator is connected to this user
                if not Connection.are_connected(request.user, user):
                    return JsonResponse({
                        'success': False,
                        'error': f'You are not connected to {user.get_full_name()}'
                    })
                participants.append(user)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'User with ID {user_id} not found'})

        # Create the group chat
        conversation = DirectConversation.create_group_chat(
            creator=request.user,
            participants=participants,
            group_name=group_name
        )

        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'group_name': conversation.group_name,
            'participant_count': conversation.participants.count()
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def group_chat_detail(request, conversation_id):
    """Get group chat detail for HTMX/AJAX requests"""
    conversation = get_object_or_404(DirectConversation, id=conversation_id)

    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)

    # Get messages
    messages_list = DirectMessage.objects.filter(
        conversation=conversation
    ).select_related('sender').order_by('created_at')

    mark_chat_activity_read(request.user, reverse('connections:conversations_list') + f'?open_group={conversation.pk}')
    # Mark messages as read for current user
    DirectMessage.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_user': None,  # Not applicable for group chats
        'is_group_chat': True,
        'participants': conversation.participants.all()
    }

    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'connections/partials/group_conversation_detail.html', context)

    return render(request, 'connections/group_chat_detail.html', context)


@login_required
@require_http_methods(["POST"])
@rate_limit_messages(max_messages=20, time_window=60)
def send_group_message(request, conversation_id):
    """Send a message to a group chat"""
    conversation = get_object_or_404(DirectConversation, id=conversation_id)

    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'success': False, 'error': 'Access denied'})

    # Check if it's actually a group chat
    if not conversation.is_group_chat:
        return JsonResponse({'success': False, 'error': 'This is not a group chat'})

    form = DirectMessageForm(request.POST, request.FILES)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        
        # Validate attachment if present
        if message.attachment:
            try:
                validate_message_attachment(message.attachment)
                message.attachment_display_name = sanitize_filename(message.attachment.name)
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'attachment': str(e)}
                })
        
        message.save()

        # Return the new message HTML for HTMX
        from django.template.loader import render_to_string
        message_html = render_to_string('connections/partials/group_message_item.html', {
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
def group_participants(request, conversation_id):
    """API endpoint to get group conversation participants"""
    try:
        conversation = get_object_or_404(DirectConversation, id=conversation_id, conversation_type='group')

        # Check if user is a participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({
                'success': False,
                'error': 'You are not a participant in this conversation'
            }, status=403)

        # Get all participants with their profile information
        participants_data = []
        for participant in conversation.participants.all().select_related('profile'):
            # Safely get profile information
            profile = getattr(participant, 'profile', None)
            alumni = getattr(participant, 'alumni', None)
            avatar_url = None
            position = None

            if profile:
                # Safely get avatar URL
                if hasattr(profile, 'avatar') and profile.avatar:
                    avatar_url = profile.avatar.url

                # Safely get position - check multiple possible attribute names
                if hasattr(profile, 'current_position') and profile.current_position:
                    position = profile.current_position
                elif hasattr(profile, 'job_title') and profile.job_title:
                    position = profile.job_title
                elif hasattr(profile, 'position') and profile.position:
                    position = profile.position
                elif hasattr(profile, 'title') and profile.title:
                    position = profile.title
                elif hasattr(profile, 'occupation') and profile.occupation:
                    position = profile.occupation

            # Also check Alumni model if it exists
            if not position and alumni:
                if hasattr(alumni, 'job_title') and alumni.job_title:
                    position = alumni.job_title
                elif hasattr(alumni, 'current_company') and alumni.current_company:
                    position = f"Employee at {alumni.current_company}"

            # Default fallback if no position found
            if not position:
                position = "Alumni"

            participant_info = {
                'id': participant.id,
                'name': participant.get_full_name(),
                'first_name': participant.first_name,
                'last_name': participant.last_name,
                'username': participant.username,
                'avatar': avatar_url,
                'position': position,
                'is_creator': participant == conversation.created_by,
            }
            participants_data.append(participant_info)

        # Sort participants: creator first, then alphabetically
        participants_data.sort(key=lambda x: (not x['is_creator'], x['name']))

        return JsonResponse({
            'success': True,
            'participants': participants_data,
            'total_count': len(participants_data),
            'current_user_is_creator': request.user == conversation.created_by,
            'current_user_id': request.user.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def remove_group_participant(request, conversation_id):
    """API endpoint to remove a participant from a group conversation"""
    try:
        conversation = get_object_or_404(DirectConversation, id=conversation_id, conversation_type='group')

        # Check if current user is the group creator
        if conversation.created_by != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Only the group creator can remove participants'
            }, status=403)

        # Get the participant to remove
        participant_id = request.POST.get('participant_id')
        if not participant_id:
            return JsonResponse({
                'success': False,
                'error': 'Participant ID is required'
            }, status=400)

        try:
            participant = User.objects.get(id=participant_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Participant not found'
            }, status=404)

        # Prevent removing the creator
        if participant == conversation.created_by:
            return JsonResponse({
                'success': False,
                'error': 'Cannot remove the group creator'
            }, status=400)

        # Check if participant is actually in the conversation
        if not conversation.participants.filter(id=participant_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'User is not a participant in this conversation'
            }, status=400)

        # Remove the participant
        conversation.participants.remove(participant)

        return JsonResponse({
            'success': True,
            'message': f'{participant.get_full_name()} has been removed from the group',
            'removed_participant_id': participant_id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def search_group_members(request, conversation_id):
    """API endpoint to search for potential group members"""
    try:
        conversation = get_object_or_404(DirectConversation, id=conversation_id, conversation_type='group')

        # Check if current user is the group creator
        if conversation.created_by != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Only the group creator can search for new members'
            }, status=403)

        # Get search query
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({
                'success': False,
                'error': 'Search query must be at least 2 characters long'
            }, status=400)

        # Get current participants to exclude them from search
        current_participant_ids = list(conversation.participants.values_list('id', flat=True))

        # Search for users by name, username, first_name, last_name
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        ).exclude(
            id__in=current_participant_ids
        ).select_related('profile').distinct()[:20]  # Limit to 20 results

        # Prepare user data
        users_data = []
        for user in users:
            # Safely get profile information
            profile = getattr(user, 'profile', None)
            alumni = getattr(user, 'alumni', None)
            avatar_url = None
            position = None
            graduation_year = None

            if profile:
                # Safely get avatar URL
                if hasattr(profile, 'avatar') and profile.avatar:
                    avatar_url = profile.avatar.url

                # Safely get position
                if hasattr(profile, 'current_position') and profile.current_position:
                    position = profile.current_position
                elif hasattr(profile, 'job_title') and profile.job_title:
                    position = profile.job_title

                # Safely get graduation year
                if hasattr(profile, 'graduation_year') and profile.graduation_year:
                    graduation_year = profile.graduation_year

            # Also check Alumni model if it exists
            if not position and alumni:
                if hasattr(alumni, 'job_title') and alumni.job_title:
                    position = alumni.job_title
                elif hasattr(alumni, 'current_company') and alumni.current_company:
                    position = f"Employee at {alumni.current_company}"

            if not graduation_year and alumni:
                if hasattr(alumni, 'graduation_year') and alumni.graduation_year:
                    graduation_year = alumni.graduation_year

            user_info = {
                'id': user.id,
                'name': user.get_full_name(),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'avatar': avatar_url,
                'position': position,
                'graduation_year': graduation_year,
            }
            users_data.append(user_info)

        return JsonResponse({
            'success': True,
            'users': users_data,
            'total_count': len(users_data),
            'query': query
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def add_group_members(request, conversation_id):
    """API endpoint to add members to a group conversation"""
    try:
        conversation = get_object_or_404(DirectConversation, id=conversation_id, conversation_type='group')

        # Check if current user is the group creator
        if conversation.created_by != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Only the group creator can add new members'
            }, status=403)

        # Get user IDs to add
        user_ids = request.POST.getlist('user_ids')
        if not user_ids:
            return JsonResponse({
                'success': False,
                'error': 'No users selected to add'
            }, status=400)

        # Validate user IDs
        try:
            user_ids = [int(uid) for uid in user_ids]
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid user IDs provided'
            }, status=400)

        # Get users to add
        users_to_add = User.objects.filter(id__in=user_ids)
        if not users_to_add.exists():
            return JsonResponse({
                'success': False,
                'error': 'No valid users found to add'
            }, status=404)

        # Check if any users are already participants
        current_participant_ids = set(conversation.participants.values_list('id', flat=True))
        already_participants = []
        new_participants = []

        for user in users_to_add:
            if user.id in current_participant_ids:
                already_participants.append(user.get_full_name())
            else:
                new_participants.append(user)

        # Add new participants
        if new_participants:
            conversation.participants.add(*new_participants)

            # Create success message
            added_names = [user.get_full_name() for user in new_participants]
            if len(added_names) == 1:
                message = f'{added_names[0]} has been added to the group'
            else:
                message = f'{len(added_names)} members have been added to the group'

            # Add warning about already existing participants if any
            if already_participants:
                if len(already_participants) == 1:
                    message += f'. Note: {already_participants[0]} was already a member.'
                else:
                    message += f'. Note: {len(already_participants)} users were already members.'

            return JsonResponse({
                'success': True,
                'message': message,
                'added_count': len(new_participants),
                'already_members_count': len(already_participants),
                'added_user_ids': [user.id for user in new_participants]
            })
        else:
            # All users were already participants
            if len(already_participants) == 1:
                message = f'{already_participants[0]} is already a member of this group'
            else:
                message = f'All selected users are already members of this group'

            return JsonResponse({
                'success': False,
                'error': message
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def upload_group_photo(request, conversation_id):
    """Handle group photo upload for group conversations"""
    print(f"=== GROUP PHOTO UPLOAD STARTED ===")
    print(f"User: {request.user.username}")
    print(f"Conversation ID: {conversation_id}")

    try:
        # Get the conversation
        conversation = get_object_or_404(DirectConversation, id=conversation_id)
        print(f"✅ Found conversation: {conversation.id} - {conversation.group_name}")

        # Basic validation
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({
                'success': False,
                'message': 'You are not a participant in this group conversation.'
            }, status=403)

        if conversation.conversation_type != 'group':
            return JsonResponse({
                'success': False,
                'message': 'This is not a group conversation.'
            }, status=400)

        if 'group_photo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No photo file was uploaded.'
            }, status=400)

        uploaded_file = request.FILES['group_photo']
        print(f"✅ File received: {uploaded_file.name} ({uploaded_file.size} bytes)")

        # Validate the form
        form = GroupPhotoUploadForm(request.POST, request.FILES, instance=conversation)
        if not form.is_valid():
            print(f"❌ Form validation failed: {form.errors}")
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            return JsonResponse({
                'success': False,
                'message': 'Photo validation failed.',
                'errors': error_messages
            }, status=400)

        print("✅ Form validation passed")

        # Simple approach: directly assign the file to the model
        print("Assigning file directly to model...")
        conversation.group_photo = uploaded_file
        conversation.save()

        # Verify it was saved
        conversation.refresh_from_db()
        print(f"After save - group_photo: {conversation.group_photo}")

        if not conversation.group_photo:
            print("❌ Direct assignment failed")
            return JsonResponse({
                'success': False,
                'message': 'Photo upload failed - file was not saved properly.'
            }, status=500)

        # Success! Return the response
        print(f"✅ Group photo uploaded successfully for conversation {conversation.id}")
        print(f"Group photo path: {conversation.group_photo.name}")
        print(f"Group photo URL: {conversation.group_photo.url}")

        response_data = {
            'success': True,
            'message': 'Group photo updated successfully!',
            'group_photo_url': conversation.group_photo.url,
            'debug_info': {
                'conversation_id': conversation.id,
                'photo_path': conversation.group_photo.name,
                'photo_exists': True
            }
        }
        print(f"✅ Returning success response")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"❌ Unexpected error in upload_group_photo: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remove_group_photo(request, conversation_id):
    """Remove group photo from group conversation"""
    conversation = get_object_or_404(DirectConversation, id=conversation_id)

    # Check if user is a participant in this group conversation
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({
            'success': False,
            'message': 'You are not a participant in this group conversation.'
        }, status=403)

    # Check if this is actually a group conversation
    if conversation.conversation_type != 'group':
        return JsonResponse({
            'success': False,
            'message': 'This is not a group conversation.'
        }, status=400)

    # Remove group photo
    if conversation.group_photo:
        try:
            conversation.group_photo.delete(save=False)
        except:
            pass  # Ignore errors if file doesn't exist

        conversation.group_photo = None
        conversation.save()

    return JsonResponse({
        'success': True,
        'message': 'Group photo removed successfully!'
    })


@login_required
def conversation_detail_redirect(request, conversation_id):
    """
    Generic conversation detail view that redirects to the main messages page.
    The connections app uses a single-page interface where all conversations
    are displayed in one view, so we redirect to the conversations list.
    """
    try:
        conversation = get_object_or_404(DirectConversation, id=conversation_id)

        # Check if user is a participant
        if request.user not in conversation.participants.all():
            messages.error(request, "You don't have access to this conversation.")
            return redirect('connections:conversations_list')

        # Always redirect to the main messages page where users can see all conversations
        # and navigate to the specific conversation from there
        return redirect('connections:conversations_list')

    except DirectConversation.DoesNotExist:
        messages.error(request, "Conversation not found.")
        return redirect('connections:conversations_list')


@login_required
@never_cache
def activity_summary(request):
    """Authenticated, recipient-scoped activity for navbar counts and live banners."""
    unread = Notification.objects.filter(recipient=request.user, is_read=False)
    recent = list(unread.exclude(notification_type='new_message').order_by('-id').values(
        'id', 'title', 'message', 'notification_type', 'action_url'
    )[:20])
    payload = {
        'success': True,
        'notifications': recent,
        'unread_notifications': unread.exclude(notification_type='new_message').count(),
        'unread_messages': unread.filter(notification_type='new_message').count(),
        'pending_requests': Connection.objects.filter(receiver=request.user, status='PENDING').count(),
    }
    return JsonResponse(payload)


@login_required
@never_cache
@ratelimit(key='user', rate='120/m', block=True)
def download_message_attachment(request, token):
    """Authorize every file access, including inline chat image previews."""
    message = get_object_or_404(
        DirectMessage.objects.select_related('conversation'),
        attachment_token=token,
    )
    if not message.attachment or not message.conversation.participants.filter(pk=request.user.pk).exists():
        raise Http404('Attachment not found')
    if message.conversation.conversation_type == 'direct':
        # Direct-conversation history is explicitly hidden when either side blocks
        # the other; attachments must enforce the same rule as the conversation view.
        member_ids = list(message.conversation.participants.values_list('pk', flat=True))
        if Connection.objects.filter(
            (Q(requester_id=request.user.pk, receiver_id__in=member_ids) |
             Q(receiver_id=request.user.pk, requester_id__in=member_ids)),
            status='BLOCKED',
        ).exists():
            raise Http404('Attachment not found')

    try:
        attachment = message.attachment.open('rb')
    except (FileNotFoundError, OSError, ValueError):
        raise Http404('Attachment not found')

    safe_name = message.attachment_label
    content_type = mimetypes.guess_type(safe_name)[0] or 'application/octet-stream'
    inline = message.attachment_is_image and content_type in {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    }
    response = FileResponse(attachment, content_type=content_type, as_attachment=not inline, filename=safe_name)
    response['Content-Disposition'] = content_disposition_header(not inline, safe_name)
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store, max-age=0'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    response['Referrer-Policy'] = 'no-referrer'
    return response
