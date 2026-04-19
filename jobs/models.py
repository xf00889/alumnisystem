from django.db import models
from django.utils.text import slugify
from django.core.validators import URLValidator
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone
import re
import json

User = get_user_model()

class RequiredDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('RESUME', 'Resume/CV'),
        ('COVER_LETTER', 'Cover Letter'),
        ('TRANSCRIPT', 'Transcript of Records'),
        ('DIPLOMA', 'Diploma'),
        ('CERTIFICATION', 'Certification'),
        ('PORTFOLIO', 'Portfolio'),
        ('RECOMMENDATION', 'Recommendation Letter'),
        ('GOVERNMENT_ID', 'Government ID'),
        ('OTHER', 'Other Document'),
    ]

    name = models.CharField(max_length=100)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    description = models.TextField(blank=True, help_text="Additional instructions or requirements for this document")
    is_required = models.BooleanField(default=True)
    file_types = models.CharField(max_length=200, default='.pdf,.doc,.docx', 
                                help_text="Comma-separated list of allowed file extensions")
    max_file_size = models.IntegerField(default=5242880,  # 5MB in bytes
                                      help_text="Maximum file size in bytes")
    job = models.ForeignKey('JobPosting', on_delete=models.CASCADE, related_name='required_documents')

    def __str__(self):
        return f"{self.get_document_type_display()} for {self.job.job_title}"

    class Meta:
        ordering = ['document_type']

class JobPosting(models.Model):
    JOB_TYPE_CHOICES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('REMOTE', 'Remote'),
        ('INTERNSHIP', 'Internship'),
    ]
    
    SOURCE_TYPE_CHOICES = [
        ('INTERNAL', 'NORSU Internal'),
        ('EXTERNAL', 'External Organization'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('ENTRY', 'Entry Level'),
        ('MID', 'Mid Level'),
        ('SENIOR', 'Senior Level'),
        ('EXECUTIVE', 'Executive Level'),
    ]

    CATEGORY_CHOICES = [
        ('technology', 'Technology'),
        ('finance', 'Finance & Accounting'),
        ('healthcare', 'Healthcare & Medical'),
        ('education', 'Education & Training'),
        ('sales_marketing', 'Sales & Marketing'),
        ('hospitality', 'Hospitality & Tourism'),
        ('manufacturing', 'Manufacturing & Production'),
        ('administrative', 'Administrative & Clerical'),
        ('construction', 'Construction & Engineering'),
        ('creative', 'Creative & Design'),
        ('other', 'Other')
    ]


    job_title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='FULL_TIME')
    job_description = models.TextField()
    requirements = models.TextField(blank=True, help_text="List the job requirements and qualifications")
    responsibilities = models.TextField(blank=True, help_text="List the key job responsibilities")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='ENTRY')
    skills_required = models.TextField(blank=True, help_text="List required skills (comma-separated)")
    education_requirements = models.TextField(blank=True, help_text="Specify education requirements")
    benefits = models.TextField(blank=True, help_text="List job benefits and perks")
    application_link = models.URLField(max_length=500, validators=[URLValidator()], blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    posted_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='job_postings')
    source = models.CharField(max_length=50, default='manual', choices=[
        ('manual', 'Manual'),
        ('bossjob', 'BossJob.ph'),
        ('jobstreet', 'JobStreet Philippines'),
        ('indeed', 'Indeed Philippines'),
        ('linkedin', 'LinkedIn'),
        ('kalibrr', 'Kalibrr'),
        ('philjobnet', 'PhilJobNet (DOLE)'),
        ('onlinejobs', 'OnlineJobs.ph'),
        ('jora', 'Jora Philippines'),
        ('mynimo', 'Mynimo'),
        ('workabroad', 'WorkAbroad.ph'),
        ('other', 'Other'),
    ])
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default='EXTERNAL')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', help_text="Job industry category")
    accepts_internal_applications = models.BooleanField(default=False, help_text="Allow applications through the system")

    class Meta:
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['job_type']),
            models.Index(fields=['posted_date']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['source_type']),
            models.Index(fields=['source']),  # Add index for source
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.job_title}-{self.company_name}")
            self.slug = base_slug
            n = 0
            while JobPosting.objects.filter(slug=self.slug).exists():
                n += 1
                # Remove any existing numeric suffix
                self.slug = re.sub(r'-\d+$', '', base_slug)
                # Add new numeric suffix
                self.slug = f"{self.slug}-{n}"
                
        # Automatically set accepts_internal_applications for NORSU internal jobs
        if self.source_type == 'INTERNAL':
            self.accepts_internal_applications = True
            
        # Generate normalized title for deduplication
        if self.job_title:
            # Remove special characters, lowercase, and normalize whitespace
            normalized = re.sub(r'[^\w\s]', '', self.job_title.lower())
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            self.title_normalized = normalized
            
        # Generate hash signature for content-based deduplication
        import hashlib
        content = f"{self.job_title}|{self.company_name}|{self.location}|{self.job_type}"
        self.hash_signature = hashlib.sha256(content.encode()).hexdigest()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEWED', 'Interviewed'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='job_applications/resumes/')
    additional_documents = models.FileField(upload_to='job_applications/documents/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-application_date']
        unique_together = ['job', 'applicant']

    def __str__(self):
        return f"{self.applicant.get_full_name()} - {self.job.job_title}"


