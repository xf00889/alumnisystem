from django.db import models
from django.conf import settings
from django.utils import timezone
from alumni_directory.models import Alumni
from core.models.contact import Address

class Survey(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_external = models.BooleanField(default=False)
    external_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date


class SurveyQuestion(models.Model):
    QUESTION_TYPES = (
        ('text', 'Text Answer'),
        ('multiple_choice', 'Multiple Choice (Single Answer)'),
        ('checkbox', 'Multiple Choice (Multiple Answers)'),
        ('rating', 'Rating Scale'),
        ('likert', 'Likert Scale'),
        ('date', 'Date'),
        ('time', 'Time'),
        ('file', 'File Upload'),
        ('email', 'Email'),
        ('number', 'Number'),
        ('phone', 'Phone Number'),
        ('url', 'Website URL'),
    )
    
    SCALE_TYPES = (
        ('1-5', '1 to 5'),
        ('1-10', '1 to 10'),
        ('a-f', 'A to F'),
        ('frequency', 'Frequency (Never - Always)'),
        ('agreement', 'Agreement (Strongly Disagree - Strongly Agree)'),
        ('satisfaction', 'Satisfaction (Very Unsatisfied - Very Satisfied)'),
        ('custom', 'Custom Scale'),
    )
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    is_required = models.BooleanField(default=False)
    help_text = models.TextField(blank=True)
    display_order = models.IntegerField()
    scale_type = models.CharField(max_length=20, choices=SCALE_TYPES, blank=True, null=True)
    
    def __str__(self):
        return f"{self.survey.title} - Q{self.display_order + 1}"
    
    class Meta:
        ordering = ['display_order']


class QuestionOption(models.Model):
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=200)
    display_order = models.IntegerField()
    allow_custom = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.question.question_text} - {self.option_text}"
    
    class Meta:
        ordering = ['display_order']


class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='survey_responses')
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.survey.title} - {self.alumni.user.get_full_name()} - {self.submitted_at}"
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['survey', 'alumni']  # Each alumni can only respond once


class ResponseAnswer(models.Model):
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True, null=True)
    rating_value = models.IntegerField(blank=True, null=True)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"Answer to {self.question.question_text}"


class EmploymentRecord(models.Model):
    SALARY_RANGES = (
        ('0-50k', '$0 - $50,000'),
        ('50k-100k', '$50,000 - $100,000'),
        ('100k-150k', '$100,000 - $150,000'),
        ('150k-200k', '$150,000 - $200,000'),
        ('200k+', '$200,000+'),
        ('prefer_not', 'Prefer not to say'),
    )
    
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='employment_records')
    company_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    salary_range = models.CharField(max_length=20, choices=SALARY_RANGES, null=True, blank=True)
    location = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.alumni.user.get_full_name()} - {self.job_title} at {self.company_name}"
    
    class Meta:
        ordering = ['-start_date']


class Achievement(models.Model):
    ACHIEVEMENT_TYPES = (
        ('award', 'Award/Recognition'),
        ('certification', 'Professional Certification'),
        ('publication', 'Publication'),
        ('speaking', 'Speaking Engagement'),
        ('education', 'Educational Achievement'),
        ('other', 'Other Achievement'),
    )
    
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='survey_achievements')
    title = models.CharField(max_length=200)
    description = models.TextField()
    achievement_date = models.DateField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.alumni.user.get_full_name()} - {self.title}"
    
    class Meta:
        ordering = ['-achievement_date']


class Report(models.Model):
    REPORT_TYPES = (
        ('employment', 'Employment Trends'),
        ('geographic', 'Geographic Distribution'),
        ('achievements', 'Alumni Achievements'),
        ('feedback', 'Survey Feedback'),
        ('custom', 'Custom Report'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    parameters = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
