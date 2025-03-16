from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.db.models import Q, Count, Avg
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import (
    AlumniGroup, GroupMembership, GroupEvent, GroupDiscussion,
    GroupDiscussionComment, GroupActivity, GroupFile, GroupAnalytics,
    SecurityQuestion, SecurityQuestionAnswer, GroupMessage, Post, Comment, PostLike
)
from .forms import (
    AlumniGroupForm, GroupEventForm, GroupDiscussionForm,
    GroupDiscussionCommentForm, GroupFileForm, SecurityQuestionForm
)
import json
from math import radians, sin, cos, sqrt, atan2
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import logging

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

class GroupListView(LoginRequiredMixin, ListView):
    model = AlumniGroup
    template_name = 'alumni_groups/group_list.html'
    context_object_name = 'groups'
    paginate_by = 12

    def get_queryset(self):
        queryset = AlumniGroup.objects.filter(is_active=True)
        
        # Apply filters
        filters = {}
        
        # Search filter
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        # Year range filter
        batch_start = self.request.GET.get('batch_start')
        batch_end = self.request.GET.get('batch_end')
        if batch_start and batch_end:
            queryset = queryset.filter(
                batch_start_year__gte=batch_start,
                batch_end_year__lte=batch_end
            )
        
        # Course filter
        course = self.request.GET.get('course')
        if course:
            queryset = queryset.filter(course=course)
        
        # Campus filter
        campus = self.request.GET.get('campus')
        if campus:
            queryset = queryset.filter(campus=campus)
        
        # Type filter
        group_type = self.request.GET.get('type')
        if group_type:
            queryset = queryset.filter(group_type=group_type)
        
        # Location filter
        user_lat = self.request.GET.get('latitude')
        user_lon = self.request.GET.get('longitude')
        radius = self.request.GET.get('radius')  # in kilometers
        
        if user_lat and user_lon and radius:
            # Filter groups with location data
            groups_with_location = [
                group for group in queryset
                if group.latitude and group.longitude and
                calculate_distance(
                    user_lat, user_lon,
                    group.latitude, group.longitude
                ) <= float(radius)
            ]
            queryset = queryset.filter(id__in=[g.id for g in groups_with_location])
        
        # Sort options
        sort = self.request.GET.get('sort', '-created_at')
        if sort == 'members':
            queryset = queryset.annotate(
                member_count=Count('memberships')
            ).order_by('-member_count')
        elif sort == 'activity':
            queryset = queryset.annotate(
                activity_count=Count('activities')
            ).order_by('-activity_count')
        else:
            queryset = queryset.order_by(sort)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_groups'] = AlumniGroup.objects.count()
        context['my_groups'] = AlumniGroup.objects.filter(
            memberships__user=self.request.user,
            memberships__status='APPROVED'
        )
        
        # Get recent activities - using a subquery-free approach
        recent_activities = GroupActivity.objects.select_related(
            'group', 'user'
        ).order_by('-created_at')
        context['recent_activities'] = list(recent_activities)[:10]
        
        # Get available filters
        context['courses'] = AlumniGroup.objects.values_list(
            'course', flat=True
        ).distinct()
        context['campuses'] = AlumniGroup.objects.values_list(
            'campus', flat=True
        ).distinct()
        context['years'] = AlumniGroup.objects.values_list(
            'batch_start_year', flat=True
        ).distinct().order_by('batch_start_year')
        
        # Get user memberships for the groups - using a list to avoid subquery
        user_memberships = GroupMembership.objects.filter(
            user=self.request.user,
        ).values_list('group_id', flat=True)
        context['user_memberships'] = set(user_memberships)
        
        return context

class GroupDetailView(LoginRequiredMixin, DetailView):
    model = AlumniGroup
    template_name = 'alumni_groups/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        
        # Get user's membership status
        context['membership'] = GroupMembership.objects.filter(
            group=group,
            user=self.request.user
        ).first()
        
        # Get group analytics
        context['analytics'] = group.analytics
        
        # Get recent activities
        context['activities'] = group.activities.select_related(
            'user'
        ).order_by('-created_at')[:10]
        
        # Get upcoming events
        context['upcoming_events'] = group.events.filter(
            end_date__gte=timezone.now()
        ).order_by('start_date')[:5]
        
        # Get recent discussions
        context['discussions'] = group.discussions.select_related(
            'created_by'
        ).order_by('-created_at')[:5]
        
        # Get group files
        context['files'] = group.files.select_related(
            'uploaded_by'
        ).order_by('-uploaded_at')[:5]
        
        # Get group posts
        context['group_posts'] = group.posts.all() if context['membership'] and context['membership'].status == 'APPROVED' else []
        
        # Get group messages
        context['group_messages'] = group.messages.all() if context['membership'] and context['membership'].status == 'APPROVED' else []
        
        return context

class GroupCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AlumniGroup
    form_class = AlumniGroupForm
    template_name = 'alumni_groups/group_form.html'
    success_url = reverse_lazy('alumni_groups:group_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create initial membership for creator
        GroupMembership.objects.create(
            group=self.object,
            user=self.request.user,
            role='ADMIN',
            status='APPROVED'
        )
        
        # Create analytics entry if it doesn't exist
        GroupAnalytics.objects.get_or_create(group=self.object)
        
        # Record activity
        GroupActivity.objects.create(
            group=self.object,
            user=self.request.user,
            activity_type='UPDATE',
            description=f'Group "{self.object.name}" was created'
        )
        
        messages.success(self.request, 'Group created successfully!')
        return response

class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AlumniGroup
    form_class = AlumniGroupForm
    template_name = 'alumni_groups/group_form.html'

    def test_func(self):
        group = self.get_object()
        return (self.request.user.is_staff or 
                group.memberships.filter(user=self.request.user, role='ADMIN').exists())

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Record activity
        GroupActivity.objects.create(
            group=self.object,
            user=self.request.user,
            activity_type='UPDATE',
            description=f'Group "{self.object.name}" was updated'
        )
        
        messages.success(self.request, 'Group updated successfully!')
        return response

    def get_success_url(self):
        return reverse_lazy('alumni_groups:group_detail', kwargs={'slug': self.object.slug})

@login_required
def join_group(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    
    # Check if user has an existing membership
    existing_membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    
    if existing_membership:
        if existing_membership.status == 'APPROVED':
            messages.warning(request, 'You are already a member of this group.')
            return redirect('alumni_groups:group_detail', slug=slug)
        elif existing_membership.status in ['REJECTED', 'BLOCKED']:
            # Allow rejected or blocked users to try joining again
            existing_membership.delete()
        elif existing_membership.status == 'PENDING':
            messages.warning(request, 'Your join request is already pending approval.')
            return redirect('alumni_groups:group_detail', slug=slug)
    
    # Create new membership
    status = 'PENDING' if group.requires_approval else 'APPROVED'
    GroupMembership.objects.create(
        group=group,
        user=request.user,
        status=status
    )
    
    # Record activity
    GroupActivity.objects.create(
        group=group,
        user=request.user,
        activity_type='JOIN',
        description=f'{request.user.get_full_name()} requested to join the group'
    )
    
    message = ('Your request to join has been submitted and is pending approval.'
              if status == 'PENDING' else 'You have successfully joined the group.')
    messages.success(request, message)
    
    return redirect('alumni_groups:group_detail', slug=slug)

@login_required
def get_leave_group(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    
    if membership.role == 'ADMIN' and group.memberships.filter(role='ADMIN').count() == 1:
        messages.error(request, 'You cannot leave the group as you are the only admin.')
        return redirect('alumni_groups:group_detail', slug=slug)
    
    return render(request, 'alumni_groups/leave_group_form.html', {'group': group})

@login_required
def leave_group(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    
    if request.method == 'GET':
        return redirect('alumni_groups:get_leave_group', slug=slug)
    
    if membership.role == 'ADMIN' and group.memberships.filter(role='ADMIN').count() == 1:
        messages.error(request, 'You cannot leave the group as you are the only admin.')
        return redirect('alumni_groups:group_detail', slug=slug)
    
    reason = request.POST.get('reason', '')
    
    # Record activity with reason if provided
    activity_description = f'{request.user.get_full_name()} left the group'
    if reason:
        activity_description += f' (Reason: {reason})'
    
    GroupActivity.objects.create(
        group=group,
        user=request.user,
        activity_type='LEAVE',
        description=activity_description
    )
    
    membership.delete()
    messages.success(request, 'You have successfully left the group.')
    return redirect('alumni_groups:group_list')

@login_required
def manage_members(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    
    # Check if user has permission to manage the group
    membership = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        status='APPROVED'
    ).first()
    
    # Only allow staff or group admins to manage members
    if not (request.user.is_staff or (membership and membership.role == 'ADMIN')):
        return HttpResponseForbidden("You don't have permission to manage members.")
    
    active_members = GroupMembership.objects.filter(
        group=group, 
        status='APPROVED'
    ).select_related('user', 'user__profile')
    
    pending_members = GroupMembership.objects.filter(
        group=group, 
        status='PENDING'
    ).select_related('user', 'user__profile')
    
    removed_members = GroupMembership.objects.filter(
        group=group, 
        status__in=['REJECTED', 'BLOCKED']
    ).select_related('user', 'user__profile')
    
    # Get posts by status
    pending_posts = Post.objects.filter(
        group=group,
        status='PENDING'
    ).select_related('author', 'author__profile')
    
    approved_posts = Post.objects.filter(
        group=group,
        status='APPROVED'
    ).select_related('author', 'author__profile', 'approved_by')
    
    rejected_posts = Post.objects.filter(
        group=group,
        status='REJECTED'
    ).select_related('author', 'author__profile', 'approved_by')
    
    context = {
        'group': group,
        'active_members': active_members,
        'pending_members': pending_members,
        'removed_members': removed_members,
        'pending_posts': pending_posts,
        'approved_posts': approved_posts,
        'rejected_posts': rejected_posts,
    }
    return render(request, 'alumni_groups/manage_members.html', context)

@login_required
def update_group_settings(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = get_object_or_404(
        GroupMembership,
        group=group,
        user=request.user,
        status='APPROVED',
        role='ADMIN'
    )
    
    if request.method == 'POST':
        require_post_approval = request.POST.get('require_post_approval') == 'on'
        group.require_post_approval = require_post_approval
        group.save()
        
        messages.success(request, 'Group settings updated successfully.')
        
        # Record activity
        GroupActivity.objects.create(
            group=group,
            user=request.user,
            activity_type='UPDATE',
            description=f'Group settings updated by {request.user.get_full_name()}'
        )
    
    return redirect('alumni_groups:manage_members', slug=group.slug)

@login_required
def nearby_groups_api(request):
    user_lat = request.GET.get('latitude')
    user_lon = request.GET.get('longitude')
    radius = float(request.GET.get('radius', 10))  # Default 10km radius
    
    if not all([user_lat, user_lon]):
        return JsonResponse({'error': 'Location data is required'}, status=400)
    
    # Get all groups with location data
    groups = AlumniGroup.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        is_active=True
    )
    
    # Calculate distances and filter
    nearby_groups = []
    for group in groups:
        distance = calculate_distance(
            float(user_lat), float(user_lon),
            float(group.latitude), float(group.longitude)
        )
        if distance <= radius:
            nearby_groups.append({
                'id': group.id,
                'name': group.name,
                'slug': group.slug,
                'latitude': float(group.latitude),
                'longitude': float(group.longitude),
                'distance': round(distance, 2),
                'member_count': group.memberships.count(),
            })
    
    # Sort by distance
    nearby_groups.sort(key=lambda x: x['distance'])
    
    return JsonResponse({'groups': nearby_groups})

@login_required
def group_analytics_api(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = get_object_or_404(
        GroupMembership,
        group=group,
        user=request.user,
        status='APPROVED'
    )
    
    analytics = group.analytics
    analytics.total_members = group.memberships.filter(status='APPROVED').count()
    analytics.active_members = group.memberships.filter(
        status='APPROVED',
        is_active=True
    ).count()
    analytics.total_posts = group.discussions.count()
    analytics.total_events = group.events.count()
    analytics.total_comments = sum(
        discussion.comments.count()
        for discussion in group.discussions.all()
    )
    
    if analytics.total_members > 0:
        analytics.engagement_rate = (
            (analytics.total_posts + analytics.total_comments) /
            analytics.total_members
        )
    
    analytics.save()
    
    return JsonResponse({
        'total_members': analytics.total_members,
        'active_members': analytics.active_members,
        'total_posts': analytics.total_posts,
        'total_events': analytics.total_events,
        'total_comments': analytics.total_comments,
        'engagement_rate': round(analytics.engagement_rate, 2),
    })

@login_required
def group_map_view(request):
    return render(request, 'alumni_groups/group_map.html')

@login_required
def manage_security_questions(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    
    # Check if user is admin
    if not group.memberships.filter(user=request.user, role='ADMIN').exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'toggle_security':
            group.has_security_questions = not group.has_security_questions
            group.save()
            messages.success(request, 'Security questions setting updated successfully.')
        
        elif action == 'add_question':
            form = SecurityQuestionForm(request.POST)
            if form.is_valid():
                question = form.save(commit=False)
                question.group = group
                question.save()
                messages.success(request, 'Security question added successfully.')
        
        elif action == 'delete_question':
            question_id = request.POST.get('question_id')
            SecurityQuestion.objects.filter(id=question_id, group=group).delete()
            messages.success(request, 'Security question deleted successfully.')
    
    questions = group.security_questions.all()
    form = SecurityQuestionForm()
    
    return render(request, 'alumni_groups/manage_security_questions.html', {
        'group': group,
        'questions': questions,
        'form': form
    })

@login_required
def join_group_with_questions(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    
    # Check if user is already a member
    if GroupMembership.objects.filter(group=group, user=request.user).exists():
        messages.warning(request, 'You are already a member of this group.')
        return redirect('alumni_groups:group_detail', slug=slug)
    
    if request.method == 'POST':
        # Create membership
        membership = GroupMembership.objects.create(
            group=group,
            user=request.user,
            status='PENDING'
        )
        
        # Save answers to security questions
        questions = group.security_questions.all()
        for question in questions:
            answer = request.POST.get(f'question_{question.id}')
            if answer:
                SecurityQuestionAnswer.objects.create(
                    question=question,
                    membership=membership,
                    answer=answer
                )
            elif question.is_required:
                membership.delete()
                messages.error(request, f'Please answer the required question: {question.question}')
                return redirect('alumni_groups:join_group_with_questions', slug=slug)
        
        # Record activity
        GroupActivity.objects.create(
            group=group,
            user=request.user,
            activity_type='JOIN',
            description=f'{request.user.get_full_name()} requested to join the group'
        )
        
        messages.success(request, 'Your request to join has been submitted and is pending approval.')
        return redirect('alumni_groups:group_detail', slug=slug)
    
    questions = group.security_questions.all()
    return render(request, 'alumni_groups/join_group_form.html', {
        'group': group,
        'questions': questions
    })

@login_required
def review_membership_answers(request, slug, membership_id):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = get_object_or_404(GroupMembership, id=membership_id, group=group)
    
    # Check if user is admin or moderator
    if not group.memberships.filter(user=request.user, role__in=['ADMIN', 'MODERATOR']).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action in ['approve', 'reject']:
            # Update answer statuses
            for answer in membership.security_answers.all():
                is_correct = request.POST.get(f'answer_{answer.id}') == 'correct'
                answer.is_correct = is_correct
                answer.reviewed_at = timezone.now()
                answer.reviewed_by = request.user
                answer.save()
            
            # Update membership status
            if action == 'approve':
                membership.status = 'APPROVED'
                messages.success(request, f'{membership.user.get_full_name()} has been approved to join the group.')
            else:
                membership.status = 'REJECTED'
                messages.success(request, f'{membership.user.get_full_name()}\'s request has been rejected.')
            
            membership.save()
            
            return redirect('alumni_groups:manage_members', slug=slug)
    
    answers = membership.security_answers.select_related('question').all()
    return render(request, 'alumni_groups/review_answers.html', {
        'group': group,
        'membership': membership,
        'answers': answers
    })

@login_required
def send_message(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = get_object_or_404(GroupMembership, user=request.user, group=group, status='APPROVED')
    
    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            message = GroupMessage.objects.create(
                group=group,
                user=request.user,
                content=content
            )
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_messages(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = get_object_or_404(GroupMembership, user=request.user, group=group, status='APPROVED')
    
    messages = group.messages.order_by('created_at')[:50]  # Get last 50 messages in chronological order
    html = render_to_string('alumni_groups/messages_list.html', {
        'group_messages': messages
    }, request=request)
    return HttpResponse(html) 

@login_required
@require_POST
def update_member_status(request, membership_id):
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to update member status for membership_id: {membership_id}")
    
    try:
        # Log the raw request body for debugging
        logger.debug(f"Raw request body: {request.body.decode('utf-8')}")
        data = json.loads(request.body)
        action = data.get('action')
        logger.info(f"Requested action: {action}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data',
            'details': str(e)
        }, status=400)
    
    try:
        membership = get_object_or_404(GroupMembership, id=membership_id)
        logger.info(f"Found membership for user: {membership.user.get_full_name()} in group: {membership.group.name}")
        
        # Check permissions
        user_membership = GroupMembership.objects.filter(
            group=membership.group,
            user=request.user,
            status='APPROVED'
        ).first()
        
        if not (request.user.is_staff or (user_membership and user_membership.role == 'ADMIN')):
            logger.warning(f"Permission denied for user: {request.user.get_full_name()}")
            return JsonResponse({
                'status': 'error',
                'message': 'Permission denied',
                'details': 'You must be a group admin or staff member to perform this action'
            }, status=403)
        
        # Don't allow removing the last admin
        if action == 'remove' and membership.role == 'ADMIN':
            admin_count = GroupMembership.objects.filter(
                group=membership.group,
                role='ADMIN',
                status='APPROVED'
            ).count()
            logger.info(f"Current admin count for group: {admin_count}")
            
            if admin_count <= 1:
                logger.warning("Attempted to remove last admin")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot remove the last admin of the group'
                }, status=400)
        
        # Validate the action
        valid_actions = {'approve', 'reject', 'remove', 'promote', 'reinstate'}
        if action not in valid_actions:
            logger.error(f"Invalid action attempted: {action}")
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid action. Must be one of: {", ".join(valid_actions)}'
            }, status=400)
        
        # Log the current state before changes
        logger.info(f"Current membership state - Status: {membership.status}, Role: {membership.role}")
        
        # Update membership based on action
        if action == 'approve':
            membership.status = 'APPROVED'
            membership.role = 'MEMBER'
        elif action == 'reject':
            membership.status = 'REJECTED'
        elif action == 'remove':
            membership.status = 'BLOCKED'
        elif action == 'promote':
            membership.role = 'ADMIN'
        elif action == 'reinstate':
            membership.status = 'APPROVED'
            membership.role = 'MEMBER'
        
        # Save the changes
        membership.save()
        logger.info(f"Updated membership - New Status: {membership.status}, New Role: {membership.role}")
        
        # Record activity
        activity_types = {
            'approve': 'JOIN',
            'reject': 'LEAVE',
            'remove': 'LEAVE',
            'promote': 'UPDATE',
            'reinstate': 'JOIN'
        }
        
        activity_descriptions = {
            'approve': f'{membership.user.get_full_name()} joined the group',
            'reject': f'{membership.user.get_full_name()} was rejected from the group',
            'remove': f'{membership.user.get_full_name()} was removed from the group',
            'promote': f'{membership.user.get_full_name()} was promoted to admin',
            'reinstate': f'{membership.user.get_full_name()} was reinstated to the group'
        }
        
        GroupActivity.objects.create(
            group=membership.group,
            user=membership.user,
            activity_type=activity_types[action],
            description=activity_descriptions[action]
        )
        logger.info(f"Activity recorded: {activity_descriptions[action]}")
        
        return JsonResponse({
            'status': 'success',
            'message': activity_descriptions[action],
            'new_status': membership.status,
            'new_role': membership.role
        })
        
    except GroupMembership.DoesNotExist:
        logger.error(f"Membership not found: {membership_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'Membership not found'
        }, status=404)
    except Exception as e:
        logger.exception("Unexpected error in update_member_status")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e)
        }, status=500)

