from typing import List, Dict, Tuple
import json
from datetime import datetime
from django.db.models import Q
from django.utils import timezone
from accounts.models import Profile, Skill, SkillMatch
from .models import JobPosting

def calculate_skill_relevancy(
    skill: Skill,
    required_skill_name: str,
    max_years_boost: int = 5
) -> float:
    """
    Calculate relevancy score between a user's skill and a required job skill.
    Returns a score between 0 and 1.
    """
    # Base match on skill name
    if skill.name.lower() != required_skill_name.lower():
        return 0.0
    
    # Calculate proficiency match (0-1)
    proficiency_score = skill.proficiency_level / 5  # Normalize to 0-1
    
    # Calculate experience match (0-1)
    years_score = min(skill.years_of_experience / max_years_boost, 1.0)
    
    # Calculate recency score (0-1)
    if skill.last_used:
        days_since_used = (timezone.now().date() - skill.last_used).days
        recency_score = max(1 - (days_since_used / 365), 0)  # Decay over a year
    else:
        recency_score = 0.5  # Default if last_used is not specified
    
    # Weight the components
    weighted_score = (
        proficiency_score * 0.4 +  # Proficiency is most important
        years_score * 0.4 +       # Experience is equally important
        recency_score * 0.2       # Recency is less important
    )
    
    # Boost score if it's a primary skill for the user
    if skill.is_primary:
        weighted_score = min(weighted_score * 1.2, 1.0)
    
    return weighted_score

def calculate_job_match_score(
    profile: Profile,
    job: JobPosting,
    required_skills_only: bool = False
) -> Tuple[float, Dict, Dict]:
    """
    Calculate match score between a user profile and a job posting.
    Returns a tuple of (match_score, matched_skills_dict, missing_skills_dict).
    """
    user_skills = {skill.name.lower(): skill for skill in profile.skills.all()}
    
    # Get required skills from job posting
    if job.skills_required:
        required_skills = [skill.strip() for skill in job.skills_required.split(',') if skill.strip()]
    else:
        required_skills = []
        
    if not required_skills:
        return 0.0, {}, {}
    
    matched_skills = {}
    missing_skills = {}
    total_weight = 0
    match_score = 0
    
    for skill_name in required_skills:
        skill_name = skill_name.lower()
        weight = 1.0  # Default weight
        total_weight += weight
        
        if skill_name in user_skills:
            relevancy = calculate_skill_relevancy(user_skills[skill_name], skill_name)
            if relevancy > 0:
                matched_skills[skill_name] = {
                    'relevancy': relevancy,
                    'weight': weight,
                    'user_proficiency': user_skills[skill_name].proficiency_level,
                    'user_experience': user_skills[skill_name].years_of_experience
                }
                match_score += relevancy * weight
        else:
            missing_skills[skill_name] = {
                'description': f"Required for {job.job_title}"
            }
    
    # Normalize score to 0-100
    final_score = (match_score / total_weight) * 100 if total_weight > 0 else 0
    
    return final_score, matched_skills, missing_skills

def find_matching_jobs(
    profile: Profile,
    min_match_score: float = 50.0,
    limit: int = 20
) -> List[Tuple[JobPosting, float, Dict, Dict]]:
    """
    Find matching jobs for a user profile.
    Returns a list of (job, score, matched_skills, missing_skills) tuples.
    """
    # Get active jobs that haven't been applied to
    active_jobs = JobPosting.objects.filter(
        is_active=True,
        application_deadline__gt=timezone.now() if hasattr(JobPosting, 'application_deadline') else Q()
    ).exclude(
        applications__applicant=profile.user if hasattr(profile, 'user') else Q()
    )
    
    matches = []
    for job in active_jobs:
        score, matched, missing = calculate_job_match_score(profile, job)
        if score >= min_match_score:
            matches.append((job, score, matched, missing))
    
    # Sort by score and return top matches
    return sorted(matches, key=lambda x: x[1], reverse=True)[:limit]

def update_skill_matches(profile: Profile) -> Dict:
    """
    Update skill matches for a user profile.
    Returns a summary of the update operation.
    """
    matching_jobs = find_matching_jobs(profile)
    
    summary = {
        'total_matches': len(matching_jobs),
        'new_matches': 0,
        'updated_matches': 0,
        'timestamp': timezone.now()
    }
    
    for job, score, matched_skills, missing_skills in matching_jobs:
        match, created = SkillMatch.objects.update_or_create(
            job=job,
            profile=profile,
            defaults={
                'match_score': score,
                'matched_skills': json.dumps(matched_skills),
                'missing_skills': json.dumps(missing_skills),
                'is_notified': False
            }
        )
        
        if created:
            summary['new_matches'] += 1
        else:
            summary['updated_matches'] += 1
    
    return summary

def get_skill_recommendations(profile: Profile) -> Dict:
    """
    Get skill recommendations based on job market analysis.
    """
    # Get skills from jobs with high match scores
    matched_jobs = SkillMatch.objects.filter(
        profile=profile,
        match_score__gte=70
    ).select_related('job')
    
    user_skills = set(skill.name.lower() for skill in profile.skills.all())
    recommended_skills = {}
    
    for match in matched_jobs:
        if match.job.skills_required:
            job_skills = [skill.strip().lower() for skill in match.job.skills_required.split(',') if skill.strip()]
            for skill_name in job_skills:
                if skill_name not in user_skills:
                    if skill_name not in recommended_skills:
                        recommended_skills[skill_name] = {
                            'count': 0,
                            'job_titles': set()
                        }
                    recommended_skills[skill_name]['count'] += 1
                    recommended_skills[skill_name]['job_titles'].add(match.job.job_title)
    
    # Sort and format recommendations
    recommendations = []
    for skill_name, data in recommended_skills.items():
        if data['count'] >= 2:  # Only recommend skills that appear multiple times
            recommendations.append({
                'name': skill_name,
                'frequency': data['count'],
                'related_jobs': list(data['job_titles'])[:3]  # Show up to 3 related jobs
            })
    
    return sorted(recommendations, key=lambda x: x['frequency'], reverse=True) 