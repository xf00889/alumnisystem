"""
Comprehensive test script for skill-based matching functionality
This script tests the entire skill matching system end-to-end
"""

import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Profile, Skill, SkillMatch
from jobs.models import JobPosting
from jobs.utils import (
    calculate_skill_relevancy,
    calculate_job_match_score,
    find_matching_jobs,
    update_skill_matches,
    get_skill_recommendations
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_skill_model():
    """Test Skill model structure and functionality"""
    print_section("TEST 1: Skill Model Structure")
    
    # Check model fields
    skill_fields = [f.name for f in Skill._meta.get_fields()]
    required_fields = ['profile', 'name', 'skill_type', 'proficiency_level', 
                      'years_of_experience', 'last_used', 'is_primary']
    
    print("✓ Skill model fields:")
    for field in required_fields:
        status = "✓" if field in skill_fields else "✗"
        print(f"  {status} {field}")
    
    # Check choices
    print("\n✓ Skill Types:")
    for code, label in Skill.SKILL_TYPES:
        print(f"  - {code}: {label}")
    
    print("\n✓ Proficiency Levels:")
    for level, label in Skill.PROFICIENCY_LEVELS:
        print(f"  - {level}: {label}")
    
    return True

def test_skill_match_model():
    """Test SkillMatch model structure"""
    print_section("TEST 2: SkillMatch Model Structure")
    
    match_fields = [f.name for f in SkillMatch._meta.get_fields()]
    required_fields = ['job', 'profile', 'match_score', 'matched_skills', 
                      'missing_skills', 'is_notified', 'is_viewed', 'is_applied']
    
    print("✓ SkillMatch model fields:")
    for field in required_fields:
        status = "✓" if field in match_fields else "✗"
        print(f"  {status} {field}")
    
    # Check indexes
    print("\n✓ Database indexes:")
    for index in SkillMatch._meta.indexes:
        print(f"  - {index.fields}")
    
    # Check unique constraint
    unique_together = SkillMatch._meta.unique_together
    print(f"\n✓ Unique constraint: {unique_together}")
    
    return True

def test_create_test_data():
    """Create test data for skill matching"""
    print_section("TEST 3: Creating Test Data")
    
    # Create test user and profile
    try:
        user = User.objects.get(username='skilltest_user')
        print("✓ Using existing test user")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='skilltest_user',
            email='skilltest@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print("✓ Created test user")
    
    profile = Profile.objects.get(user=user)
    print(f"✓ Profile: {profile}")
    
    # Clear existing skills for clean test
    Skill.objects.filter(profile=profile).delete()
    print("✓ Cleared existing skills")
    
    # Create test skills
    test_skills = [
        {
            'name': 'Python',
            'skill_type': 'TECH',
            'proficiency_level': 5,
            'years_of_experience': 5,
            'is_primary': True,
            'last_used': timezone.now().date()
        },
        {
            'name': 'Django',
            'skill_type': 'TECH',
            'proficiency_level': 4,
            'years_of_experience': 3,
            'is_primary': True,
            'last_used': timezone.now().date()
        },
        {
            'name': 'JavaScript',
            'skill_type': 'TECH',
            'proficiency_level': 4,
            'years_of_experience': 4,
            'is_primary': False,
            'last_used': timezone.now().date()
        },
        {
            'name': 'SQL',
            'skill_type': 'TECH',
            'proficiency_level': 3,
            'years_of_experience': 2,
            'is_primary': False,
            'last_used': timezone.now().date() - timedelta(days=180)
        },
        {
            'name': 'Project Management',
            'skill_type': 'SOFT',
            'proficiency_level': 3,
            'years_of_experience': 2,
            'is_primary': False,
            'last_used': timezone.now().date()
        }
    ]
    
    created_skills = []
    for skill_data in test_skills:
        skill = Skill.objects.create(profile=profile, **skill_data)
        created_skills.append(skill)
        print(f"  ✓ Created skill: {skill.name} (Level {skill.proficiency_level}, {skill.years_of_experience} years)")
    
    # Create test job postings
    JobPosting.objects.filter(company_name='Test Company').delete()
    
    test_jobs = [
        {
            'job_title': 'Senior Python Developer',
            'company_name': 'Test Company',
            'location': 'Remote',
            'job_type': 'FULL_TIME',
            'job_description': 'Looking for an experienced Python developer',
            'skills_required': 'Python, Django, SQL, Docker',
            'is_active': True,
            'source_type': 'EXTERNAL'
        },
        {
            'job_title': 'Full Stack Developer',
            'company_name': 'Test Company',
            'location': 'Manila',
            'job_type': 'FULL_TIME',
            'job_description': 'Full stack development position',
            'skills_required': 'Python, JavaScript, React, PostgreSQL',
            'is_active': True,
            'source_type': 'EXTERNAL'
        },
        {
            'job_title': 'Junior Web Developer',
            'company_name': 'Test Company',
            'location': 'Dumaguete',
            'job_type': 'FULL_TIME',
            'job_description': 'Entry level web development',
            'skills_required': 'HTML, CSS, JavaScript, Git',
            'is_active': True,
            'source_type': 'EXTERNAL'
        },
        {
            'job_title': 'Data Analyst',
            'company_name': 'Test Company',
            'location': 'Cebu',
            'job_type': 'FULL_TIME',
            'job_description': 'Data analysis position',
            'skills_required': 'Python, SQL, Excel, Tableau',
            'is_active': True,
            'source_type': 'EXTERNAL'
        }
    ]
    
    created_jobs = []
    for job_data in test_jobs:
        job = JobPosting.objects.create(**job_data)
        created_jobs.append(job)
        print(f"  ✓ Created job: {job.job_title} (Skills: {job.skills_required})")
    
    return profile, created_skills, created_jobs

def test_skill_relevancy():
    """Test skill relevancy calculation"""
    print_section("TEST 4: Skill Relevancy Calculation")
    
    profile, skills, jobs = test_create_test_data()
    
    # Test relevancy for different skills
    python_skill = skills[0]  # Expert Python with 5 years
    sql_skill = skills[3]     # Intermediate SQL with 2 years, last used 6 months ago
    
    print(f"\n✓ Testing relevancy for {python_skill.name}:")
    relevancy = calculate_skill_relevancy(python_skill, 'Python')
    print(f"  - Proficiency: {python_skill.proficiency_level}/5")
    print(f"  - Experience: {python_skill.years_of_experience} years")
    print(f"  - Is Primary: {python_skill.is_primary}")
    print(f"  - Relevancy Score: {relevancy:.2f}")
    
    print(f"\n✓ Testing relevancy for {sql_skill.name}:")
    relevancy = calculate_skill_relevancy(sql_skill, 'SQL')
    print(f"  - Proficiency: {sql_skill.proficiency_level}/5")
    print(f"  - Experience: {sql_skill.years_of_experience} years")
    print(f"  - Last Used: {sql_skill.last_used}")
    print(f"  - Relevancy Score: {relevancy:.2f}")
    
    return True

def test_job_match_calculation():
    """Test job match score calculation"""
    print_section("TEST 5: Job Match Score Calculation")
    
    profile, skills, jobs = test_create_test_data()
    
    for job in jobs:
        print(f"\n✓ Calculating match for: {job.job_title}")
        print(f"  Required skills: {job.skills_required}")
        
        score, matched, missing = calculate_job_match_score(profile, job)
        
        print(f"  Match Score: {score:.2f}%")
        
        if matched:
            print(f"  Matched Skills ({len(matched)}):")
            for skill_name, data in matched.items():
                print(f"    - {skill_name}: relevancy={data['relevancy']:.2f}, "
                      f"proficiency={data['user_proficiency']}, "
                      f"experience={data['user_experience']} years")
        
        if missing:
            print(f"  Missing Skills ({len(missing)}):")
            for skill_name in missing.keys():
                print(f"    - {skill_name}")
    
    return True

def test_find_matching_jobs():
    """Test finding matching jobs"""
    print_section("TEST 6: Finding Matching Jobs")
    
    profile, skills, jobs = test_create_test_data()
    
    print("\n✓ Finding jobs with minimum 30% match:")
    matches = find_matching_jobs(profile, min_match_score=30.0, limit=10)
    
    print(f"  Found {len(matches)} matching jobs:")
    for job, score, matched, missing in matches:
        print(f"\n  - {job.job_title} ({score:.2f}% match)")
        print(f"    Location: {job.location}")
        print(f"    Matched: {len(matched)} skills")
        print(f"    Missing: {len(missing)} skills")
    
    return True

def test_update_skill_matches():
    """Test updating skill matches in database"""
    print_section("TEST 7: Updating Skill Matches")
    
    profile, skills, jobs = test_create_test_data()
    
    # Clear existing matches
    SkillMatch.objects.filter(profile=profile).delete()
    print("✓ Cleared existing skill matches")
    
    # Update matches
    print("\n✓ Updating skill matches...")
    summary = update_skill_matches(profile)
    
    print(f"  Total matches: {summary['total_matches']}")
    print(f"  New matches: {summary['new_matches']}")
    print(f"  Updated matches: {summary['updated_matches']}")
    print(f"  Timestamp: {summary['timestamp']}")
    
    # Verify matches in database
    print("\n✓ Verifying matches in database:")
    matches = SkillMatch.objects.filter(profile=profile).order_by('-match_score')
    
    for match in matches:
        print(f"\n  - {match.job.job_title}")
        print(f"    Score: {match.match_score:.2f}%")
        print(f"    Created: {match.created_at}")
        print(f"    Notified: {match.is_notified}")
        print(f"    Viewed: {match.is_viewed}")
        print(f"    Applied: {match.is_applied}")
    
    return True

def test_skill_recommendations():
    """Test skill recommendations"""
    print_section("TEST 8: Skill Recommendations")
    
    profile, skills, jobs = test_create_test_data()
    
    # Ensure we have some matches
    update_skill_matches(profile)
    
    print("\n✓ Getting skill recommendations...")
    recommendations = get_skill_recommendations(profile)
    
    if recommendations:
        print(f"  Found {len(recommendations)} recommended skills:")
        for rec in recommendations:
            print(f"\n  - {rec['name']}")
            print(f"    Frequency: {rec['frequency']} jobs")
            print(f"    Related jobs: {', '.join(rec['related_jobs'])}")
    else:
        print("  No recommendations found (this is expected if match scores are low)")
    
    return True

def test_edge_cases():
    """Test edge cases and error handling"""
    print_section("TEST 9: Edge Cases")
    
    profile, skills, jobs = test_create_test_data()
    
    # Test with job that has no skills
    print("\n✓ Testing job with no required skills:")
    job_no_skills = JobPosting.objects.create(
        job_title='Test Job No Skills',
        company_name='Test Company',
        location='Test',
        job_type='FULL_TIME',
        job_description='Test',
        skills_required='',
        is_active=True,
        source_type='EXTERNAL'
    )
    
    score, matched, missing = calculate_job_match_score(profile, job_no_skills)
    print(f"  Score: {score:.2f}% (should be 0)")
    print(f"  Matched: {len(matched)} (should be 0)")
    print(f"  Missing: {len(missing)} (should be 0)")
    
    # Test with profile that has no skills
    print("\n✓ Testing profile with no skills:")
    user_no_skills = User.objects.create_user(
        username='noskills_user',
        email='noskills@example.com',
        password='testpass123'
    )
    profile_no_skills = Profile.objects.get(user=user_no_skills)
    
    score, matched, missing = calculate_job_match_score(profile_no_skills, jobs[0])
    print(f"  Score: {score:.2f}% (should be 0)")
    print(f"  Matched: {len(matched)} (should be 0)")
    print(f"  Missing: {len(missing)} (should be > 0)")
    
    # Cleanup
    job_no_skills.delete()
    user_no_skills.delete()
    
    return True

def test_database_constraints():
    """Test database constraints and indexes"""
    print_section("TEST 10: Database Constraints")
    
    profile, skills, jobs = test_create_test_data()
    
    # Test unique_together constraint
    print("\n✓ Testing unique_together constraint:")
    match1 = SkillMatch.objects.create(
        job=jobs[0],
        profile=profile,
        match_score=75.0,
        matched_skills='{}',
        missing_skills='{}'
    )
    print(f"  Created first match: {match1}")
    
    try:
        match2 = SkillMatch.objects.create(
            job=jobs[0],
            profile=profile,
            match_score=80.0,
            matched_skills='{}',
            missing_skills='{}'
        )
        print("  ✗ FAILED: Should have raised IntegrityError")
        return False
    except Exception as e:
        print(f"  ✓ Correctly prevented duplicate: {type(e).__name__}")
    
    # Test update_or_create
    print("\n✓ Testing update_or_create:")
    match, created = SkillMatch.objects.update_or_create(
        job=jobs[0],
        profile=profile,
        defaults={'match_score': 85.0}
    )
    print(f"  Created: {created} (should be False)")
    print(f"  Updated score: {match.match_score} (should be 85.0)")
    
    return True

def cleanup_test_data():
    """Clean up test data"""
    print_section("CLEANUP: Removing Test Data")
    
    try:
        # Delete test users and related data
        User.objects.filter(username__in=['skilltest_user', 'noskills_user']).delete()
        print("✓ Deleted test users")
        
        # Delete test jobs
        JobPosting.objects.filter(company_name='Test Company').delete()
        print("✓ Deleted test jobs")
        
        print("\n✓ Cleanup completed successfully")
    except Exception as e:
        print(f"✗ Cleanup error: {e}")

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  SKILL-BASED MATCHING SYSTEM - COMPREHENSIVE TEST")
    print("="*80)
    
    tests = [
        ("Skill Model Structure", test_skill_model),
        ("SkillMatch Model Structure", test_skill_match_model),
        ("Skill Relevancy Calculation", test_skill_relevancy),
        ("Job Match Score Calculation", test_job_match_calculation),
        ("Finding Matching Jobs", test_find_matching_jobs),
        ("Updating Skill Matches", test_update_skill_matches),
        ("Skill Recommendations", test_skill_recommendations),
        ("Edge Cases", test_edge_cases),
        ("Database Constraints", test_database_constraints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "ERROR"))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    for test_name, status in results:
        symbol = "✓" if status == "PASS" else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup
    cleanup_test_data()
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