@login_required
def get_security_answers(request, membership_id):
    membership = get_object_or_404(GroupMembership, id=membership_id)
    
    # Check permissions
    user_membership = GroupMembership.objects.filter(
        group=membership.group,
        user=request.user,
        status='APPROVED'
    ).first()
    
    if not (request.user.is_staff or (user_membership and user_membership.role == 'ADMIN')):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    answers = SecurityQuestionAnswer.objects.filter(
        membership=membership
    ).select_related('question')
    
    return JsonResponse({
        'answers': [
            f"Q: {answer.question.question}\nA: {answer.answer}"
            for answer in answers
        ]
    })

@login_required
def remove_member(request, group_slug, member_id):
    if request.method == 'POST':
        group = get_object_or_404(AlumniGroup, slug=group_slug)
        membership_to_remove = get_object_or_404(GroupMembership, id=member_id, group=group)
        
        # Check if user has permission to manage the group
        admin_membership = GroupMembership.objects.filter(
            group=group,
            user=request.user,
            status='APPROVED',
            role='ADMIN'
        ).first()
        
        # Only allow staff or group admins to remove members
        if not (request.user.is_staff or admin_membership):
            messages.error(request, "You don't have permission to remove members.")
            return redirect('alumni_groups:manage_members', group_slug=group_slug)
        
        # Don't allow removing the last admin
        if membership_to_remove.role == 'ADMIN':
            admin_count = GroupMembership.objects.filter(
                group=group,
                role='ADMIN',
                status='APPROVED'
            ).count()
            if admin_count <= 1:
                messages.error(request, "Cannot remove the last admin of the group.")
                return redirect('alumni_groups:manage_members', group_slug=group_slug)
        
        # Update the membership status to REMOVED
        membership_to_remove.status = 'REMOVED'
        membership_to_remove.save()
        
        # Record the activity
        GroupActivity.objects.create(
            group=group,
            user=request.user,
            activity_type='UPDATE',
            description=f'Member {membership_to_remove.user.get_full_name()} was removed from the group'
        )
        
        messages.success(request, f'{membership_to_remove.user.get_full_name()} has been removed from the group.')
        
    return redirect('alumni_groups:manage_members', group_slug=group_slug)

