from django.db import models
from django.utils.text import slugify
from django.core.validators import URLValidator
from django.contrib.auth import get_user_model
from django.db.models import Max
import re

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
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='job_postings')
    source = models.CharField(max_length=50, default='manual', choices=[
        ('manual', 'Manual'), 
        ('indeed', 'Indeed'),
        ('bossjobs', 'BossJobs')
    ])
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default='EXTERNAL')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', help_text="Job industry category")
    external_id = models.CharField(max_length=100, blank=True, null=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    accepts_internal_applications = models.BooleanField(default=False, help_text="Allow applications through the system")
    # Fields to help with job deduplication and search
    search_query = models.CharField(max_length=200, blank=True, null=True, 
                                  help_text="Search query used to find this job")
    search_location = models.CharField(max_length=200, blank=True, null=True,
                                     help_text="Location used to find this job")
    title_normalized = models.CharField(max_length=200, blank=True, null=True,
                                     help_text="Normalized version of job title for deduplication")
    hash_signature = models.CharField(max_length=64, blank=True, null=True, 
                                   help_text="Hash signature based on job content for deduplication")

    class Meta:
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['job_type']),
            models.Index(fields=['posted_date']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['source_type']),
            models.Index(fields=['source']),  # Add index for source
            models.Index(fields=['external_id']),  # Add index for external_id
        ]
        # Only one job with the same external_id per source
        unique_together = [('source', 'external_id')]

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
