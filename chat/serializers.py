from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Conversation, Message, UserBlock
from alumni_directory.models import Alumni

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    student_id = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    college = serializers.SerializerMethodField()
    campus = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
                 'student_id', 'course', 'batch', 'college', 'campus', 'avatar_url', 'is_active']

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        if not name:
            try:
                alumni = obj.alumni
                if alumni.course:
                    return f"{obj.username} ({alumni.course})"
            except Alumni.DoesNotExist:
                pass
        return name or obj.username

    def get_student_id(self, obj):
        try:
            return str(obj.alumni.graduation_year)
        except Alumni.DoesNotExist:
            return None

    def get_course(self, obj):
        try:
            return obj.alumni.course
        except Alumni.DoesNotExist:
            return None

    def get_batch(self, obj):
        try:
            return str(obj.alumni.graduation_year)
        except Alumni.DoesNotExist:
            return None

    def get_college(self, obj):
        try:
            return obj.alumni.get_college_display()
        except Alumni.DoesNotExist:
            return None

    def get_campus(self, obj):
        try:
            return obj.alumni.get_campus_display()
        except Alumni.DoesNotExist:
            return None

    def get_avatar_url(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'timestamp', 'is_read', 'is_deleted']
        read_only_fields = ['is_deleted', 'deleted_at']

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'name', 'participants', 'created_at', 'is_group_chat', 'created_by', 'last_message', 'unread_count']
        read_only_fields = ['created_at']

    def get_last_message(self, obj):
        last_message = obj.messages.filter(is_deleted=False).first()
        if last_message:
            return MessageSerializer(last_message).data
        return None

    def get_unread_count(self, obj):
        user = self.context.get('request').user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

class UserBlockSerializer(serializers.ModelSerializer):
    blocker = UserSerializer(read_only=True)
    blocked = UserSerializer(read_only=True)

    class Meta:
        model = UserBlock
        fields = ['id', 'blocker', 'blocked', 'timestamp'] 