from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.db.models import Q, Count, Avg, Prefetch
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import (
    AlumniGroup, GroupMembership, GroupEvent, GroupDiscussion,
    GroupDiscussionComment, GroupActivity, GroupFile, GroupAnalytics,
    SecurityQuestion, SecurityQuestionAnswer, GroupMessage, Post, Comment, PostLike,
    PostBookmark, PostReport, GroupPoll, GroupPollVote, GroupEventRSVP, GroupNotification, GroupEventShareRequest
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

def get_approved_group_feed_posts(group, user, feed_sort='newest'):
    """One permission-neutral queryset preparation path for the page and AJAX refresh.

    Call only after verifying an approved group membership. Every result is an
    approved post belonging to this group; pending posts cannot enter the feed.
    """
    if feed_sort not in ('newest', 'oldest', 'popular', 'saved'):
        feed_sort = 'newest'
    posts = group.posts.filter(status='APPROVED').select_related(
        'author', 'author__profile'
    ).prefetch_related('likes', 'comments__author', 'event_shares__event')
    if feed_sort == 'saved':
        posts = posts.filter(bookmarks__user=user).order_by('-is_pinned', '-created_at', '-pk')
    elif feed_sort == 'oldest':
        posts = posts.order_by('-is_pinned', 'created_at', 'pk')
    elif feed_sort == 'popular':
        posts = posts.annotate(popularity=Count('likes', distinct=True)).order_by('-is_pinned', '-popularity', '-created_at', '-pk')
    else:
        posts = posts.order_by('-is_pinned', '-created_at', '-pk')
    items = list(posts[:100])
    liked_ids = set(user.liked_posts.filter(group=group).values_list('pk', flat=True))
    bookmarked_ids = set(PostBookmark.objects.filter(user=user, post__group=group).values_list('post_id', flat=True))
    for post in items:
        post.is_liked = post.pk in liked_ids
        post.is_bookmarked = post.pk in bookmarked_ids
        post.top_comments = [comment for comment in post.comments.all() if comment.parent_id is None]
    return items


@login_required
def group_feed_snapshot(request, slug):
    """Safe, read-only HTML fragment of the latest visible posts for a group member."""
    group = get_object_or_404(AlumniGroup, slug=slug)
    if not GroupMembership.objects.filter(
        group=group, user=request.user, status='APPROVED', is_active=True
    ).exists():
        return HttpResponseForbidden('Approved group membership is required.')
    feed_sort = request.GET.get('feed_sort', 'newest')
    posts = get_approved_group_feed_posts(group, request.user, feed_sort)
    html = render_to_string('alumni_groups/feed_post_cards.html', {
        'group_posts': posts,
        'user': request.user,
        'can_moderate_posts': GroupMembership.objects.filter(
            group=group, user=request.user, status='APPROVED', is_active=True
        ).filter(Q(role='ADMIN') | Q(user__is_staff=True)).exists(),
    }, request=request)
    response = JsonResponse({'html': html, 'post_ids': [post.pk for post in posts]})
    response['Cache-Control'] = 'no-store, private'
    return response


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
        context['discussions'] = group.discussions.select_related('created_by').prefetch_related(
            Prefetch('comments', queryset=GroupDiscussionComment.objects.select_related('created_by').order_by('created_at'))
        ).order_by('-is_pinned', '-created_at')[:25]
        
        # Get group files
        context['files'] = group.files.select_related(
            'uploaded_by'
        ).order_by('-uploaded_at')[:5]
        
        # Feed access is tied to an approved membership, never merely a staff role.
        membership = context['membership']
        is_member = bool(membership and membership.status == 'APPROVED')
        can_moderate = is_member and (self.request.user.is_staff or membership.role == 'ADMIN')
        context['can_moderate_posts'] = can_moderate
        context['can_review_event_shares'] = is_member and membership.is_active and membership.role == 'ADMIN'
        context['approved_member_count'] = group.memberships.filter(status='APPROVED').count()
        context['feed_sort'] = self.request.GET.get('feed_sort', 'newest')
        if context['feed_sort'] not in ('newest', 'oldest', 'popular', 'saved'):
            context['feed_sort'] = 'newest'
        context['group_posts'] = []
        context['pending_posts'] = []
        context['my_pending_posts'] = []
        context['group_polls'] = []
        context['community_notifications'] = []
        context['pending_event_shares'] = []
        context['group_events'] = []
        context['is_community_member'] = is_member
        if is_member:
            posts = group.posts.select_related('author', 'author__profile')
            context['group_posts'] = get_approved_group_feed_posts(group, self.request.user, context['feed_sort'])
            if can_moderate:
                context['pending_posts'] = list(posts.filter(status='PENDING').order_by('created_at')[:100])
            else:
                context['my_pending_posts'] = list(posts.filter(status='PENDING', author=self.request.user).order_by('-created_at')[:20])
        # Only active GroupEvent records appear on the Events tab.
        if is_member:
            context['group_events'] = list(group.events.filter(is_active=True).order_by('start_date')[:25])
            event_responses = dict(GroupEventRSVP.objects.filter(event__group=group, user=self.request.user).values_list('event_id', 'response'))
            for event in context['group_events']:
                event.my_rsvp = event_responses.get(event.id)
                event.going_count = event.rsvps.filter(response='GOING').count()
            context['group_polls'] = list(group.polls.select_related('author').prefetch_related('options__votes').order_by('-created_at')[:20])
            vote_options = dict(GroupPollVote.objects.filter(poll__group=group, voter=self.request.user).values_list('poll_id', 'option_id'))
            for poll in context['group_polls']:
                poll.my_option_id = vote_options.get(poll.id)
                poll.is_closed = bool(poll.closes_at and poll.closes_at <= timezone.now())
                poll.total_votes = len(poll.votes.all())
            context['community_notifications'] = list(GroupNotification.objects.filter(group=group, recipient=self.request.user).order_by('-created_at')[:20])
            context['unread_group_notifications'] = sum(not notice.is_read for notice in context['community_notifications'])
            if context['can_review_event_shares']:
                context['pending_event_shares'] = list(
                    GroupEventShareRequest.objects.filter(
                        group=group, status='PENDING', event__status='published', event__end_date__gte=timezone.now(),
                        event__notified_groups=group,
                    ).select_related('event', 'event__created_by').order_by('-created_at')[:50]
                )
        else:
            context['unread_group_notifications'] = 0
        context['group_event_form'] = GroupEventForm() if can_moderate else None
        context['group_messages'] = group.messages.all() if is_member else []
        
        return context

class GroupCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AlumniGroup
    form_class = AlumniGroupForm
    template_name = 'alumni_groups/group_form.html'
    success_url = reverse_lazy('alumni_groups:group_list')

    def test_func(self):
        # Allow all authenticated users to create groups
        return True

    def form_valid(self, form):
        print("DEBUG: form_valid method called!")
        # Check for duplicate groups based on the specified criteria
        batch_start_year = form.cleaned_data.get('batch_start_year')
        batch_end_year = form.cleaned_data.get('batch_end_year')
        course = form.cleaned_data.get('course')
        campus = form.cleaned_data.get('campus')
        
        # Debug logging
        print(f"DEBUG: Checking for duplicates with criteria:")
        print(f"  batch_start_year: {batch_start_year}")
        print(f"  batch_end_year: {batch_end_year}")
        print(f"  course: {course}")
        print(f"  campus: {campus}")
        
        # Debug: Show all existing groups with similar criteria
        all_groups = AlumniGroup.objects.all()
        print(f"DEBUG: All existing groups:")
        for group in all_groups:
            print(f"  - {group.name}: batch={group.batch_start_year}-{group.batch_end_year}, course={group.course}, campus={group.campus}")
        
        # Check if a group with the same criteria already exists
        existing_group = AlumniGroup.objects.filter(
            batch_start_year=batch_start_year,
            batch_end_year=batch_end_year,
            course=course,
            campus=campus
        ).first()
        
        print(f"DEBUG: Found existing group: {existing_group}")
        
        if existing_group:
            # Group with same criteria already exists
            print(f"DEBUG: Duplicate found! Blocking creation.")
            messages.error(
                self.request, 
                f'A group with the same batch years ({batch_start_year}-{batch_end_year}), '
                f'course ({course}), and campus ({existing_group.get_campus_display()}) already exists. '
                f'Please check the existing group: "{existing_group.name}"'
            )
            return self.form_invalid(form)
        
        # No duplicate found, proceed with normal group creation
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
    
    def form_invalid(self, form):
        print("DEBUG: form_invalid method called!")
        print(f"DEBUG: Form errors: {form.errors}")
        return super().form_invalid(form)

class GroupCreateProgressiveView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Main progressive group creation view"""
    template_name = 'alumni_groups/group_create_progressive.html'

    def test_func(self):
        # Allow all authenticated users to create groups
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_step'] = self.request.GET.get('step', '1')
        return context

class GroupCreatePhase1View(LoginRequiredMixin, View):
    """Phase 1: Collect batch years, college, course, and campus"""
    
    def get(self, request):
        return render(request, 'alumni_groups/group_create_phase1.html')
    
    def post(self, request):
        batch_start_year = request.POST.get('batch_start_year')
        batch_end_year = request.POST.get('batch_end_year')
        course = request.POST.get('course')
        campus = request.POST.get('campus')
        
        # Validate required fields
        if not all([batch_start_year, batch_end_year, course, campus]):
            messages.error(request, 'All fields are required.')
            return render(request, 'alumni_groups/group_create_phase1.html')
        
        # Check for duplicate groups
        existing_group = AlumniGroup.objects.filter(
            batch_start_year=int(batch_start_year),
            batch_end_year=int(batch_end_year),
            course=course,
            campus=campus
        ).first()
        
        if existing_group:
            # Duplicate found - show error and suggest existing group
            messages.error(
                request,
                f'A group with the same batch years ({batch_start_year}-{batch_end_year}), '
                f'course ({course}), and campus ({existing_group.get_campus_display()}) already exists. '
                f'Please check the existing group: "{existing_group.name}"'
            )
            return render(request, 'alumni_groups/group_create_phase1.html')
        
        # No duplicate found - store data in session and proceed to phase 2
        request.session['group_creation_data'] = {
            'batch_start_year': int(batch_start_year),
            'batch_end_year': int(batch_end_year),
            'course': course,
            'campus': campus
        }
        
        return redirect('alumni_groups:group_create_phase2')

class GroupCreatePhase2View(LoginRequiredMixin, View):
    """Phase 2: Group details, type, visibility, and finalization"""
    
    def get(self, request):
        # Check if phase 1 data exists
        if 'group_creation_data' not in request.session:
            messages.error(request, 'Please start from the beginning.')
            return redirect('alumni_groups:group_create_phase1')
        
        context = {
            'phase1_data': request.session['group_creation_data']
        }
        return render(request, 'alumni_groups/group_create_phase2.html', context)
    
    def post(self, request):
        # Check if phase 1 data exists
        if 'group_creation_data' not in request.session:
            messages.error(request, 'Please start from the beginning.')
            return redirect('alumni_groups:group_create_phase1')
        
        phase1_data = request.session['group_creation_data']
        
        # Get phase 2 data
        group_name = request.POST.get('group_name')
        group_type = request.POST.get('group_type')
        description = request.POST.get('description')
        visibility = request.POST.get('visibility')
        tags = request.POST.get('tags', '')
        cover_image = request.FILES.get('cover_image')
        profile_photo = request.FILES.get('profile_photo')
        requires_approval = request.POST.get('requires_approval') == 'on'
        has_security_questions = request.POST.get('has_security_questions') == 'on'
        max_members = request.POST.get('max_members')
        
        # Validate required fields
        if not all([group_name, group_type, description, visibility]):
            messages.error(request, 'All required fields must be filled.')
            return self.get(request)
        
        # Create the group
        try:
            # Create group first
            group = AlumniGroup.objects.create(
                name=group_name,
                description=description,
                group_type=group_type,
                visibility=visibility,
                batch_start_year=phase1_data['batch_start_year'],
                batch_end_year=phase1_data['batch_end_year'],
                course=phase1_data['course'],
                campus=phase1_data['campus'],
                created_by=request.user,
                requires_approval=requires_approval,
                has_security_questions=has_security_questions,
                max_members=int(max_members) if max_members else None,
            )
            
            # Update image fields if files were uploaded
            if cover_image:
                group.cover_image = cover_image
            if profile_photo:
                group.profile_photo = profile_photo
            
            # Save again to persist file uploads
            if cover_image or profile_photo:
                group.save()
            
            # Add tags if provided
            if tags:
                group.tags.set(*[tag.strip() for tag in tags.split(',') if tag.strip()])
            
            # Create initial membership for creator
            GroupMembership.objects.create(
                group=group,
                user=request.user,
                role='ADMIN',
                status='APPROVED'
            )
            
            # Create analytics entry
            GroupAnalytics.objects.get_or_create(group=group)
            
            # Record activity
            GroupActivity.objects.create(
                group=group,
                user=request.user,
                activity_type='UPDATE',
                description=f'Group "{group.name}" was created'
            )
            
            # Clear session data
            del request.session['group_creation_data']
            
            messages.success(request, f'Group "{group.name}" created successfully!')
            return redirect('alumni_groups:group_detail', slug=group.slug)
            
        except Exception as e:
            messages.error(request, f'Error creating group: {str(e)}')
            return self.get(request)

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
    
    member_query = (request.GET.get('member_search') or '').strip()[:100]
    if member_query:
        member_filter = Q(user__first_name__icontains=member_query) | Q(user__last_name__icontains=member_query) | Q(user__username__icontains=member_query) | Q(user__email__icontains=member_query)
        active_members = active_members.filter(member_filter)
        pending_members = pending_members.filter(member_filter)
        removed_members = removed_members.filter(member_filter)

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
        'member_search': member_query,
        'open_reports': PostReport.objects.filter(post__group=group, status='OPEN').select_related('post', 'post__author', 'reporter').order_by('-created_at')[:100],
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
    # Use the same active-group visibility as the existing Groups directory.
    # The group model has no geographical coordinates, so this view supplies
    # discoverable groups without inventing or exposing member locations.
    groups = list(AlumniGroup.objects.filter(is_active=True))
    memberships = GroupMembership.objects.filter(
        user=request.user, group_id__in=[group.id for group in groups]
    ).values_list('group_id', flat=True)
    return render(request, 'alumni_groups/group_map.html', {
        'groups': groups,
        'user_memberships': set(memberships),
        'group_types': AlumniGroup.GROUP_TYPES,
        'courses': sorted({group.course for group in groups if group.course}),
        'current_year': timezone.now().year,
    })

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
    from django.db import transaction
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    action = data.get('action')
    valid = {'approve', 'reject', 'remove', 'promote', 'demote', 'make_moderator', 'reinstate'}
    if action not in valid:
        return JsonResponse({'status': 'error', 'message': 'Invalid member action.'}, status=400)
    with transaction.atomic():
        membership = get_object_or_404(GroupMembership.objects.select_for_update().select_related('group', 'user'), pk=membership_id)
        actor = GroupMembership.objects.filter(group=membership.group, user=request.user, status='APPROVED', is_active=True).first()
        if not (request.user.is_staff or (actor and actor.role == 'ADMIN')):
            return JsonResponse({'status': 'error', 'message': 'Group administrator required.'}, status=403)
        if membership.user_id == request.user.pk and action in ('remove', 'demote', 'reject', 'make_moderator'):
            return JsonResponse({'status': 'error', 'message': 'You cannot remove or demote your own role.'}, status=400)
        if action in ('promote', 'demote', 'make_moderator') and membership.status != 'APPROVED':
            return JsonResponse({'status': 'error', 'message': 'Only approved members can receive role changes.'}, status=400)
        if action in ('approve', 'reject') and membership.status != 'PENDING':
            return JsonResponse({'status': 'error', 'message': 'Only pending requests can be reviewed.'}, status=400)
        if action == 'reinstate' and membership.status not in ('BLOCKED', 'REJECTED'):
            return JsonResponse({'status': 'error', 'message': 'Member is not removed.'}, status=400)
        if membership.role == 'ADMIN' and membership.status == 'APPROVED' and action in ('remove', 'demote', 'make_moderator'):
            if GroupMembership.objects.filter(group=membership.group, role='ADMIN', status='APPROVED').count() <= 1:
                return JsonResponse({'status': 'error', 'message': 'The group must retain an administrator.'}, status=400)
        if action == 'approve':
            membership.status, membership.role = 'APPROVED', 'MEMBER'
        elif action == 'reject':
            membership.status = 'REJECTED'
        elif action == 'remove':
            membership.status, membership.is_active = 'BLOCKED', False
        elif action == 'reinstate':
            membership.status, membership.is_active, membership.role = 'APPROVED', True, 'MEMBER'
        elif action == 'promote':
            membership.role = 'ADMIN'
        elif action == 'make_moderator':
            membership.role = 'MODERATOR'
        elif action == 'demote':
            membership.role = 'MEMBER'
        membership.save(update_fields=['status', 'role', 'is_active', 'last_active_at'])
        GroupActivity.objects.create(group=membership.group, user=request.user, activity_type='UPDATE', description=f'Group membership {action}: {membership.user.username}')
    return JsonResponse({'status': 'success', 'message': 'Member updated.', 'new_status': membership.status, 'new_role': membership.role})

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
    
    content = (request.POST.get('content') or '').strip()
    photo = request.FILES.get('image')
    if not content and not photo:
        return JsonResponse({'error': 'Write an update or attach a photo.'}, status=400)
    if len(content) > 5000:
        return JsonResponse({'error': 'Posts must be 5,000 characters or fewer.'}, status=400)

    if photo:
        # ImageField validates image bytes, not only the browser-provided MIME type.
        from django import forms
        from django.core.exceptions import ValidationError
        if photo.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'Photo must be 5 MB or smaller.'}, status=400)
        try:
            photo = forms.ImageField().clean(photo)
        except ValidationError:
            return JsonResponse({'error': 'Please upload a valid image file.'}, status=400)
        if photo.image.format not in ('JPEG', 'PNG', 'WEBP'):
            return JsonResponse({'error': 'Only JPEG, PNG, or WebP photos are supported.'}, status=400)

    # The group's setting controls whether ordinary members need approval.
    can_publish = request.user.is_staff or membership.role in ('ADMIN', 'MODERATOR')
    initial_status = 'APPROVED' if can_publish or not group.require_post_approval else 'PENDING'
    post = Post.objects.create(
        group=group, author=request.user, content=content,
        image=photo, status=initial_status,
    )
    
    # If auto-approved, set the approval details
    if initial_status == 'APPROVED':
        post.approved_by = request.user
        post.approved_at = timezone.now()
        post.save()
        
    if post.status == 'APPROVED':
        from .community_views import notify_mentions
        notify_mentions(group, request.user, content, post=post)
    return JsonResponse({'success': True, 'post_id': post.id, 'status': post.status,
                         'message': 'Post published.' if post.status == 'APPROVED' else 'Post sent for approval.'})

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
    if action == 'approve':
        from .community_views import notify_mentions
        notify_mentions(post.group, post.author, post.content, post=post)
    GroupNotification.objects.create(group=post.group, recipient=post.author, actor=request.user, post=post,
                                     message=f'Your group post was {post.status.lower()}.')
    return JsonResponse({
        'success': True,
        'status': post.get_status_display(),
        'approved_by': post.approved_by.get_full_name(),
        'approved_at': post.approved_at.isoformat()
    })

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='APPROVED')
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
    post = get_object_or_404(Post, id=post_id, status='APPROVED')
    membership = get_object_or_404(GroupMembership, group=post.group, user=request.user, status='APPROVED')
    
    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        if not content or len(content) > 3000:
            return JsonResponse({'status': 'error', 'message': 'Comment must contain 1–3000 characters.'}, status=400)
        parent = None
        if request.POST.get('parent_id'):
            parent = get_object_or_404(Comment, pk=request.POST['parent_id'], post=post)
            if parent.parent_id:
                parent = parent.parent
        comment = Comment.objects.create(post=post, author=request.user, content=content, parent=parent)
        from .community_views import notify_mentions
        notify_mentions(post.group, request.user, content, post=post)
        recipient = parent.author if parent else post.author
        if recipient_id := (recipient.pk if recipient.pk != request.user.pk else None):
            GroupNotification.objects.create(group=post.group, recipient_id=recipient_id, actor=request.user, post=post,
                                             message=f'{request.user.get_full_name() or request.user.username} replied to your group post.')
        return JsonResponse({'status': 'success', 'comment_id': comment.pk})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def get_post_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='APPROVED')
    membership = get_object_or_404(GroupMembership, group=post.group, user=request.user, status='APPROVED')
    
    comments = post.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author').order_by('created_at')
    comments_html = render_to_string('alumni_groups/comments_list.html', {
        'comments': comments
    }, request=request)
    
    return HttpResponse(comments_html) 