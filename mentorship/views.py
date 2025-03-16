from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Case, When, IntegerField
from django.utils import timezone
from accounts.models import Mentor, MentorshipRequest
from .models import MentorshipMeeting, MentorshipMessage, MentorshipProgress, TimelineMilestone
from .serializers import (
    MentorSerializer, MentorshipRequestSerializer, MentorshipMeetingSerializer,
    MentorshipMessageSerializer, MentorshipProgressSerializer, TimelineMilestoneSerializer
)
from rest_framework import serializers
from django.http import JsonResponse

@login_required
def mentor_search(request):
    """
    View for searching and filtering mentors
    """
    return render(request, 'mentorship/mentor_search.html')

@login_required
def mentee_dashboard(request):
    """
    View for mentee's dashboard showing their mentorship requests and active mentorships
    """
    # Get mentorship requests grouped by status
    pending_requests = MentorshipRequest.objects.filter(
        mentee=request.user,
        status='PENDING'
    ).select_related('mentor', 'mentor__user', 'mentor__user__profile').order_by('-created_at')
    
    active_mentorships = MentorshipRequest.objects.filter(
        mentee=request.user,
        status='APPROVED'
    ).select_related('mentor', 'mentor__user', 'mentor__user__profile').order_by('-start_date', '-created_at')
    
    completed_mentorships = MentorshipRequest.objects.filter(
        mentee=request.user,
        status='COMPLETED'
    ).select_related('mentor', 'mentor__user', 'mentor__user__profile').order_by('-end_date', '-created_at')
    
    rejected_requests = MentorshipRequest.objects.filter(
        mentee=request.user,
        status='REJECTED'
    ).select_related('mentor', 'mentor__user', 'mentor__user__profile').order_by('-updated_at')
    
    # Get upcoming meetings
    upcoming_meetings = MentorshipMeeting.objects.filter(
        mentorship__mentee=request.user,
        mentorship__status='APPROVED',
        status='SCHEDULED',
        meeting_date__gt=timezone.now()
    ).select_related('mentorship', 'mentorship__mentor', 'mentorship__mentor__user').order_by('meeting_date')[:5]
    
    # Get recent messages
    recent_messages = MentorshipMessage.objects.filter(
        mentorship__mentee=request.user,
        mentorship__status='APPROVED'
    ).select_related('sender', 'mentorship').order_by('-created_at')[:5]
    
    # Get progress updates
    progress_updates = MentorshipProgress.objects.filter(
        mentorship__mentee=request.user
    ).select_related('mentorship', 'created_by').order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'pending_requests': pending_requests,
        'active_mentorships': active_mentorships,
        'completed_mentorships': completed_mentorships,
        'rejected_requests': rejected_requests,
        'upcoming_meetings': upcoming_meetings,
        'recent_messages': recent_messages,
        'progress_updates': progress_updates,
        'total_active_mentorships': active_mentorships.count(),
        'total_pending_requests': pending_requests.count(),
        'total_completed_mentorships': completed_mentorships.count()
    }
    
    return render(request, 'mentorship/mentee_dashboard.html', context)

@login_required
def request_mentorship(request, mentor_id):
    """
    View for requesting mentorship from a specific mentor.
    """
    mentor = get_object_or_404(Mentor, user_id=mentor_id)
    
    # Check if mentor is accepting mentees
    if not mentor.accepting_mentees or not mentor.is_active:
        messages.error(request, "This mentor is not currently accepting new mentees.")
        return redirect('alumni_directory:alumni_detail', pk=mentor_id)
    
    # Check if a request already exists
    existing_request = MentorshipRequest.objects.filter(
        mentor=mentor,
        mentee=request.user,
        status__in=['PENDING', 'APPROVED']
    ).first()
    
    if existing_request:
        if existing_request.status == 'PENDING':
            messages.info(request, "You already have a pending request with this mentor.")
        else:
            messages.info(request, "You are already in a mentorship relationship with this mentor.")
        return redirect('alumni_directory:alumni_detail', pk=mentor_id)
    
    if request.method == 'POST':
        # Process the form submission
        skills_seeking = request.POST.get('skills_seeking', '')
        goals = request.POST.get('goals', '')
        message = request.POST.get('message', '')
        
        if not skills_seeking or not goals or not message:
            messages.error(request, "Please fill out all required fields.")
        else:
            # Create the mentorship request
            mentorship_request = MentorshipRequest.objects.create(
                mentor=mentor,
                mentee=request.user,
                skills_seeking=skills_seeking,
                goals=goals,
                message=message,
                status='PENDING'
            )
            
            messages.success(request, "Your mentorship request has been submitted successfully and is awaiting approval from the mentor. You will be notified when they respond.")
            return redirect('mentorship:mentor_search')
    
    context = {
        'mentor': mentor,
    }
    return render(request, 'mentorship/request_mentorship.html', context)

