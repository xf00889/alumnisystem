from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from core.models.contact import Address, ContactInfo

User = get_user_model()

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]

    EMPLOYMENT_STATUS_CHOICES = [
        ('EMPLOYED_FULL', 'Employed Full-Time'),
        ('EMPLOYED_PART', 'Employed Part-Time'),
        ('SELF_EMPLOYED', 'Self-Employed'),
        ('UNEMPLOYED', 'Unemployed'),
        ('STUDENT', 'Further Studies'),
        ('RETIRED', 'Retired'),
        ('INTERN', 'Internship/OJT'),
    ]

    SALARY_RANGE_CHOICES = [
        ('0-15K', 'Below ₱15,000'),
        ('15K-30K', '₱15,000 - ₱30,000'),
        ('30K-50K', '₱30,000 - ₱50,000'),
        ('50K-80K', '₱50,000 - ₱80,000'),
        ('80K-100K', '₱80,000 - ₱100,000'),
        ('100K+', 'Above ₱100,000'),
        ('PREFER_NOT', 'Prefer not to say'),
    ]

    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    # Professional Information
    current_position = models.CharField(max_length=200, blank=True)
    current_employer = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=200, blank=True)
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='UNEMPLOYED'
    )
    salary_range = models.CharField(
        max_length=20,
        choices=SALARY_RANGE_CHOICES,
        default='PREFER_NOT',
        blank=True
    )

    # Legacy fields - maintained for backward compatibility
    # These will be deprecated in future versions
    phone_number = PhoneNumberField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = CountryField(blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    linkedin_profile = models.URLField(max_length=255, blank=True)
    facebook_profile = models.URLField(max_length=255, blank=True)
    twitter_profile = models.URLField(max_length=255, blank=True)

    # Metadata
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    has_completed_registration = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}'s Profile"

    @property
    def primary_address(self):
        """Get the user's primary address from the normalized model"""
        return self.user.addresses.filter(is_primary=True).first()

    @property
    def primary_phone(self):
        """Get the user's primary phone number from the normalized model"""
        contact = self.user.contact_info.filter(
            contact_type='PHONE',
            is_primary=True
        ).first()
        return contact.contact_value if contact else self.phone_number

    @property
    def primary_email(self):
        """Get the user's primary email from the normalized model"""
        contact = self.user.contact_info.filter(
            contact_type='EMAIL',
            is_primary=True
        ).first()
        return contact.contact_value if contact else self.user.email

    @property
    def social_profiles(self):
        """Get all social media profiles from the normalized model"""
        return self.user.contact_info.filter(
            contact_type__in=['LINKEDIN', 'FACEBOOK', 'TWITTER'],
            is_primary=True
        )

    def save(self, *args, **kwargs):
        # Sync professional information with Alumni model if it exists
        super().save(*args, **kwargs)
        try:
            alumni = self.user.alumni
            alumni.current_company = self.current_employer
            alumni.job_title = self.current_position
            alumni.employment_status = self.employment_status
            alumni.save()
        except:
            pass