@login_required
def group_detail(request, slug):
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = group.memberships.filter(user=request.user).first()
    
    # Redirect users with pending membership to waiting approval page
    if membership and membership.status == 'PENDING':
        return render(request, 'alumni_groups/waiting_approval.html', {'group': group})
    
    context = {
        'group': group,
        'membership': membership,
    }
    
    if membership and membership.status == 'APPROVED':
        # Only show approved posts for regular members
        if request.user.is_staff or membership.role == 'ADMIN':
            context['group_posts'] = group.posts.select_related('author', 'author__profile').prefetch_related('likes')
        else:
            context['group_posts'] = group.posts.filter(status='APPROVED').select_related('author', 'author__profile').prefetch_related('likes')
        
        # Add is_liked annotation for each post
        if context.get('group_posts'):
            liked_posts = request.user.liked_posts.values_list('id', flat=True)
            for post in context['group_posts']:
                post.is_liked = post.id in liked_posts
    
    return render(request, 'alumni_groups/group_detail.html', context)

@login_required
def create_post(request, slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    group = get_object_or_404(AlumniGroup, slug=slug)
    membership = group.memberships.filter(user=request.user, status='APPROVED').first()
    
    if not membership:
        return JsonResponse({'error': 'You must be an approved member to post'}, status=403)
    
    content = request.POST.get('content')
    if not content:
        return JsonResponse({'error': 'Content is required'}, status=400)
    
    # Set initial status based on user role
    initial_status = 'PENDING'
    if request.user.is_staff or membership.role in ['ADMIN', 'MODERATOR']:
        initial_status = 'APPROVED'
    
    # Create post with appropriate status
    post = Post.objects.create(
        group=group,
        author=request.user,
        content=content,
        status=initial_status
    )
    
    # If auto-approved, set the approval details
    if initial_status == 'APPROVED':
        post.approved_by = request.user
        post.approved_at = timezone.now()
        post.save()
        
    return JsonResponse({'success': True, 'post_id': post.id})

@login_required
def approve_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    post = get_object_or_404(Post, id=post_id)
    membership = post.group.memberships.filter(user=request.user).first()
    
    if not (request.user.is_staff or (membership and membership.role == 'ADMIN')):
        return JsonResponse({'error': 'You do not have permission to approve posts'}, status=403)
    
    action = request.POST.get('action')
    if action not in ['approve', 'reject']:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    post.status = 'APPROVED' if action == 'approve' else 'REJECTED'
    post.approved_by = request.user
    post.approved_at = timezone.now()
    post.save()
    
    return JsonResponse({
        'success': True,
        'status': post.get_status_display(),
        'approved_by': post.approved_by.get_full_name(),
        'approved_at': post.approved_at.isoformat()
    })

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    membership = get_object_or_404(GroupMembership, group=post.group, user=request.user, status='APPROVED')
    
    if request.method == 'POST':
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
        
        return JsonResponse({
            'status': 'success',
            'likes_count': post.likes_count,
            'is_liked': created
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    membership = get_object_or_404(GroupMembership, group=post.group, user=request.user, status='APPROVED')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
            return JsonResponse({
                'status': 'success',
                'comment_id': comment.id
            })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_post_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    membership = get_object_or_404(GroupMembership, group=post.group, user=request.user, status='APPROVED')
    
    comments = post.comments.select_related('author').order_by('created_at')
    comments_html = render_to_string('alumni_groups/comments_list.html', {
        'comments': comments
    }, request=request)
    
    return HttpResponse(comments_html) 