@login_required
def mentor_dashboard(request):
    """
    View for mentor's dashboard showing their mentorship requests and current mentees
    """
    if not hasattr(request.user, 'mentor_profile'):
        messages.error(request, "You need to be a verified mentor to access this page.")
        return redirect('accounts:apply_mentor')
    
    mentor = request.user.mentor_profile
    
    # Get mentorship requests grouped by status
    pending_requests = MentorshipRequest.objects.filter(
        mentor=mentor,
        status='PENDING'
    ).select_related('mentee', 'mentee__profile').order_by('-created_at')
    
    active_mentorships = MentorshipRequest.objects.filter(
        mentor=mentor,
        status='APPROVED'
    ).select_related('mentee', 'mentee__profile').order_by('-start_date', '-created_at')
    
    completed_mentorships = MentorshipRequest.objects.filter(
        mentor=mentor,
        status='COMPLETED'
    ).select_related('mentee', 'mentee__profile').order_by('-end_date', '-created_at')
    
    # Get upcoming meetings
    upcoming_meetings = MentorshipMeeting.objects.filter(
        mentorship__mentor=mentor,
        mentorship__status='APPROVED',
        status='SCHEDULED',
        meeting_date__gt=timezone.now()
    ).select_related('mentorship', 'mentorship__mentee').order_by('meeting_date')[:5]
    
    context = {
        'mentor': mentor,
        'pending_requests': pending_requests,
        'active_mentorships': active_mentorships,
        'completed_mentorships': completed_mentorships,
        'upcoming_meetings': upcoming_meetings,
    }
    
    return render(request, 'mentorship/mentor_dashboard.html', context)

# Create your views here.

class IsMentorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(request.user, 'mentor_profile') and request.user.mentor_profile.is_active

class IsMentorshipParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Handle different object types
        if hasattr(obj, 'mentorship'):
            # For objects like MentorshipMeeting, MentorshipMessage, etc.
            mentorship = obj.mentorship
            if hasattr(user, 'mentor_profile'):
                return mentorship.mentor == user.mentor_profile
            return mentorship.mentee == user
        else:
            # For direct mentorship objects
            if hasattr(user, 'mentor_profile'):
                return obj.mentor == user.mentor_profile
            return obj.mentee == user

class MentorOnlyForDelete(permissions.BasePermission):
    """
    Permission class that allows only mentors to delete meetings.
    Mentees can view, create, and update meetings but not delete them.
    """
    def has_permission(self, request, view):
        # Allow all authenticated users for non-destructive methods
        if request.method != 'DELETE':
            return True
        
        # For DELETE, only allow mentors
        return hasattr(request.user, 'mentor_profile')
    
    def has_object_permission(self, request, view, obj):
        # For non-DELETE methods, allow both mentors and mentees
        if request.method != 'DELETE':
            return True
        
        # For DELETE, only allow the mentor of this meeting
        user = request.user
        if hasattr(user, 'mentor_profile'):
            return obj.mentorship.mentor == user.mentor_profile
        
        # Mentees cannot delete meetings
        return False