class Education(models.Model):
    PROGRAM_CHOICES = [
        ('BSIT', 'Bachelor of Science in Information Technology'),
        ('BSCS', 'Bachelor of Science in Computer Science'),
        ('BSIS', 'Bachelor of Science in Information Systems'),
        ('BSA', 'Bachelor of Science in Accountancy'),
        ('BSBA', 'Bachelor of Science in Business Administration'),
        ('BEED', 'Bachelor of Elementary Education'),
        ('BSED', 'Bachelor of Secondary Education'),
        ('BSN', 'Bachelor of Science in Nursing'),
        ('BSCRIM', 'Bachelor of Science in Criminology'),
        ('BSHRM', 'Bachelor of Science in Hotel and Restaurant Management'),
        ('BSTM', 'Bachelor of Science in Tourism Management'),
        ('BSE', 'Bachelor of Science in Engineering'),
        ('BSP', 'Bachelor of Science in Psychology'),
        ('OTHER', 'Other Program'),
    ]

    SCHOOL_CHOICES = [
        ('NORSU-G', 'NORSU Guihulngan'),
        ('NORSU-BC', 'NORSU Bais City'),
        ('NORSU-MB', 'NORSU Mabinay'),
        ('NORSU-SC', 'NORSU Siaton'),
        ('NORSU-PC', 'NORSU Pamplona'),
        ('NORSU-SCC', 'NORSU Sta. Catalina'),
        ('NORSU-VC', 'NORSU Valencia'),
        ('OTHER', 'Other Campus'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='education')
    program = models.CharField(max_length=10, choices=PROGRAM_CHOICES, null=True, blank=True)
    major = models.CharField(max_length=100, blank=True)
    school = models.CharField(max_length=10, choices=SCHOOL_CHOICES, null=True, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    achievements = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.program and self.school:
            return f"{self.get_program_display()} - {self.get_school_display()} ({self.graduation_year})"
        return "Education Record"

    class Meta:
        verbose_name = _('Education')
        verbose_name_plural = _('Education')
        ordering = ['-graduation_year']

class Experience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experience')
    company = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.position} at {self.company}"

    class Meta:
        verbose_name = _('Experience')
        verbose_name_plural = _('Experience')
        ordering = ['-start_date']

class Skill(models.Model):
    SKILL_TYPES = [
        ('TECH', 'Technical'),
        ('SOFT', 'Soft Skills'),
        ('LANG', 'Language'),
        ('CERT', 'Certification'),
        ('DOMAIN', 'Domain Knowledge'),
        ('TOOL', 'Tools & Software'),
        ('OTHER', 'Other'),
    ]

    PROFICIENCY_LEVELS = [
        (1, 'Beginner'),
        (2, 'Elementary'),
        (3, 'Intermediate'),
        (4, 'Advanced'),
        (5, 'Expert'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    skill_type = models.CharField(max_length=10, choices=SKILL_TYPES)
    proficiency_level = models.IntegerField(choices=PROFICIENCY_LEVELS)
    years_of_experience = models.IntegerField(default=0, help_text="Years of experience with this skill")
    last_used = models.DateField(null=True, blank=True, help_text="When was this skill last used")
    is_primary = models.BooleanField(default=False, help_text="Is this a primary/key skill")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_proficiency_level_display()}"

    class Meta:
        verbose_name = _('Skill')
        verbose_name_plural = _('Skills')
        ordering = ['-proficiency_level', '-years_of_experience']
        indexes = [
            models.Index(fields=['name', 'skill_type']),
            models.Index(fields=['proficiency_level']),
        ]

class SkillMatch(models.Model):
    job = models.ForeignKey('jobs.JobPosting', on_delete=models.CASCADE, related_name='skill_matches')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='job_matches')
    match_score = models.FloatField(help_text="Percentage match score (0-100)")
    matched_skills = models.TextField(help_text="JSON of matched skills and their weights")
    missing_skills = models.TextField(blank=True, help_text="JSON of required skills that are missing")
    created_at = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    is_applied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.profile.user.get_full_name()} - {self.job.job_title} ({self.match_score}%)"

    class Meta:
        verbose_name = _('Skill Match')
        verbose_name_plural = _('Skill Matches')
        ordering = ['-match_score', '-created_at']
        unique_together = ['job', 'profile']
        indexes = [
            models.Index(fields=['match_score']),
            models.Index(fields=['created_at']),
        ]

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('TRANSCRIPT', 'Academic Transcript'),
        ('CERTIFICATE', 'Certificate'),
        ('DIPLOMA', 'Diploma'),
        ('RESUME', 'Resume/CV'),
        ('OTHER', 'Other'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-uploaded_at']

class MentorApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_application')
    expertise_areas = models.TextField(help_text="Comma-separated areas of expertise")
    years_of_experience = models.IntegerField(help_text="Total years of professional experience")
    certifications = models.FileField(upload_to='mentor/certifications/', help_text="PDF of relevant certifications")
    training_documents = models.FileField(upload_to='mentor/training/', help_text="PDF of training documents")
    competency_summary = models.TextField(help_text="Summary of expertise and competencies")
    application_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    review_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Mentor Application - {self.user.get_full_name()}"

    class Meta:
        verbose_name = _('Mentor Application')
        verbose_name_plural = _('Mentor Applications')
        ordering = ['-application_date']

class Mentor(models.Model):
    AVAILABILITY_CHOICES = [
        ('AVAILABLE', 'Available for Mentorship'),
        ('LIMITED', 'Limited Availability'),
        ('UNAVAILABLE', 'Currently Unavailable'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_profile')
    expertise_areas = models.TextField(help_text="Comma-separated areas of expertise")
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='AVAILABLE')
    max_mentees = models.IntegerField(default=3, help_text="Maximum number of mentees to accept")
    current_mentees = models.IntegerField(default=0)
    mentoring_experience = models.TextField(blank=True, help_text="Brief description of mentoring experience")
    expectations = models.TextField(blank=True, help_text="What mentees can expect from the mentorship")
    preferred_contact_method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False, help_text="Whether this mentor has been verified by admins")
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='verified_mentors')
    accepting_mentees = models.BooleanField(default=True, help_text="Whether the mentor is currently accepting new mentees")

    def __str__(self):
        return f"{self.user.get_full_name()}'s Mentor Profile"

    class Meta:
        verbose_name = _('Mentor')
        verbose_name_plural = _('Mentors')

    def save(self, *args, **kwargs):
        if self.current_mentees >= self.max_mentees:
            self.accepting_mentees = False
        super().save(*args, **kwargs)

class MentorshipRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('PAUSED', 'Paused'),
    ]

    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name='mentorship_requests')
    mentee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentorship_requests')
    skills_seeking = models.TextField(help_text="Skills or knowledge areas seeking mentorship in")
    goals = models.TextField(help_text="What do you hope to achieve through this mentorship?")
    message = models.TextField(help_text="Introduction and why you chose this mentor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    expected_end_date = models.DateField(null=True, blank=True, help_text="Target date for completing the mentorship")
    timeline_milestones = models.TextField(blank=True, help_text="Key milestones and timeline for the mentorship")
    progress_percentage = models.IntegerField(default=0, help_text="Overall progress percentage (0-100)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    feedback = models.TextField(blank=True, help_text="Feedback after mentorship completion")
    rating = models.IntegerField(null=True, blank=True, help_text="Rating out of 5")

    def __str__(self):
        return f"Mentorship Request: {self.mentee.get_full_name()} -> {self.mentor.user.get_full_name()}"

    class Meta:
        verbose_name = _('Mentorship Request')
        verbose_name_plural = _('Mentorship Requests')
        ordering = ['-created_at']
        unique_together = ['mentor', 'mentee', 'status']

    def save(self, *args, **kwargs):
        # Update mentor's current_mentees count when request is approved
        if self.status == 'APPROVED' and self._state.adding:
            self.mentor.current_mentees += 1
            self.mentor.save()
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
