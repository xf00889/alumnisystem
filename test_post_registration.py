import os
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from accounts.models import Profile
from accounts.forms import PostRegistrationForm

def test_post_registration_form():
    print("=== Testing PostRegistrationForm ===\n")
    
    # Create test user
    User = get_user_model()
    test_user, created = User.objects.get_or_create(
        username='testuser2',
        defaults={
            'email': 'testuser2@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Ensure user has a profile
    profile, created = Profile.objects.get_or_create(user=test_user)
    print(f"User: {test_user.username}")
    print(f"Profile created: {created}")
    print(f"Registration completed: {profile.has_completed_registration}")
    
    # Test form with valid data
    form_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'college': 'CAS',
        'course_graduated': 'BSIT',
        'graduation_year': 2020,
        'present_occupation': 'Software Developer',
        'company_name': 'Tech Company'
    }
    
    print("\n1. Testing form validation...")
    form = PostRegistrationForm(data=form_data)
    if form.is_valid():
        print("✓ Form is valid")
        
        print("\n2. Testing form save...")
        try:
            form.save(test_user)
            print("✓ Form saved successfully")
            
            # Check if registration is now complete
            profile.refresh_from_db()
            print(f"✓ Registration completed: {profile.has_completed_registration}")
            
        except Exception as e:
            print(f"✗ Error saving form: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"✗ Form is invalid: {form.errors}")

def test_post_registration_view():
    print("\n=== Testing PostRegistration View ===\n")
    
    client = Client(HTTP_HOST='127.0.0.1:8000')
    
    # Create test user with incomplete registration
    User = get_user_model()
    test_user, created = User.objects.get_or_create(
        username='testuser3',
        defaults={
            'email': 'testuser3@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Ensure user has a profile with incomplete registration
    profile, created = Profile.objects.get_or_create(user=test_user)
    profile.has_completed_registration = False
    profile.save()
    
    # Login the user
    client.force_login(test_user)
    
    print("1. Testing GET /profile/post-registration/")
    try:
        response = client.get('/profile/post-registration/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ GET request successful")
        else:
            print(f"✗ GET request failed with status {response.status_code}")
    except Exception as e:
        print(f"✗ Error in GET request: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2. Testing POST /profile/post-registration/")
    try:
        post_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'college': 'CAS',
            'course_graduated': 'BSIT',
            'graduation_year': 2020,
            'present_occupation': 'Software Developer',
            'company_name': 'Tech Company'
        }
        
        response = client.post('/profile/post-registration/', data=post_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"✓ POST request successful, redirected to: {response.url}")
        elif response.status_code == 200:
            print("✓ POST request returned 200 (form might have errors)")
        else:
            print(f"✗ POST request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error in POST request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_post_registration_form()
    test_post_registration_view()
    print("\n=== Test Complete ===")