class MentorViewSet(viewsets.ModelViewSet):
    queryset = Mentor.objects.filter(is_active=True)
    serializer_class = MentorSerializer
    permission_classes = [permissions.IsAuthenticated, IsMentorOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['expertise_areas', 'user__first_name', 'user__last_name']

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset().filter(accepting_mentees=True)
            queryset = self.filter_queryset(queryset)
            serializer = self.get_serializer(queryset, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_queryset(self):
        queryset = super().get_queryset()
        
        try:
            # Filter by expertise
            expertise = self.request.query_params.get('expertise', None)
            if expertise:
                expertise_terms = [term.strip() for term in expertise.split(',')]
                q_objects = Q()
                for term in expertise_terms:
                    q_objects |= Q(expertise_areas__icontains=term)
                queryset = queryset.filter(q_objects)
            
            # Filter by availability
            availability = self.request.query_params.get('availability', None)
            if availability:
                queryset = queryset.filter(availability_status=availability)
            
            # Filter by experience
            experienced = self.request.query_params.get('experienced', None)
            if experienced and experienced.lower() == 'true':
                # Filter mentors with substantial mentoring experience
                queryset = queryset.exclude(
                    Q(mentoring_experience__isnull=True) | 
                    Q(mentoring_experience__exact='')
                )
            
            # Sort results
            sort = self.request.query_params.get('sort', 'experience')
            if sort == 'experience':
                # Sort by mentoring experience (non-empty first) and then by creation date
                queryset = queryset.annotate(
                    has_experience=Case(
                        When(mentoring_experience__isnull=False, mentoring_experience__gt='', then=0),
                        default=1,
                        output_field=IntegerField(),
                    )
                ).order_by('has_experience', '-created_at')
            elif sort == 'availability':
                # Sort by availability status (AVAILABLE first, then LIMITED, then others)
                queryset = queryset.order_by(
                    Case(
                        When(availability_status='AVAILABLE', then=0),
                        When(availability_status='LIMITED', then=1),
                        default=2,
                        output_field=IntegerField(),
                    ),
                    '-created_at'
                )
            else:  # Default sorting by most recently joined mentors
                queryset = queryset.order_by('-created_at')
            
            return queryset.select_related('user')
        except Exception as e:
            raise ValueError(f"Error filtering mentors: {str(e)}")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        print(f"Toggle availability request for mentor ID: {pk}")
        
        try:
            mentor = self.get_object()
            print(f"Mentor found: {mentor}, User: {mentor.user}")
            
            if mentor.user != request.user:
                return Response(
                    {"detail": "You don't have permission to modify this mentor profile."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the is_available value from the request data
            is_available = request.data.get('is_available', None)
            print(f"Request data: {request.data}, is_available: {is_available}")
            
            if is_available is not None:
                # Convert string to boolean if necessary
                if isinstance(is_available, str):
                    is_available = is_available.lower() == 'true'
                mentor.accepting_mentees = is_available
            else:
                # Toggle if no value provided
                mentor.accepting_mentees = not mentor.accepting_mentees
            
            mentor.save()
            print(f"Mentor updated, accepting_mentees: {mentor.accepting_mentees}")
            
            return Response({
                'message': f'Availability {"enabled" if mentor.accepting_mentees else "disabled"} successfully',
                'accepting_mentees': mentor.accepting_mentees
            })
        except Exception as e:
            print(f"Error in toggle_availability: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MentorshipRequestViewSet(viewsets.ModelViewSet):
    serializer_class = MentorshipRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsMentorshipParticipant]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorshipRequest.objects.filter(mentor=user.mentor_profile)
        return MentorshipRequest.objects.filter(mentee=user)

    def create(self, request, *args, **kwargs):
        try:
            # Get the mentor
            mentor_id = request.data.get('mentor_id')
            mentor = get_object_or_404(Mentor, id=mentor_id)
            
            # Check if user is trying to request mentorship from their own profile
            if mentor.user == request.user:
                return Response(
                    {"detail": "You cannot request mentorship from your own mentor profile."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create the mentorship request
            mentorship_request = serializer.save(
                mentee=request.user,
                status='PENDING'
            )
            
            # Return the created request data
            response_serializer = self.get_serializer(mentorship_request)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except serializers.ValidationError as e:
            return Response(
                {"detail": str(e.detail[0]) if isinstance(e.detail, list) else e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": "Failed to create mentorship request. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        mentorship = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(MentorshipRequest.STATUS_CHOICES):
            return Response(
                {"detail": "Invalid status provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if mentorship.mentor.user != request.user:
            return Response(
                {"detail": "Only the mentor can update the status."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            mentorship.status = new_status
            mentorship.save()
            return Response(self.get_serializer(mentorship).data)
        except Exception as e:
            return Response(
                {"detail": "Failed to update request status. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_timeline(self, request, pk=None):
        """
        Update the timeline milestones for a mentorship request.
        This endpoint handles both:
        1. Creating/updating the full timeline (with expected_end_date and timeline_milestones)
        2. Updating milestone statuses within an existing timeline
        """
        mentorship = self.get_object()
        
        # Check if user is a participant of this mentorship
        if (mentorship.mentor.user != request.user and 
            mentorship.mentee != request.user):
            return Response(
                {"detail": "You do not have permission to update this timeline."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            # Check if this is a full timeline update
            timeline_milestones = request.data.get('timeline_milestones')
            expected_end_date = request.data.get('expected_end_date')
            
            # Check if this is a progress percentage update
            progress_percentage = request.data.get('progress_percentage')
            
            # Check if this is a milestone status update
            update_milestones = request.data.get('update_milestones_in_timeline', False)
            milestone_statuses = request.data.get('milestone_statuses', [])
            
            # Case 1: Full timeline update
            if timeline_milestones is not None:
                mentorship.timeline_milestones = timeline_milestones
                if expected_end_date:
                    mentorship.expected_end_date = expected_end_date
                mentorship.save()
                return Response(self.get_serializer(mentorship).data)
                
            # Case 2: Progress percentage update
            if progress_percentage is not None:
                mentorship.progress_percentage = progress_percentage
                mentorship.save()
                return Response(self.get_serializer(mentorship).data)
                
            # Case 3: Milestone status update
            if update_milestones and milestone_statuses:
                # Get current timeline
                timeline_text = mentorship.timeline_milestones
                if not timeline_text:
                    return Response(
                        {"detail": "No timeline set for this mentorship."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                # Parse the timeline text and update milestone statuses
                lines = timeline_text.split('\n')
                updated_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        updated_lines.append(line)
                        continue
                    
                    # Check if this is a milestone line
                    match = line.startswith('Week/Day ')
                    if not match:
                        updated_lines.append(line)
                        continue
                    
                    # Check if this milestone needs to be updated
                    found_match = False
                    for milestone in milestone_statuses:
                        milestone_period = milestone.get('period')
                        milestone_desc = milestone.get('description')
                        milestone_status = milestone.get('status')
                        
                        if milestone_period and f"Week/Day {milestone_period}:" in line:
                            # Extract the description without status
                            current_desc = line.split(':', 1)[1].strip()
                            if '[' in current_desc:
                                current_desc = current_desc.split('[')[0].strip()
                            
                            # If description is provided, check if it matches
                            if milestone_desc and not current_desc.startswith(milestone_desc):
                                continue
                                
                            # Update the line with the new status
                            updated_line = f"Week/Day {milestone_period}: {current_desc} [{milestone_status}]"
                            updated_lines.append(updated_line)
                            found_match = True
                            break
                    
                    # If no match was found, keep the original line
                    if not found_match:
                        updated_lines.append(line)
                
                # Update the timeline_milestones field
                mentorship.timeline_milestones = '\n'.join(updated_lines)
                mentorship.save()
                
                # Update progress percentage based on completed milestones
                self.update_progress_percentage(mentorship)
                
                return Response(self.get_serializer(mentorship).data)
            
            # If none of the above cases match, return an error
            return Response(
                {"detail": "Invalid request. Please provide timeline_milestones, progress_percentage, or milestone_statuses."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"detail": f"Failed to update timeline: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update_progress_percentage(self, mentorship):
        """Helper method to update the progress percentage based on milestone completion."""
        if not mentorship.timeline_milestones:
            return
            
        lines = mentorship.timeline_milestones.split('\n')
        total_milestones = 0
        completed_milestones = 0
        in_progress_milestones = 0
        
        for line in lines:
            if line.startswith('Week/Day '):
                total_milestones += 1
                if '[COMPLETED]' in line:
                    completed_milestones += 1
                elif '[IN_PROGRESS]' in line:
                    in_progress_milestones += 1
        
        if total_milestones > 0:
            # Calculate progress: completed + half of in-progress
            progress = (completed_milestones + (in_progress_milestones * 0.5)) / total_milestones
            mentorship.progress_percentage = int(progress * 100)
            mentorship.save()

class MentorshipMeetingViewSet(viewsets.ModelViewSet):
    serializer_class = MentorshipMeetingSerializer
    permission_classes = [permissions.IsAuthenticated, IsMentorshipParticipant, MentorOnlyForDelete]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorshipMeeting.objects.filter(mentorship__mentor=user.mentor_profile)
        return MentorshipMeeting.objects.filter(mentorship__mentee=user)

    def perform_create(self, serializer):
        mentorship = get_object_or_404(
            MentorshipRequest,
            Q(mentor__user=self.request.user) | Q(mentee=self.request.user),
            pk=self.request.data.get('mentorship')
        )
        serializer.save(mentorship=mentorship)

class MentorshipMessageViewSet(viewsets.ModelViewSet):
    serializer_class = MentorshipMessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMentorshipParticipant]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorshipMessage.objects.filter(mentorship__mentor=user.mentor_profile)
        return MentorshipMessage.objects.filter(mentorship__mentee=user)

    def perform_create(self, serializer):
        mentorship = get_object_or_404(
            MentorshipRequest,
            Q(mentor__user=self.request.user) | Q(mentee=self.request.user),
            pk=self.request.data.get('mentorship')
        )
        serializer.save(mentorship=mentorship, sender=self.request.user)

class MentorshipProgressViewSet(viewsets.ModelViewSet):
    serializer_class = MentorshipProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsMentorshipParticipant]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'mentor_profile'):
            return MentorshipProgress.objects.filter(mentorship__mentor=user.mentor_profile)
        return MentorshipProgress.objects.filter(mentorship__mentee=user)

    def perform_create(self, serializer):
        mentorship = get_object_or_404(
            MentorshipRequest,
            Q(mentor__user=self.request.user) | Q(mentee=self.request.user),
            pk=self.request.data.get('mentorship')
        )
        serializer.save(mentorship=mentorship, created_by=self.request.user)

class TimelineMilestoneViewSet(viewsets.ModelViewSet):
    serializer_class = TimelineMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return TimelineMilestone.objects.filter(
            Q(mentorship__mentor__user=user) | Q(mentorship__mentee=user)
        )
    
    @action(detail=False, methods=['post'])
    def update_batch(self, request):
        milestones_data = request.data.get('milestones', [])
        updated_milestones = []
        
        for milestone_data in milestones_data:
            milestone_id = milestone_data.get('id')
            try:
                milestone = TimelineMilestone.objects.get(id=milestone_id)
                # Check if user is part of this mentorship
                if request.user != milestone.mentorship.mentor.user and request.user != milestone.mentorship.mentee:
                    return Response({"error": "You don't have permission to update this milestone"}, 
                                   status=status.HTTP_403_FORBIDDEN)
                
                milestone.status = milestone_data.get('status', milestone.status)
                milestone.save()
                updated_milestones.append(TimelineMilestoneSerializer(milestone).data)
            except TimelineMilestone.DoesNotExist:
                return Response({"error": f"Milestone with id {milestone_id} not found"}, 
                               status=status.HTTP_404_NOT_FOUND)
        
        return Response({"milestones": updated_milestones}, status=status.HTTP_200_OK)

@login_required
def update_quick_progress(request, mentorship_id):
    # Ensure the request is a POST request
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    # Get the mentorship request or return 404
    mentorship = get_object_or_404(MentorshipRequest, id=mentorship_id)
    
    # Check if user is part of this mentorship
    if request.user != mentorship.mentor.user and request.user != mentorship.mentee:
        return JsonResponse({"error": "You don't have permission to update this mentorship"}, status=403)
    
    # Get the note from the request data
    import json
    data = json.loads(request.body)
    note = data.get('note', '')
    
    # Create a progress update if note is provided
    if note.strip():
        progress = MentorshipProgress.objects.create(
            mentorship=mentorship,
            title='Progress Update',
            description=note,
            created_by=request.user
        )
    
    # Update the progress percentage if provided
    progress_percentage = data.get('progress_percentage')
    if progress_percentage is not None:
        try:
            progress_percentage = int(progress_percentage)
            if 0 <= progress_percentage <= 100:
                mentorship.progress_percentage = progress_percentage
                mentorship.save()
        except (ValueError, TypeError):
            pass
    
    return JsonResponse({"success": True})

@login_required
def update_mentorship_status(request, mentorship_id):
    # Ensure the request is a POST request
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    # Get the mentorship request or return 404
    mentorship = get_object_or_404(MentorshipRequest, id=mentorship_id)
    
    # Check if user is part of this mentorship
    if request.user != mentorship.mentor.user and request.user != mentorship.mentee:
        return JsonResponse({"error": "You don't have permission to update this mentorship"}, status=403)
    
    # Get the status and reason from the request data
    import json
    data = json.loads(request.body)
    new_status = data.get('status', '')
    reason = data.get('reason', '')
    
    # Validate the status
    valid_statuses = ['PAUSED', 'COMPLETED', 'CANCELLED']
    if new_status not in valid_statuses:
        return JsonResponse({"error": "Invalid status provided"}, status=400)
    
    # Update the mentorship status
    mentorship.status = new_status
    
    # If the mentorship is completed or cancelled, update the end date
    if new_status in ['COMPLETED', 'CANCELLED']:
        mentorship.end_date = timezone.now().date()
        
        # If the mentor is the one ending the mentorship, decrement their current_mentees count
        if request.user == mentorship.mentor.user:
            mentor = mentorship.mentor
            if mentor.current_mentees > 0:
                mentor.current_mentees -= 1
                mentor.save()
    
    # Create a progress update with the reason
    if reason.strip():
        status_messages = {
            'PAUSED': 'Mentorship Paused',
            'COMPLETED': 'Mentorship Completed',
            'CANCELLED': 'Mentorship Cancelled'
        }
        
        progress = MentorshipProgress.objects.create(
            mentorship=mentorship,
            title=status_messages.get(new_status, 'Status Update'),
            description=f"Status changed to {new_status}: {reason}",
            created_by=request.user
        )
    
    mentorship.save()
    
    return JsonResponse({
        "success": True,
        "message": f"Mentorship status updated to {new_status}"
    })

@login_required
def set_timeline(request):
    """
    View for setting the timeline for a mentorship.
    This endpoint handles the POST request from the dashboard to set a timeline.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    
    # Parse the JSON data
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    
    # Get the mentorship request
    mentorship_id = data.get('mentorship_id')
    if not mentorship_id:
        return JsonResponse({"error": "Mentorship ID is required"}, status=400)
    
    try:
        mentorship = get_object_or_404(MentorshipRequest, id=mentorship_id)
    except:
        return JsonResponse({"error": "Mentorship not found"}, status=404)
    
    # Check if user is part of this mentorship
    if request.user != mentorship.mentor.user and request.user != mentorship.mentee:
        return JsonResponse({"error": "You don't have permission to update this mentorship"}, status=403)
    
    # Get the timeline data
    expected_end_date = data.get('expected_end_date')
    milestones = data.get('milestones', [])
    notes = data.get('notes', '')
    
    # Format the timeline milestones
    timeline_text = ""
    for milestone in milestones:
        period = milestone.get('period', '')
        description = milestone.get('description', '')
        if period and description:
            timeline_text += f"Week/Day {period}: {description} [NOT_STARTED]\n"
    
    # Add notes if provided
    if notes:
        timeline_text += f"\nNotes:\n{notes}"
    
    # Update the mentorship
    mentorship.timeline_milestones = timeline_text
    if expected_end_date:
        try:
            from datetime import datetime
            mentorship.expected_end_date = datetime.strptime(expected_end_date, '%Y-%m-%d').date()
        except:
            pass
    
    mentorship.save()
    
    return JsonResponse({"success": True})
