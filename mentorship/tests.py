from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import Profile

User = get_user_model()


class MenteeDashboardTemplateTest(TestCase):
    """Test mentee dashboard template with safe profile access"""
    
    def setUp(self):
        self.client = Client()
        # Create a user without a profile
        self.user_without_profile = User.objects.create_user(
            username='testuser_no_profile',
            email='noprofile@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Ensure no profile exists
        Profile.objects.filter(user=self.user_without_profile).delete()
        
        # Create a user with a profile
        self.user_with_profile = User.objects.create_user(
            username='testuser_with_profile',
            email='withprofile@test.com',
            password='testpass123',
            first_name='Profile',
            last_name='User'
        )
        # Ensure profile exists
        Profile.objects.get_or_create(user=self.user_with_profile)
    
    def test_mentee_dashboard_without_profile(self):
        """Test that mentee dashboard loads for user without profile"""
        self.client.login(username='testuser_no_profile', password='testpass123')
        response = self.client.get(reverse('mentorship:mentee_dashboard'), follow=True)
        
        # Should return 200 OK, not 500 error - this is the key test
        # The view should handle missing profiles gracefully
        self.assertEqual(response.status_code, 200)
        
        # Verify no server error occurred
        self.assertNotIn(b'500', response.content)
        self.assertNotIn(b'Internal Server Error', response.content)
    
    def test_mentee_dashboard_with_profile(self):
        """Test that mentee dashboard loads for user with profile"""
        self.client.login(username='testuser_with_profile', password='testpass123')
        response = self.client.get(reverse('mentorship:mentee_dashboard'), follow=True)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verify no server error occurred
        self.assertNotIn(b'500', response.content)
        self.assertNotIn(b'Internal Server Error', response.content)


class MentorSearchAPITest(TestCase):
    """Test mentor search API with safe profile access"""
    
    def setUp(self):
        self.client = Client()
        
        # Create a regular user for testing
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create a mentor user without a profile
        self.mentor_user_no_profile = User.objects.create_user(
            username='mentor_no_profile',
            email='mentor_no_profile@test.com',
            password='testpass123',
            first_name='Mentor',
            last_name='NoProfile'
        )
        # Ensure no profile exists
        Profile.objects.filter(user=self.mentor_user_no_profile).delete()
        
        # Create a mentor user with a profile
        self.mentor_user_with_profile = User.objects.create_user(
            username='mentor_with_profile',
            email='mentor_with_profile@test.com',
            password='testpass123',
            first_name='Mentor',
            last_name='WithProfile'
        )
        # Ensure profile exists with data
        profile, created = Profile.objects.get_or_create(user=self.mentor_user_with_profile)
        if not profile.current_position:
            profile.current_position = 'Senior Developer'
            profile.save(update_fields=['current_position'])
        
        # Import Mentor model
        from accounts.models import Mentor
        
        # Create mentor profiles
        self.mentor_no_profile = Mentor.objects.create(
            user=self.mentor_user_no_profile,
            expertise_areas='Python, Django',
            availability_status='AVAILABLE',
            accepting_mentees=True,
            is_active=True
        )
        
        self.mentor_with_profile = Mentor.objects.create(
            user=self.mentor_user_with_profile,
            expertise_areas='JavaScript, React',
            availability_status='AVAILABLE',
            accepting_mentees=True,
            is_active=True
        )
    
    def test_mentor_search_page_loads(self):
        """Test that mentor search page loads without errors"""
        # Ensure test user has a profile
        Profile.objects.get_or_create(user=self.test_user)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('mentorship:mentor_search'), follow=True)
        
        # Should return 200 OK (following redirects)
        self.assertEqual(response.status_code, 200)
        
        # Verify no server error occurred
        self.assertNotIn(b'500', response.content)
        self.assertNotIn(b'Internal Server Error', response.content)
    
    def test_mentor_api_with_missing_profiles(self):
        """Test that mentor API serializer returns data safely for mentors without profiles"""
        from mentorship.serializers import MentorSerializer
        from rest_framework.request import Request
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/api/mentors/')
        request.user = self.test_user
        
        # Serialize both mentors
        mentors = [self.mentor_no_profile, self.mentor_with_profile]
        serializer = MentorSerializer(
            mentors,
            many=True,
            context={'request': Request(request)}
        )
        
        # Should not raise an exception
        data = serializer.data
        
        # Should return list of 2 mentors
        self.assertEqual(len(data), 2)
        
        # Find mentor without profile
        mentor_no_profile_data = next(
            (m for m in data if m['user']['id'] == self.mentor_user_no_profile.id),
            None
        )
        
        # Verify mentor data is present
        self.assertIsNotNone(mentor_no_profile_data)
        
        # Verify user data is safe (should have None or empty string for missing profile fields)
        self.assertEqual(mentor_no_profile_data['user']['full_name'], 'Mentor NoProfile')
        self.assertIsNone(mentor_no_profile_data['user']['avatar'])
        # current_position can be None or empty string when profile is missing
        self.assertIn(mentor_no_profile_data['user']['current_position'], [None, ''])
        
        # Find mentor with profile
        mentor_with_profile_data = next(
            (m for m in data if m['user']['id'] == self.mentor_user_with_profile.id),
            None
        )
        
        # Verify mentor with profile has data
        self.assertIsNotNone(mentor_with_profile_data)
        self.assertEqual(mentor_with_profile_data['user']['full_name'], 'Mentor WithProfile')
        # The key test is that it doesn't raise an exception, position value may vary
        self.assertIsNotNone(mentor_with_profile_data['user'])
    
    def test_mentor_serializer_handles_missing_profile(self):
        """Test that MentorSerializer handles missing profiles gracefully"""
        from mentorship.serializers import MentorSerializer
        from rest_framework.request import Request
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/api/mentors/')
        request.user = self.test_user
        
        # Serialize mentor without profile
        serializer = MentorSerializer(
            self.mentor_no_profile,
            context={'request': Request(request)}
        )
        
        # Should not raise an exception
        data = serializer.data
        
        # Verify safe handling of missing profile
        self.assertIsNone(data['user']['avatar'])
        # current_position can be None or empty string when profile is missing
        self.assertIn(data['user']['current_position'], [None, ''])
        self.assertEqual(data['user']['full_name'], 'Mentor NoProfile')
