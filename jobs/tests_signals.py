"""
Tests for jobs app signals.

This module tests the automatic creation of JobPreference instances
when new users are created.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from jobs.models import JobPreference

User = get_user_model()


class JobPreferenceSignalTestCase(TestCase):
    """Test cases for JobPreference signal handlers"""
    
    def test_job_preference_created_on_user_creation(self):
        """
        Test that a JobPreference instance is automatically created
        when a new User is created.
        """
        # Create a new user
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Verify that JobPreference was created
        self.assertTrue(hasattr(user, 'job_preferences'))
        self.assertIsNotNone(user.job_preferences)
        self.assertEqual(user.job_preferences.user, user)
    
    def test_job_preference_has_default_values(self):
        """
        Test that the automatically created JobPreference has
        correct default values.
        """
        # Create a new user
        user = User.objects.create_user(
            username='testuser2',
            email='testuser2@example.com',
            password='testpass123'
        )
        
        # Get the JobPreference
        preferences = user.job_preferences
        
        # Verify default values
        self.assertFalse(preferences.is_configured)
        self.assertFalse(preferences.was_prompted)
        self.assertEqual(preferences.job_types, [])
        self.assertEqual(preferences.location_text, '')
        self.assertFalse(preferences.remote_only)
        self.assertFalse(preferences.willing_to_relocate)
        self.assertIsNone(preferences.minimum_salary)
        self.assertEqual(preferences.source_type, 'BOTH')
        self.assertEqual(preferences.industries, [])
        self.assertEqual(preferences.experience_levels, [])
        self.assertFalse(preferences.skill_matching_enabled)
        self.assertEqual(preferences.skill_match_threshold, 50)
        self.assertEqual(preferences.modification_count, 0)
        self.assertIsNone(preferences.first_configured_at)
    
    def test_job_preference_not_created_on_user_update(self):
        """
        Test that updating an existing user does not create
        a duplicate JobPreference.
        """
        # Create a new user
        user = User.objects.create_user(
            username='testuser3',
            email='testuser3@example.com',
            password='testpass123'
        )
        
        # Get the initial JobPreference
        initial_preference = user.job_preferences
        initial_preference_id = initial_preference.id
        
        # Update the user
        user.email = 'newemail@example.com'
        user.save()
        
        # Verify that the same JobPreference still exists
        user.refresh_from_db()
        self.assertEqual(user.job_preferences.id, initial_preference_id)
        
        # Verify only one JobPreference exists for this user
        preference_count = JobPreference.objects.filter(user=user).count()
        self.assertEqual(preference_count, 1)
    
    def test_multiple_users_get_separate_preferences(self):
        """
        Test that multiple users each get their own JobPreference instance.
        """
        # Create multiple users
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # Verify each user has their own JobPreference
        self.assertIsNotNone(user1.job_preferences)
        self.assertIsNotNone(user2.job_preferences)
        self.assertIsNotNone(user3.job_preferences)
        
        # Verify they are different instances
        self.assertNotEqual(user1.job_preferences.id, user2.job_preferences.id)
        self.assertNotEqual(user2.job_preferences.id, user3.job_preferences.id)
        self.assertNotEqual(user1.job_preferences.id, user3.job_preferences.id)
        
        # Verify each preference is linked to the correct user
        self.assertEqual(user1.job_preferences.user, user1)
        self.assertEqual(user2.job_preferences.user, user2)
        self.assertEqual(user3.job_preferences.user, user3)
    
    def test_job_preference_timestamps_set_on_creation(self):
        """
        Test that created_at and updated_at timestamps are set
        when JobPreference is created via signal.
        """
        # Create a new user
        user = User.objects.create_user(
            username='testuser4',
            email='testuser4@example.com',
            password='testpass123'
        )
        
        # Get the JobPreference
        preferences = user.job_preferences
        
        # Verify timestamps are set
        self.assertIsNotNone(preferences.created_at)
        self.assertIsNotNone(preferences.updated_at)
        
        # Verify created_at and updated_at are approximately equal (within 1 second)
        time_diff = abs((preferences.updated_at - preferences.created_at).total_seconds())
        self.assertLess(time_diff, 1.0)
