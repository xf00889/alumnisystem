"""
Serializers for the setup app API.
"""
from rest_framework import serializers
from .models import SiteConfiguration, EmailConfiguration, FeatureToggle, SetupState


class SiteConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for SiteConfiguration model."""
    
    class Meta:
        model = SiteConfiguration
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for EmailConfiguration model."""
    
    class Meta:
        model = EmailConfiguration
        fields = ['id', 'name', 'backend', 'host', 'port', 'use_tls', 'username', 'password', 'from_email', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class FeatureToggleSerializer(serializers.ModelSerializer):
    """Serializer for FeatureToggle model."""
    
    class Meta:
        model = FeatureToggle
        fields = ['id', 'name', 'is_enabled', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SetupStateSerializer(serializers.ModelSerializer):
    """Serializer for SetupState model."""
    
    class Meta:
        model = SetupState
        fields = ['id', 'is_complete', 'completed_at', 'setup_data', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SetupProgressSerializer(serializers.Serializer):
    """Serializer for setup progress information."""
    environment_setup = serializers.BooleanField()
    database_available = serializers.BooleanField()
    setup_complete = serializers.BooleanField()
    overall_progress = serializers.FloatField()


class EmailTestSerializer(serializers.Serializer):
    """Serializer for email testing."""
    test_email = serializers.EmailField()
    success = serializers.BooleanField()
    message = serializers.CharField()


class DatabaseTestSerializer(serializers.Serializer):
    """Serializer for database testing."""
    success = serializers.BooleanField()
    message = serializers.CharField()
