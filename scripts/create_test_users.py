import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from accounts.models import Profile
from alumni_directory.models import Alumni, CareerPath, Achievement

# Sample data for generating realistic test users
FIRST_NAMES = [
    'Juan', 'Maria', 'Pedro', 'Ana', 'Jose', 'Rosa', 'Carlos', 'Sofia',
    'Miguel', 'Isabella', 'Antonio', 'Gabriela', 'Luis', 'Carmen', 'Diego', 'Elena'
]

LAST_NAMES = [
    'Santos', 'Cruz', 'Reyes', 'Garcia', 'Torres', 'Ramos', 'Flores', 'Rivera',
    'Mendoza', 'Gonzales', 'Fernandez', 'Lopez', 'Martinez', 'Rodriguez', 'Perez', 'Gomez'
]

COMPANIES = [
    'Tech Innovators Inc.', 'Global Solutions Corp.', 'Digital Dynamics',
    'Future Systems', 'Creative Solutions', 'Data Analytics Pro',
    'Web Frontier', 'Cloud Computing Solutions', 'AI Research Lab',
    'Software Dynamics'
]

POSITIONS = [
    'Software Engineer', 'Data Analyst', 'Project Manager', 'Business Analyst',
    'Product Manager', 'UX Designer', 'System Administrator', 'DevOps Engineer',
    'Quality Assurance Engineer', 'Technical Lead'
]

SKILLS = [
    'Python', 'Java', 'JavaScript', 'SQL', 'React', 'Node.js', 'Docker',
    'Kubernetes', 'AWS', 'Azure', 'Machine Learning', 'Data Analysis',
    'Project Management', 'Agile Methodologies', 'UI/UX Design'
]

ACHIEVEMENTS = [
    {
        'title': 'Best Employee of the Year',
        'type': 'AWARD',
        'description': 'Recognized for outstanding performance and contribution to the company'
    },
    {
        'title': 'AWS Certified Solutions Architect',
        'type': 'CERTIFICATION',
        'description': 'Professional certification for AWS cloud architecture'
    },
    {
        'title': 'Published Research Paper',
        'type': 'PUBLICATION',
        'description': 'Research on modern software development practices'
    },
    {
        'title': 'Innovation Project Lead',
        'type': 'PROJECT',
        'description': 'Led a team of 10 in developing a revolutionary product'
    },
    {
        'title': 'Speaker at Tech Conference',
        'type': 'RECOGNITION',
        'description': 'Presented on emerging technologies at national conference'
    }
]

def create_test_users(num_users=10):
    created_users = []
    
    for i in range(num_users):
        # Create user
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
        username = f"{first_name.lower()}{last_name.lower()}{i}"
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User {username} already exists, skipping...")
            continue
            
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            first_name=first_name,
            last_name=last_name
        )
        
        # Check if profile already exists
        if not Profile.objects.filter(user=user).exists():
            profile = Profile.objects.create(
                user=user,
                phone_number=f"+639{random.randint(100000000, 999999999)}",
                bio=f"A passionate professional with {random.randint(2, 15)} years of experience"
            )
        else:
            profile = user.profile
        
        # Check if alumni record already exists
        if not Alumni.objects.filter(user=user).exists():
            graduation_year = random.randint(2010, 2023)
            alumni = Alumni.objects.create(
                user=user,
                gender=random.choice(['M', 'F']),
                date_of_birth=timezone.now() - timedelta(days=random.randint(8000, 15000)),
                phone_number=profile.phone_number,
                country='PH',
                province='Negros Oriental',
                city='Dumaguete City',
                address=f"{random.randint(1, 100)} Sample Street",
                college=random.choice(['CAS', 'CBA', 'CTE', 'CCJE', 'CEA']),
                campus='MAIN',
                graduation_year=graduation_year,
                course=random.choice([
                    'BS Computer Science',
                    'BS Information Technology',
                    'BS Business Administration',
                    'BS Accountancy',
                    'BS Education'
                ]),
                current_company=random.choice(COMPANIES),
                job_title=random.choice(POSITIONS),
                employment_status='EMPLOYED_FULL',
                skills=', '.join(random.sample(SKILLS, 5)),
                interests='Technology, Innovation, Leadership'
            )
        else:
            alumni = user.alumni
            
        # Create career paths if none exist
        if not CareerPath.objects.filter(alumni=alumni).exists():
            num_positions = random.randint(2, 4)
            current_date = timezone.now()
            
            for j in range(num_positions):
                is_current = (j == 0)
                start_date = current_date - timedelta(days=random.randint(365, 730))
                
                CareerPath.objects.create(
                    alumni=alumni,
                    company=random.choice(COMPANIES),
                    position=random.choice(POSITIONS),
                    start_date=start_date,
                    end_date=None if is_current else current_date - timedelta(days=1),
                    is_current=is_current,
                    description=f"Responsible for various projects and initiatives",
                    achievements="- Successfully completed multiple projects\n- Led team initiatives\n- Improved process efficiency",
                    promotion_type=random.choice(['PROMOTION', 'LATERAL', 'NEW_ROLE']),
                    salary_range=f"{random.randint(30, 100)}K - {random.randint(101, 200)}K",
                    location='Dumaguete City',
                    skills_gained=', '.join(random.sample(SKILLS, 3))
                )
                current_date = start_date
        
        # Create achievements if none exist
        if not Achievement.objects.filter(alumni=alumni).exists():
            num_achievements = random.randint(2, 4)
            achievement_list = random.sample(ACHIEVEMENTS, num_achievements)
            
            for achievement in achievement_list:
                Achievement.objects.create(
                    alumni=alumni,
                    title=achievement['title'],
                    achievement_type=achievement['type'],
                    date_achieved=timezone.now() - timedelta(days=random.randint(30, 1095)),
                    description=achievement['description'],
                    issuer=random.choice(COMPANIES)
                )
        
        created_users.append(user)
        print(f"Created user: {user.get_full_name()} ({user.email})")
    
    return created_users

if __name__ == '__main__':
    print("Creating test users...")
    users = create_test_users(num_users=30)
    print(f"\nCreated {len(users)} test users successfully!")
    print("\nTest user credentials:")
    print("Username format: firstnamelastnameN (e.g., juansantos0)")
    print("Password for all users: testpass123") 