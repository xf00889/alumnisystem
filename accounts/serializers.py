from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, Skill, SkillMatch
from jobs.models import JobPosting

User = get_user_model()

class SkillSerializer(serializers.ModelSerializer):
    skill_type_display = serializers.CharField(source='get_skill_type_display', read_only=True)
    proficiency_display = serializers.CharField(source='get_proficiency_level_display', read_only=True)
    
    class Meta:
        model = Skill
        fields = [
            'id', 'name', 'skill_type', 'skill_type_display',
            'proficiency_level', 'proficiency_display',
            'years_of_experience', 'last_used', 'is_primary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        from django.utils import timezone
        if data.get('last_used') and data['last_used'] > timezone.now().date():
            raise serializers.ValidationError("Last used date cannot be in the future")
        return data

class ProfileSkillsSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'skills']

class JobPostingBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosting
        fields = [
            'id', 'job_title', 'company_name', 'location',
            'job_type', 'experience_level', 'is_featured'
        ]

class SkillMatchSerializer(serializers.ModelSerializer):
    job = JobPostingBasicSerializer(read_only=True)
    profile = serializers.PrimaryKeyRelatedField(read_only=True)
    matched_skills_data = serializers.SerializerMethodField()
    missing_skills_data = serializers.SerializerMethodField()
    
    class Meta:
        model = SkillMatch
        fields = [
            'id', 'job', 'profile', 'match_score',
            'matched_skills', 'matched_skills_data',
            'missing_skills', 'missing_skills_data',
            'created_at', 'is_notified', 'is_viewed',
            'is_applied'
        ]
        read_only_fields = [
            'match_score', 'matched_skills', 'missing_skills',
            'created_at', 'is_notified'
        ]

    def get_matched_skills_data(self, obj):
        import json
        try:
            return json.loads(obj.matched_skills)
        except:
            return {}

    def get_missing_skills_data(self, obj):
        import json
        try:
            return json.loads(obj.missing_skills)
        except:
            return {}

class SkillMatchCalculationSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    profile_id = serializers.IntegerField()
    
    def validate(self, data):
        try:
            data['job'] = JobPosting.objects.get(pk=data['job_id'])
        except JobPosting.DoesNotExist:
            raise serializers.ValidationError("Job posting not found")
            
        try:
            data['profile'] = Profile.objects.get(pk=data['profile_id'])
        except Profile.DoesNotExist:
            raise serializers.ValidationError("Profile not found")
            
        return data 