class ScrapedJob(models.Model):
    """Model to store scraped job data as JSON"""
    
    SOURCE_CHOICES = [
        ('BOSSJOB', 'BossJob.ph'),
        ('JOBSTREET', 'JobStreet Philippines'),
        ('LINKEDIN', 'LinkedIn'),
        ('INDEED', 'Indeed Philippines'),
        ('KALIBRR', 'Kalibrr'),
        ('PHILJOBNET', 'PhilJobNet (DOLE)'),
        ('ONLINEJOBS', 'OnlineJobs.ph'),
        ('JORA', 'Jora Philippines'),
        ('MYNIMO', 'Mynimo'),
        ('WORKABROAD', 'WorkAbroad.ph'),
        ('OTHER', 'Other'),
    ]
    
    search_keyword = models.CharField(max_length=200, help_text="The keyword used for scraping")
    search_location = models.CharField(max_length=200, help_text="The location used for scraping")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='BOSSJOB')
    scraped_data = models.JSONField(help_text="Complete scraped job data as JSON")
    total_found = models.IntegerField(default=0, help_text="Total number of jobs found in scraping")
    scraped_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scraped_jobs')
    scraped_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['search_keyword']),
            models.Index(fields=['search_location']),
            models.Index(fields=['source']),
            models.Index(fields=['scraped_at']),
        ]
    
    def __str__(self):
        return f"Scraped jobs for '{self.search_keyword}' in '{self.search_location}' from {self.get_source_display()}"
    
    @property
    def jobs_data(self):
        """Return the jobs list from scraped_data"""
        if isinstance(self.scraped_data, dict):
            return self.scraped_data.get('jobs', [])
        return []
    
    @property
    def jobs_count(self):
        """Return the number of jobs in the scraped data"""
        return len(self.jobs_data)
    
    def get_job_by_index(self, index):
        """Get a specific job by index"""
        jobs = self.jobs_data
        if 0 <= index < len(jobs):
            return jobs[index]
        return None


class JobPreference(models.Model):
    """Stores user job filtering preferences"""
    
    SOURCE_TYPE_CHOICES = [
        ('INTERNAL', 'NORSU Internal'),
        ('EXTERNAL', 'External'),
        ('BOTH', 'Both'),
    ]
    
    # Relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='job_preferences',
        help_text="User who owns these preferences"
    )
    
    # Configuration Status
    is_configured = models.BooleanField(
        default=False,
        help_text="Whether user has completed preference setup"
    )
    was_prompted = models.BooleanField(
        default=False,
        help_text="Whether user was shown the modal"
    )
    
    # Hard Filters (Exclusionary)
    job_types = models.JSONField(
        default=list,
        blank=True,
        help_text="Selected job types (FULL_TIME, PART_TIME, etc.)"
    )
    location_text = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated preferred locations"
    )
    remote_only = models.BooleanField(
        default=False,
        help_text="Only show remote jobs"
    )
    willing_to_relocate = models.BooleanField(
        default=False,
        help_text="Willing to relocate for opportunities"
    )
    minimum_salary = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum acceptable salary in PHP"
    )
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        default='BOTH',
        help_text="Job source preference"
    )
    
    # Soft Filters (Scoring)
    industries = models.JSONField(
        default=list,
        blank=True,
        help_text="Preferred industries/categories"
    )
    experience_levels = models.JSONField(
        default=list,
        blank=True,
        help_text="Preferred experience levels"
    )
    
    # Skill Matching Integration
    skill_matching_enabled = models.BooleanField(
        default=False,
        help_text="Enable skill-based filtering"
    )
    skill_match_threshold = models.IntegerField(
        default=50,
        help_text="Minimum skill match percentage (0-100)"
    )
    
    # Analytics
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    first_configured_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when preferences were first configured"
    )
    modification_count = models.IntegerField(
        default=0,
        help_text="Number of times preferences have been modified"
    )
    
    class Meta:
        verbose_name = 'Job Preference'
        verbose_name_plural = 'Job Preferences'
        indexes = [
            models.Index(fields=['is_configured']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"Job Preferences for {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Track first configuration
        if self.is_configured and not self.first_configured_at:
            self.first_configured_at = timezone.now()
        
        # Increment modification count (only for updates, not creation)
        if self.pk:
            self.modification_count += 1
        
        super().save(*args, **kwargs)
        
        # Invalidate cache after saving preferences
        self.invalidate_cache()
    
    def invalidate_cache(self):
        """
        Invalidate the cached job matches for this user.
        
        This method is called automatically after saving preferences
        to ensure users see updated results based on their new preferences.
        """
        from django.core.cache import cache
        import logging
        
        logger = logging.getLogger(__name__)
        cache_key = f"job_preferences_{self.user.id}"
        
        try:
            cache.delete(cache_key)
            logger.debug(f"Invalidated cache for user {self.user.id}")
        except Exception as e:
            logger.error(f"Error invalidating cache for user {self.user.id}: {e}")


class UserJobAIScore(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_ai_scores')
    job = models.ForeignKey('JobPosting', on_delete=models.CASCADE, related_name='user_ai_scores')

    score = models.IntegerField(null=True, blank=True, help_text='AI match score (0-100)')
    reason = models.TextField(blank=True)
    strengths_json = models.JSONField(default=list, blank=True)
    gaps_json = models.JSONField(default=list, blank=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)

    profile_version = models.BigIntegerField(default=0)
    computed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Job AI Score'
        verbose_name_plural = 'User Job AI Scores'
        unique_together = ['user', 'job']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'score']),
            models.Index(fields=['computed_at']),
        ]

    def __str__(self):
        score_label = self.score if self.score is not None else 'N/A'
        return f"AI Score: user={self.user_id}, job={self.job_id}, score={score_label}"
