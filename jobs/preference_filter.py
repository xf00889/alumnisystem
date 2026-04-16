"""
Job Preference Filter Service

This module provides filtering and scoring functionality for job postings
based on user preferences. It implements a hybrid filtering approach:
- Hard filters: Exclusionary filters that remove non-matching jobs
- Soft filters: Scoring filters that rank remaining jobs by match quality
"""

import logging
from typing import List, Dict, Optional, Tuple
from django.core.cache import cache
from django.db.models import Q, QuerySet
from django.conf import settings
from .models import JobPosting, JobPreference
from .utils import calculate_job_match_score, parse_salary_range

logger = logging.getLogger(__name__)


class PreferenceFilterService:
    """Service for filtering and scoring jobs based on user preferences"""
    
    def __init__(self, user, preferences=None):
        """
        Initialize the preference filter service.
        
        Args:
            user: The user whose preferences to use
            preferences: Optional JobPreference instance (will be fetched if not provided)
        """
        self.user = user
        self.preferences = preferences or self.get_user_preferences()
        self.cache_key = self._generate_cache_key()
        # Use configured cache timeout from settings, fallback to 300 seconds (5 minutes)
        self.cache_timeout = getattr(settings, 'JOB_PREFERENCES_CACHE_TIMEOUT', 300)
    
    def _generate_cache_key(self) -> str:
        """
        Generate a unique cache key for this user's job preferences.
        
        The cache key is based on the user ID to ensure each user has
        their own cached results. This key is used for storing and
        retrieving filtered job results.
        
        Returns:
            str: Cache key in format "job_preferences_{user_id}"
        """
        return f"job_preferences_{self.user.id}"
    
    def get_user_preferences(self) -> JobPreference:
        """
        Get or create user preferences.
        
        Returns:
            JobPreference instance for the user
        """
        prefs, created = JobPreference.objects.get_or_create(user=self.user)
        return prefs
    
    def should_show_modal(self, session=None) -> bool:
        """
        Determine if preference modal should be shown to the user.
        
        The modal should NOT be shown to:
        - Superusers
        - Staff members
        - HR users
        - Alumni coordinators
        - Users who have already configured preferences
        - Users who were already prompted in this session
        
        Args:
            session: Optional Django session object to check if user was prompted
        
        Returns:
            bool: True if modal should be shown, False otherwise
        """
        # Check if user is admin/staff
        if self.user.is_superuser or self.user.is_staff:
            return False
        
        # Check if user has HR or alumni coordinator role
        if hasattr(self.user, 'profile'):
            if self.user.profile.is_hr or self.user.profile.is_alumni_coordinator:
                return False
        
        # Check if preferences are already configured
        if self.preferences.is_configured:
            return False
        
        # Check if user was already prompted in database
        if self.preferences.was_prompted:
            return False
        
        # Check if user was already prompted in this session
        if session and session.get('preference_modal_prompted', False):
            return False
        
        # Show modal if all checks pass
        return True
    
    def apply_hard_filters(self, queryset: QuerySet) -> QuerySet:
        """
        Apply exclusionary filters to the job queryset.
        
        Hard filters remove jobs that don't meet critical requirements:
        - Job type
        - Remote-only preference
        - Location (when not willing to relocate)
        - Minimum salary
        - Source type
        
        Args:
            queryset: Initial job queryset to filter
            
        Returns:
            Filtered queryset
        """
        # Job Type Filter
        if self.preferences.job_types:
            queryset = queryset.filter(job_type__in=self.preferences.job_types)
        
        # Remote Only Filter
        if self.preferences.remote_only:
            queryset = queryset.filter(job_type='REMOTE')
        
        # Location Filter (if not willing to relocate and not remote only)
        if (self.preferences.location_text and 
            not self.preferences.willing_to_relocate and 
            not self.preferences.remote_only):
            locations = [loc.strip() for loc in self.preferences.location_text.split(',')]
            location_q = Q()
            for loc in locations:
                location_q |= Q(location__icontains=loc)
            queryset = queryset.filter(location_q)
        
        # Minimum Salary Filter
        if self.preferences.minimum_salary:
            queryset = self.filter_by_salary(queryset, self.preferences.minimum_salary)
        
        # Source Type Filter
        if self.preferences.source_type != 'BOTH':
            queryset = queryset.filter(source_type=self.preferences.source_type)
        
        return queryset
    
    def filter_by_salary(self, queryset: QuerySet, min_salary: int) -> QuerySet:
        """
        Filter jobs by minimum salary using salary parsing utility.
        
        This method parses various salary formats and filters jobs where
        the minimum salary meets or exceeds the user's requirement.
        
        Supported formats:
        - "₱20,000 - ₱30,000"
        - "20K-30K"
        - "Above ₱50,000"
        - "₱25,000"
        
        Jobs without salary_range are excluded from results.
        
        Args:
            queryset: Job queryset to filter
            min_salary: Minimum acceptable salary in PHP
            
        Returns:
            Filtered queryset containing only jobs meeting salary requirement
        """
        # Get all jobs with salary information
        jobs_with_salary = queryset.filter(salary_range__isnull=False).exclude(salary_range='')
        
        # Filter jobs by parsing salary and comparing to minimum
        matching_job_ids = []
        
        for job in jobs_with_salary:
            try:
                # Parse the salary range to get minimum value
                parsed_min_salary = parse_salary_range(job.salary_range)
                
                # If parsing succeeded and meets minimum requirement, include it
                if parsed_min_salary is not None and parsed_min_salary >= min_salary:
                    matching_job_ids.append(job.id)
                    
            except Exception as e:
                # Log error but continue processing other jobs
                logger.error(
                    f"Error processing salary for job {job.id} ('{job.salary_range}'): {e}"
                )
                continue
        
        # Return filtered queryset
        if matching_job_ids:
            return queryset.filter(id__in=matching_job_ids)
        else:
            # Return empty queryset if no jobs match
            return queryset.none()
    
    def calculate_match_score(self, job: JobPosting) -> int:
        """
        Calculate soft filter match score (0-100).
        
        Scoring criteria:
        - Industry match: +20 points
        - Experience level match: +15 points
        - Location match (when willing to relocate): +15 points
        
        Score is normalized to 0-100 range.
        
        Args:
            job: JobPosting instance to score
            
        Returns:
            Match score between 0 and 100
        """
        score = 0
        max_score = 0
        
        # Industry Match (+20 points)
        if self.preferences.industries:
            max_score += 20
            if job.category in self.preferences.industries:
                score += 20
        
        # Experience Level Match (+15 points)
        if self.preferences.experience_levels:
            max_score += 15
            if job.experience_level in self.preferences.experience_levels:
                score += 15
        
        # Location Match when willing to relocate (+15 points)
        if self.preferences.location_text and self.preferences.willing_to_relocate:
            max_score += 15
            locations = [loc.strip().lower() for loc in self.preferences.location_text.split(',')]
            if any(loc in job.location.lower() for loc in locations):
                score += 15
        
        # Normalize to 0-100
        if max_score > 0:
            return int((score / max_score) * 100)
        return 0
    
    def get_skill_match_score(self, job: JobPosting) -> int:
        """
        Get skill match score from existing skill matching system.
        
        Integrates with the existing calculate_job_match_score function
        from jobs/utils.py.
        
        Args:
            job: JobPosting instance to score
            
        Returns:
            Skill match score between 0 and 100, or 0 if error occurs
        """
        try:
            if not hasattr(self.user, 'profile'):
                return 0
            
            profile = self.user.profile
            score, _, _ = calculate_job_match_score(profile, job)
            return int(score)
        except Exception as e:
            logger.error(f"Error calculating skill match score: {e}")
            return 0
    
    def get_filtered_jobs(self) -> List[Dict]:
        """
        Get filtered and scored jobs based on user preferences.
        
        Process:
        1. Check cache for existing results
        2. Get active jobs queryset
        3. Apply hard filters
        4. Calculate match scores for remaining jobs
        5. Integrate skill matching scores (if enabled)
        6. Sort by score descending
        7. Cache results
        
        Returns:
            List of dictionaries with 'job' and 'score' keys
        """
        # Check cache first with graceful fallback
        try:
            cached = cache.get(self.cache_key)
            if cached:
                logger.debug(f"Returning cached job matches for user {self.user.id}")
                return cached
        except Exception as e:
            logger.warning(f"Cache unavailable for reading, proceeding without cache: {e}")
        
        # Start with active jobs
        jobs = JobPosting.objects.filter(is_active=True)
        
        # Apply hard filters
        jobs = self.apply_hard_filters(jobs)
        
        # Calculate match scores
        job_matches = []
        for job in jobs:
            # Calculate preference-based score
            preference_score = self.calculate_match_score(job)
            
            # Integrate skill matching if enabled
            if self.preferences.skill_matching_enabled:
                skill_score = self.get_skill_match_score(job)
                
                # Skip jobs below skill match threshold
                if skill_score < self.preferences.skill_match_threshold:
                    continue
                
                # Blend scores (70% preference, 30% skills)
                final_score = int(preference_score * 0.7 + skill_score * 0.3)
            else:
                final_score = preference_score
            
            job_matches.append({
                'job': job,
                'score': final_score
            })
        
        # Sort by score descending
        job_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Cache results with graceful fallback
        try:
            cache.set(self.cache_key, job_matches, self.cache_timeout)
            logger.debug(f"Cached {len(job_matches)} job matches for user {self.user.id}")
        except Exception as e:
            logger.warning(f"Cache unavailable for writing, continuing without cache: {e}")
        
        return job_matches
    
    def invalidate_cache(self):
        """
        Invalidate the cached job matches for this user.
        
        Should be called when:
        - User updates their preferences
        - User updates their skills
        - New jobs are posted
        
        Gracefully handles cache unavailability by logging a warning
        and continuing execution.
        """
        try:
            cache.delete(self.cache_key)
            logger.debug(f"Invalidated cache for user {self.user.id}")
        except Exception as e:
            logger.warning(f"Cache unavailable for deletion, continuing without cache invalidation: {e}")
