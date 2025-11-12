from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class ProfileSignalTestCase(TestCase):
    """Test profile creation signals"""
    
    def test_profile_created_on_user_creation(self):
        """Test that a profile is automatically created when a user is created"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Profile should be created automatically
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.profile.user, user)
    
    def test_profile_get_or_create_prevents_duplicates(self):
        """Test that get_or_create prevents duplicate profiles"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Try to create another profile manually
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Should not create a new profile
        self.assertFalse(created)
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
