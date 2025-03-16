from typing import List, Dict, Tuple
from django.db.models import Q
from django.utils import timezone
from accounts.models import Profile, Skill
from .models import Mentor, MentorshipRequest

def calculate_expertise_match(mentor_expertise: str, mentee_skills_seeking: str) -> float:
    """
    Calculate match score between mentor's expertise and mentee's desired skills.
    Returns a score between 0 and 1.
    """
    mentor_areas = set(area.strip().lower() for area in mentor_expertise.split(','))
    mentee_areas = set(area.strip().lower() for area in mentee_skills_seeking.split(','))
    
    if not mentor_areas or not mentee_areas:
        return 0.0
    
    matching_areas = mentor_areas.intersection(mentee_areas)
    return len(matching_areas) / len(mentee_areas)

def calculate_availability_score(mentor: Mentor) -> float:
    """
    Calculate mentor's availability score based on current mentee load and status.
    Returns a score between 0 and 1.
    """
    if not mentor.is_active or mentor.availability_status == 'UNAVAILABLE':
        return 0.0
    
    if mentor.current_mentees >= mentor.max_mentees:
        return 0.0
    
    availability_weights = {
        'AVAILABLE': 1.0,
        'LIMITED': 0.5,
        'UNAVAILABLE': 0.0
    }
    
    base_score = availability_weights.get(mentor.availability_status, 0.0)
    capacity_score = 1 - (mentor.current_mentees / mentor.max_mentees)
    
    return (base_score + capacity_score) / 2

def calculate_experience_score(mentor: Mentor) -> float:
    """
    Calculate mentor's experience score based on mentoring history.
    Returns a score between 0 and 1.
    """
    completed_mentorships = MentorshipRequest.objects.filter(
        mentor=mentor,
        status='COMPLETED'
    ).count()
    
    # Calculate average rating
    rated_mentorships = MentorshipRequest.objects.filter(
        mentor=mentor,
        status='COMPLETED',
        rating__isnull=False
    )
    avg_rating = rated_mentorships.aggregate(models.Avg('rating'))['rating__avg'] or 0
    
    # Normalize scores
    experience_score = min(completed_mentorships / 5, 1.0)  # Cap at 5 mentorships
    rating_score = avg_rating / 5 if avg_rating else 0.5  # Default to 0.5 if no ratings
    
    return (experience_score + rating_score) / 2

def find_matching_mentors(
    mentee_profile: Profile,
    skills_seeking: str,
    limit: int = 10
) -> List[Tuple[Mentor, float]]:
    """
    Find matching mentors based on expertise, availability, and experience.
    Returns a list of (mentor, score) tuples sorted by match score.
    """
    active_mentors = Mentor.objects.filter(is_active=True)
    mentor_scores = []
    
    for mentor in active_mentors:
        # Skip if mentor is already mentoring this mentee
        if MentorshipRequest.objects.filter(
            mentor=mentor,
            mentee=mentee_profile.user,
            status__in=['PENDING', 'APPROVED']
        ).exists():
            continue
        
        # Calculate individual scores
        expertise_score = calculate_expertise_match(mentor.expertise_areas, skills_seeking)
        availability_score = calculate_availability_score(mentor)
        experience_score = calculate_experience_score(mentor)
        
        # Calculate weighted total score
        total_score = (
            expertise_score * 0.5 +  # Expertise is most important
            availability_score * 0.3 +  # Availability is second
            experience_score * 0.2  # Experience is third
        )
        
        if total_score > 0:  # Only include mentors with non-zero scores
            mentor_scores.append((mentor, total_score))
    
    # Sort by score and return top matches
    return sorted(mentor_scores, key=lambda x: x[1], reverse=True)[:limit]

def get_mentor_recommendations(
    mentee_profile: Profile,
    skills_seeking: str = None,
    exclude_pending: bool = True
) -> Dict:
    """
    Get personalized mentor recommendations with detailed matching information.
    """
    if not skills_seeking:
        # If no specific skills are provided, use mentee's skill interests
        mentee_skills = Skill.objects.filter(profile=mentee_profile)
        skills_seeking = ','.join(skill.name for skill in mentee_skills)
    
    matching_mentors = find_matching_mentors(mentee_profile, skills_seeking)
    
    recommendations = {
        'matches': [],
        'total_matches': len(matching_mentors),
        'search_criteria': {
            'skills_seeking': skills_seeking,
            'timestamp': timezone.now()
        }
    }
    
    for mentor, score in matching_mentors:
        match_details = {
            'mentor': mentor,
            'match_score': round(score * 100, 2),  # Convert to percentage
            'expertise_match': calculate_expertise_match(mentor.expertise_areas, skills_seeking),
            'availability': calculate_availability_score(mentor),
            'experience_score': calculate_experience_score(mentor),
            'common_areas': set(mentor.expertise_areas.lower().split(',')) & 
                          set(skills_seeking.lower().split(','))
        }
        recommendations['matches'].append(match_details)
    
    return recommendations 