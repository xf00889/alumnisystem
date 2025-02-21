from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField

class Alumni(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    EMPLOYMENT_STATUS_CHOICES = (
        ('EMPLOYED_FULL', 'Employed Full-Time'),
        ('EMPLOYED_PART', 'Employed Part-Time'),
        ('SELF_EMPLOYED', 'Self-Employed'),
        ('UNEMPLOYED', 'Unemployed'),
        ('STUDENT', 'Further Studies'),
        ('RETIRED', 'Retired'),
        ('INTERN', 'Internship/OJT'),
    )

    COLLEGE_CHOICES = (
        ('CAS', 'College of Arts and Sciences'),
        ('CAFF', 'College of Agriculture, Forestry and Fishery'),
        ('CBA', 'College of Business Administration'),
        ('CCJE', 'College of Criminal Justice Education'),
        ('CEA', 'College of Engineering and Architecture'),
        ('CIT', 'College of Industrial Technology'),
        ('CNPAHS', 'College of Nursing, Pharmacy and Allied Health Sciences'),
        ('CTE', 'College of Teacher Education'),
        ('CTHM', 'College of Tourism and Hospitality Management'),
    )

    CAMPUS_CHOICES = (
        ('MAIN', 'Dumaguete Main Campus'),
        ('NORTH', 'Dumaguete North Campus'),
        ('BAIS1', 'Bais City Campus I'),
        ('BAIS2', 'Bais City Campus II'),
        ('BSC', 'Bayawan-Sta. Catalina Campus'),
        ('SIATON', 'Siaton Campus'),
        ('GUI', 'Guihulngan Campus'),
        ('PAM', 'Pamplona Campus'),
        ('MAB', 'Mabinay Campus'),
    )

    # Basic Information
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    
    # Contact Information
    phone_number = PhoneNumberField(blank=True)
    alternate_email = models.EmailField(blank=True)
    linkedin_profile = models.URLField(blank=True)
    
    # Location Information
    country = CountryField(default='PH')
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    
    # Academic Information
    college = models.CharField(max_length=10, choices=COLLEGE_CHOICES)
    campus = models.CharField(max_length=10, choices=CAMPUS_CHOICES)
    graduation_year = models.IntegerField()
    course = models.CharField(max_length=200)
    major = models.CharField(max_length=200, blank=True)
    honors = models.CharField(max_length=200, blank=True)
    thesis_title = models.CharField(max_length=500, blank=True, null=True)
    
    # Professional Information
    current_company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='UNEMPLOYED'
    )
    industry = models.CharField(max_length=200, blank=True)
    
    # Skills and Interests
    skills = models.TextField(blank=True, help_text="Comma-separated list of skills")
    interests = models.TextField(blank=True, help_text="Comma-separated list of interests")
    
    # Additional Information
    bio = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Alumni"
        ordering = ['-graduation_year', 'user__last_name']
        indexes = [
            models.Index(fields=['graduation_year', 'course']),
            models.Index(fields=['province', 'city']),
            models.Index(fields=['college', 'campus']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.course} ({self.graduation_year})"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def location(self):
        return f"{self.city}, {self.province}, {self.country.name}"

    @property
    def college_display(self):
        return dict(self.COLLEGE_CHOICES).get(self.college, '')

    @property
    def campus_display(self):
        return dict(self.CAMPUS_CHOICES).get(self.campus, '')

class AlumniDocument(models.Model):
    DOCUMENT_TYPES = (
        ('RESUME', 'Resume/CV'),
        ('CERT', 'Certification'),
        ('DIPLOMA', 'Diploma'),
        ('TOR', 'Transcript of Records'),
        ('OTHER', 'Other'),
    )

    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to='alumni_documents/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.alumni.full_name} - {self.title}"

    @property
    def file_extension(self):
        return self.file.name.split('.')[-1].lower()

    @property
    def file_size(self):
        try:
            size_bytes = self.file.size
            # Convert to appropriate unit
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.2f} TB"
        except:
            return "Unknown size"

class CareerPath(models.Model):
    PROMOTION_TYPE_CHOICES = (
        ('PROMOTION', 'Promotion'),
        ('LATERAL', 'Lateral Move'),
        ('NEW_ROLE', 'New Role'),
        ('COMPANY_CHANGE', 'Company Change'),
    )

    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='career_paths')
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPE_CHOICES, blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    skills_gained = models.TextField(blank=True, help_text="Comma-separated list of skills gained in this role")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Career Path'
        verbose_name_plural = 'Career Paths'

    def __str__(self):
        return f"{self.position} at {self.company}"

    def save(self, *args, **kwargs):
        if self.is_current:
            self.end_date = None
            # Set all other career paths for this alumni to not current
            CareerPath.objects.filter(alumni=self.alumni).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

class Achievement(models.Model):
    ACHIEVEMENT_TYPE_CHOICES = (
        ('AWARD', 'Award'),
        ('CERTIFICATION', 'Certification'),
        ('PUBLICATION', 'Publication'),
        ('PROJECT', 'Project'),
        ('RECOGNITION', 'Recognition'),
        ('OTHER', 'Other'),
    )

    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='achievements_list')
    title = models.CharField(max_length=255)
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPE_CHOICES)
    date_achieved = models.DateField()
    description = models.TextField(blank=True)
    issuer = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    attachment = models.FileField(
        upload_to='achievements/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_achieved']
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'

    def __str__(self):
        return self.title
