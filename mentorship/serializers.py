from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import Mentor, MentorshipRequest
from .models import (
    MentorshipMeeting, MentorshipMessage, MentorshipProgress,
    MentorshipGoal, MentorshipSkillProgress, TimelineMilestone
)

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar = serializers.SerializerMethodField()
    current_position = serializers.CharField(source='profile.current_position', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'avatar', 'current_position']
        read_only_fields = ['email']

    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None

class MentorSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    current_availability = serializers.SerializerMethodField()
    expertise_list = serializers.SerializerMethodField()
    has_requested = serializers.SerializerMethodField()
    
    class Meta:
        model = Mentor
        fields = [
            'id', 'user', 'expertise_areas', 'expertise_list', 'availability_status',
            'max_mentees', 'current_mentees', 'mentoring_experience', 'expectations',
            'preferred_contact_method', 'is_active', 'current_availability',
            'accepting_mentees', 'has_requested'
        ]
        read_only_fields = ['current_mentees']

    def get_current_availability(self, obj):
        return obj.max_mentees - obj.current_mentees if obj.is_active else 0

    def get_expertise_list(self, obj):
        if not obj.expertise_areas:
            return []
        return [area.strip() for area in obj.expertise_areas.split(',') if area.strip()]
        
    def get_has_requested(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
            
        # Check if the current user has an active or pending request with this mentor
        return obj.mentorship_requests.filter(
            mentee=request.user, 
            status__in=['PENDING', 'APPROVED', 'PAUSED']
        ).exists()

class MentorshipRequestSerializer(serializers.ModelSerializer):
    mentor = MentorSerializer(read_only=True)
    mentee = UserBasicSerializer(read_only=True)
    mentor_id = serializers.PrimaryKeyRelatedField(
        queryset=Mentor.objects.filter(is_active=True, accepting_mentees=True),
        write_only=True,
        source='mentor'
    )
    
    class Meta:
        model = MentorshipRequest
        fields = [
            'id', 'mentor', 'mentor_id', 'mentee', 'skills_seeking',
            'goals', 'message', 'status', 'start_date', 'end_date',
            'expected_end_date', 'timeline_milestones', 'progress_percentage',
            'feedback', 'rating', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'feedback', 'rating', 'start_date', 'end_date']

    def validate(self, data):
        mentor = data.get('mentor')
        if not mentor:
            raise serializers.ValidationError({
                "mentor_id": "Please select a valid mentor."
            })
            
        if not mentor.is_active:
            raise serializers.ValidationError({
                "mentor_id": "This mentor is not currently active."
            })
            
        if not mentor.accepting_mentees:
            raise serializers.ValidationError({
                "mentor_id": "This mentor is not accepting new mentees at this time."
            })
            
        if mentor.current_mentees >= mentor.max_mentees:
            raise serializers.ValidationError({
                "mentor_id": "This mentor has reached their maximum number of mentees."
            })
            
        # Check if user is trying to request mentorship from their own profile
        mentee = self.context['request'].user
        if mentor.user == mentee:
            raise serializers.ValidationError({
                "mentor_id": "You cannot request mentorship from your own mentor profile."
            })
            
        # Check for existing requests
        existing_request = MentorshipRequest.objects.filter(
            mentor=mentor,
            mentee=mentee,
            status__in=['PENDING', 'APPROVED']
        ).first()
        
        if existing_request:
            status_msg = "pending" if existing_request.status == 'PENDING' else "active"
            raise serializers.ValidationError({
                "mentor_id": f"You already have a {status_msg} mentorship request with this mentor."
            })
        
        # Validate required fields
        if not data.get('skills_seeking', '').strip():
            raise serializers.ValidationError({
                "skills_seeking": "Please specify the skills you're seeking help with."
            })
            
        if not data.get('goals', '').strip():
            raise serializers.ValidationError({
                "goals": "Please specify your mentorship goals."
            })
            
        if not data.get('message', '').strip():
            raise serializers.ValidationError({
                "message": "Please provide an introduction message."
            })
        
        return data

class MentorshipMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorshipMeeting
        fields = [
            'id', 'mentorship', 'title', 'description', 'meeting_date',
            'duration', 'meeting_link', 'status', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']
        extra_kwargs = {
            'duration': {'required': False},
        }

    def validate_meeting_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Meeting date cannot be in the past")
        return value

class MentorshipMessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = MentorshipMessage
        fields = [
            'id', 'mentorship', 'sender', 'content',
            'attachment', 'is_read', 'created_at'
        ]
        read_only_fields = ['is_read', 'created_at']

class MentorshipProgressSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)
    completed_items_list = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = MentorshipProgress
        fields = [
            'id', 'mentorship', 'title', 'description',
            'completed_items', 'completed_items_list', 'next_steps',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'completed_items': {'required': False},
            'next_steps': {'required': False}
        }

    def validate(self, data):
        if 'completed_items_list' in data:
            data['completed_items'] = self.convert_to_json_string(data.pop('completed_items_list'))
        return data

    @staticmethod
    def convert_to_json_string(items):
        import json
        return json.dumps(items)

class TimelineMilestoneSerializer(serializers.ModelSerializer):
    """
    Serializer for the TimelineMilestone model.
    """
    class Meta:
        model = TimelineMilestone
        fields = ['id', 'mentorship', 'period', 'description', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at'] 