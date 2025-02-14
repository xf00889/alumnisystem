from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    phone_number = PhoneNumberField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, blank=True, help_text=_('Two-letter country code (ISO 3166-1 alpha-2)'))
    postal_code = models.CharField(max_length=20, blank=True)
    linkedin_profile = models.URLField(max_length=255, blank=True)
    facebook_profile = models.URLField(max_length=255, blank=True)
    twitter_profile = models.URLField(max_length=255, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    has_completed_registration = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}'s Profile"

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

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
    skill_type = models.CharField(max_length=5, choices=SKILL_TYPES)
    proficiency_level = models.IntegerField(choices=PROFICIENCY_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_proficiency_level_display()}"

    class Meta:
        verbose_name = _('Skill')
        verbose_name_plural = _('Skills')
        ordering = ['-proficiency_level']

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

    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-uploaded_at']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
