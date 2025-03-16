import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumnisystem.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from surveys.models import Survey

def create_test_survey():
    # Get the first user (admin)
    user = User.objects.first()
    if not user:
        print("No users found in the system.")
        return
    
    # Create an active survey
    survey = Survey.objects.create(
        title='Alumni Feedback 2025',
        description='Please share your feedback about our alumni program and experiences. Your input helps us improve.',
        start_date=timezone.now(),
        end_date=timezone.now() + timezone.timedelta(days=30),
        status='active',
        created_by=user
    )
    
    print(f"Created survey: {survey.title}")
    print(f"Status: {survey.status}")
    print(f"Start date: {survey.start_date}")
    print(f"End date: {survey.end_date}")

if __name__ == '__main__':
    create_test_survey() 