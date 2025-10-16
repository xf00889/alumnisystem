"""
API views for the setup app.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
from .serializers import (
    SiteConfigurationSerializer, 
    EmailConfigurationSerializer, 
    FeatureToggleSerializer,
    SetupProgressSerializer,
    EmailTestSerializer,
    DatabaseTestSerializer
)
from .models import SiteConfiguration, EmailConfiguration, FeatureToggle
from .utils import get_setup_progress
import logging

logger = logging.getLogger(__name__)


class SetupProgressAPIView(APIView):
    """API view to get setup progress."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current setup progress."""
        progress = get_setup_progress()
        serializer = SetupProgressSerializer(progress)
        return Response(serializer.data)


class TestEmailAPIView(APIView):
    """API view to test email configuration."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Test email configuration by sending a test email."""
        test_email = request.data.get('test_email')
        
        if not test_email:
            return Response(
                {'success': False, 'message': 'Test email address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Send test email
            send_mail(
                'Test Email from Setup',
                'This is a test email to verify your email configuration.',
                settings.DEFAULT_FROM_EMAIL,
                [test_email],
                fail_silently=False,
            )
            
            serializer = EmailTestSerializer({
                'test_email': test_email,
                'success': True,
                'message': 'Test email sent successfully!'
            })
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Email test failed: {e}")
            serializer = EmailTestSerializer({
                'test_email': test_email,
                'success': False,
                'message': str(e)
            })
            
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class CheckDatabaseAPIView(APIView):
    """API view to check database connection."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Check database connection."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if result:
                serializer = DatabaseTestSerializer({
                    'success': True,
                    'message': 'Database connection successful!'
                })
                return Response(serializer.data)
            else:
                serializer = DatabaseTestSerializer({
                    'success': False,
                    'message': 'Database connection failed'
                })
                return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            serializer = DatabaseTestSerializer({
                'success': False,
                'message': str(e)
            })
            return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SiteConfigurationAPIView(APIView):
    """API view for site configuration management."""
    permission_classes = [AllowAny]  # Allow during setup
    
    def get(self, request):
        """Get all site configurations."""
        configurations = SiteConfiguration.objects.filter(is_active=True)
        serializer = SiteConfigurationSerializer(configurations, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create or update site configuration."""
        key = request.data.get('key')
        value = request.data.get('value')
        description = request.data.get('description', '')
        
        if not key or value is None:
            return Response(
                {'error': 'Key and value are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            setting = SiteConfiguration.set_setting(key, value, description)
            serializer = SiteConfigurationSerializer(setting)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to set configuration: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailConfigurationAPIView(APIView):
    """API view for email configuration management."""
    permission_classes = [AllowAny]  # Allow during setup
    
    def get(self, request):
        """Get email configurations."""
        configurations = EmailConfiguration.objects.filter(is_active=True)
        serializer = EmailConfigurationSerializer(configurations, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create email configuration."""
        serializer = EmailConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeatureToggleAPIView(APIView):
    """API view for feature toggle management."""
    permission_classes = [AllowAny]  # Allow during setup
    
    def get(self, request):
        """Get all feature toggles."""
        toggles = FeatureToggle.objects.all()
        serializer = FeatureToggleSerializer(toggles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create or update feature toggle."""
        serializer = FeatureToggleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
