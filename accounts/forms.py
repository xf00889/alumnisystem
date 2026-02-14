from django import forms
from django.forms import inlineformset_factory
from .models import (
    Profile, Education, Experience, Skill, Document,
    MentorApplication, Mentor, EmailVerification
)
from django.contrib.auth.models import User
from alumni_directory.models import Alumni
import datetime
from django_countries.fields import CountryField
from django_countries import countries
from allauth.account.forms import SignupForm, ResetPasswordForm, LoginForm
from .security import PasswordValidator, RateLimiter, SecurityAuditLogger
from .validators import UniqueFieldValidator
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from core.recaptcha_fields import DatabaseReCaptchaField
from core.recaptcha_widgets import DatabaseReCaptchaV3
from core.recaptcha_utils import is_recaptcha_enabled

class CustomLoginForm(LoginForm):
    """Custom login form with reCAPTCHA protection"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only add reCAPTCHA if it's properly configured in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    verification_code = forms.CharField(
        max_length=6,
        required=False,  # Make it optional since we handle verification on server side
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter verification code',
            'maxlength': '6',
            'pattern': '[0-9]{6}'
        }),
        help_text="Enter the 6-digit code sent to your email"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make password fields required for validation
        self.fields['password1'].required = True
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )
        self.fields['password2'].required = True

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            errors = PasswordValidator.validate_password_strength(password1)
            if errors:
                raise forms.ValidationError(errors)
        return password1

    def clean_verification_code(self):
        verification_code = self.cleaned_data.get('verification_code')
        email = self.cleaned_data.get('email')
        
        if verification_code and email:
            from .security import SecurityCodeManager
            is_valid, message = SecurityCodeManager.verify_code(email, verification_code, 'signup')
            if not is_valid:
                raise forms.ValidationError(message)
        
        return verification_code

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check rate limiting
            if RateLimiter.is_rate_limited(email, 'signup_attempt'):
                raise forms.ValidationError("Too many signup attempts. Please try again later.")
            
            # Normalize email to lowercase
            email = UniqueFieldValidator.normalize_email(email)
            
            # Check if email already exists (case-insensitive)
            if UniqueFieldValidator.is_email_taken(email):
                raise forms.ValidationError("An account with this email already exists.")
        
        return email

    def clean_username(self):
        """Validate username uniqueness (case-insensitive)."""
        username = self.cleaned_data.get('username')
        if username:
            # Check if username already exists (case-insensitive)
            if UniqueFieldValidator.is_username_taken(username):
                raise forms.ValidationError("This username is already taken.")
        
        return username

    def save(self, request):
        # Create user manually instead of using allauth's save method
        # to avoid allauth's built-in redirect behavior
        from django.contrib.auth import get_user_model
        from django.db import IntegrityError
        import logging
        logger = logging.getLogger(__name__)
        
        User = get_user_model()
        
        # Normalize email to lowercase before saving
        normalized_email = UniqueFieldValidator.normalize_email(self.cleaned_data['email'])
        
        try:
            user = User.objects.create_user(
                username=normalized_email,  # Use normalized email as username
                email=normalized_email,
                password=self.cleaned_data['password1'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                is_active=False  # Keep user inactive until email verification
            )
        except IntegrityError as e:
            # Log the database constraint violation for monitoring
            logger.error(
                f"Database constraint violation during user creation: email={normalized_email}",
                extra={
                    'email': normalized_email,
                    'error_type': 'IntegrityError',
                    'error_message': str(e),
                    'ip_address': self.get_client_ip(request),
                    'action': 'user_creation_failed'
                },
                exc_info=True
            )
            # Raise a user-friendly validation error
            raise forms.ValidationError(
                "Unable to create account. Please try again or use a different email/username."
            )
        
        # Create profile if it doesn't exist
        Profile.objects.get_or_create(user=user)
        
        # Generate OTP
        otp = get_random_string(length=6, allowed_chars='0123456789')
        
        # Create email verification record
        EmailVerification.objects.create(user=user, otp=otp)
        
        # Send verification email
        try:
            from core.email_utils import send_email_with_provider
            from .email_utils import render_verification_email
            
            # Render HTML email template
            html_message = render_verification_email(user, otp)
            
            send_email_with_provider(
                subject='Verify your email address - NORSU Alumni System',
                message=f'''
Hello {user.first_name},

Welcome to the NORSU Alumni System!

Your verification code is: {otp}

This code will expire in 10 minutes. Please enter this code on the verification page to activate your account.

If you didn't create an account with us, please ignore this email.

Best regards,
NORSU Alumni System Team
                ''',
                html_message=html_message,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Log email sending error but don't fail the signup
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        
        # Log account creation
        SecurityAuditLogger.log_account_creation(user.email, self.get_client_ip(request))
        
        # Store user ID in session for redirect after signup
        request.session['pending_verification_user_id'] = user.id
        
        return user

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class CustomPasswordResetForm(ResetPasswordForm):
    """Enhanced password reset form with security features"""
    
    verification_code = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter verification code',
            'maxlength': '6',
            'pattern': '[0-9]{6}'
        }),
        help_text="Enter the 6-digit code sent to your email"
    )
    
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        help_text="Password must be at least 8 characters with uppercase, lowercase, number, and special character."
    )
    
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            errors = PasswordValidator.validate_password_strength(password1)
            if errors:
                raise forms.ValidationError(errors)
            
            # Check password history if user exists
            if self.user:
                if not PasswordValidator.check_password_history(self.user, password1):
                    raise forms.ValidationError("You cannot reuse a recently used password.")
        
        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        verification_code = cleaned_data.get('verification_code')
        email = cleaned_data.get('email')

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords don't match.")

        if verification_code and email:
            from .security import SecurityCodeManager
            is_valid, message = SecurityCodeManager.verify_code(email, verification_code, 'password_reset')
            if not is_valid:
                raise forms.ValidationError(message)

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check rate limiting
            if RateLimiter.is_rate_limited(email, 'password_reset_attempt'):
                raise forms.ValidationError("Too many password reset attempts. Please try again later.")
            
            # Check if email exists
            try:
                user = User.objects.get(email=email)
                self.user = user
            except User.DoesNotExist:
                raise forms.ValidationError("No account found with this email address.")
        
        return email

    def save(self, request):
        if self.user:
            # Set new password
            self.user.set_password(self.cleaned_data['new_password1'])
            self.user.save()
            
            # Log password reset
            SecurityAuditLogger.log_event(
                'password_reset_success',
                user=self.user,
                ip_address=self.get_client_ip(request)
            )
            
            return self.user
        return None

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PostRegistrationForm(forms.Form):
    # Import college choices from Alumni model
    from alumni_directory.models import Alumni

    COLLEGE_CHOICES = [
        ('', '-- Select your college --'),
    ] + list(Alumni.COLLEGE_CHOICES)

    # Organize courses by college for cascading dropdown functionality
    COURSES_BY_COLLEGE = {
        'CAS': [  # College of Arts and Sciences
            ('BSIT', 'BS in Information Technology'),
            ('BSCS', 'BS in Computer Science'),
            ('BSP', 'BS in Psychology'),
            ('BSM', 'BS in Mathematics'),
            ('BSPHY', 'BS in Physics'),
            ('BSBIO', 'BS in Biology'),
        ],
        'CBA': [  # College of Business Administration
            ('BSA', 'BS in Accountancy'),
            ('BSBA-FM', 'BSBA in Financial Management'),
            ('BSBA-MM', 'BSBA in Marketing Management'),
            ('BSBA-HRM', 'BSBA in Human Resource Management'),
        ],
        'CTE': [  # College of Teacher Education
            ('BEED', 'Bachelor of Elementary Education'),
            ('BSED-ENG', 'BS in Education - English'),
            ('BSED-MATH', 'BS in Education - Mathematics'),
            ('BSED-SCI', 'BS in Education - Science'),
            ('BSED-SS', 'BS in Education - Social Studies'),
        ],
        'CNPAHS': [  # College of Nursing, Pharmacy and Allied Health Sciences
            ('BSN', 'BS in Nursing'),
            ('BSP', 'BS in Pharmacy'),
            ('BSMT', 'BS in Medical Technology'),
        ],
        'CCJE': [  # College of Criminal Justice Education
            ('BSCRIM', 'BS in Criminology'),
        ],
        'CTHM': [  # College of Tourism and Hospitality Management
            ('BSHRM', 'BS in Hotel and Restaurant Management'),
            ('BSTM', 'BS in Tourism Management'),
        ],
        'CEA': [  # College of Engineering and Architecture
            ('BSCE', 'BS in Civil Engineering'),
            ('BSEE', 'BS in Electrical Engineering'),
            ('BSME', 'BS in Mechanical Engineering'),
            ('BSARCH', 'BS in Architecture'),
        ],
        'CAFF': [  # College of Agriculture, Forestry and Fishery
            ('BSA-AGRI', 'BS in Agriculture'),
            ('BSF', 'BS in Forestry'),
            ('BSFT', 'BS in Fisheries Technology'),
        ],
        'CIT': [  # College of Industrial Technology
            ('BSIT-AT', 'BS in Industrial Technology - Automotive'),
            ('BSIT-ET', 'BS in Industrial Technology - Electronics'),
            ('BSIT-FPSM', 'BS in Industrial Technology - Food Processing'),
        ],
        'COL': [  # College of Law
            ('JD', 'Juris Doctor'),
            ('LLB', 'Bachelor of Laws'),
        ],
    }

    # Default course choices (empty until college is selected)
    PROGRAM_CHOICES = [
        ('', '-- Select your college first --'),
    ]

    # Generate all program choices for validation purposes
    ALL_PROGRAM_CHOICES = [('', '-- Select your program --')]
    for college_code, courses in COURSES_BY_COLLEGE.items():
        ALL_PROGRAM_CHOICES.extend(courses)
    ALL_PROGRAM_CHOICES.append(('OTHER', 'Other Program'))

    # Generate course to college mapping from the organized structure
    COURSE_COLLEGE_MAPPING = {}
    for college_code, courses in COURSES_BY_COLLEGE.items():
        for course_code, course_name in courses:
            COURSE_COLLEGE_MAPPING[course_code] = college_code

    SCHOOL_CHOICES = [
        ('', '-- Select your campus --'),
        ('NORSU-MAIN', 'Main Campus I & II (Dumaguete)'),
        ('NORSU-BAIS', 'Bais Campus I & II'),
        ('NORSU-GUI', 'Guihulngan Campus'),
        ('NORSU-MAB', 'Mabinay Campus'),
        ('NORSU-BSC', 'Bayawan-Sta. Catalina Campus'),
        ('NORSU-SIA', 'Siaton Campus'),
        ('NORSU-PAM', 'Pamplona Campus'),
        ('OTHER', 'Other Campus'),
    ]

    GENDER_CHOICES = [
        ('', '-- Select your gender --'),
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        help_text="Enter your first name as it appears on your diploma"
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        help_text="Enter your last name as it appears on your diploma"
    )
    graduation_year = forms.IntegerField(
        required=True,
        min_value=1970,
        max_value=datetime.datetime.now().year,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'YYYY',
            'min': 1970,
            'max': datetime.datetime.now().year
        }),
        help_text="Year you graduated",
        label="Year"
    )
    college = forms.ChoiceField(
        choices=COLLEGE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select your college first",
        label="College"
    )
    course_graduated = forms.ChoiceField(
        choices=ALL_PROGRAM_CHOICES,  # Use all choices for validation
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'disabled': 'disabled',
        }),
        help_text="Select your college first to see available programs",
        label="Course Graduated"
    )
    present_occupation = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Software Engineer, Teacher, Nurse'
        }),
        help_text="Your current job title or position"
    )
    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Accenture Philippines, DepEd, Provincial Hospital'
        }),
        help_text="The name of the company or organization you currently work for"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially set course choices to be empty (will be populated by JavaScript)
        # But keep all choices available for validation
        if not self.data:  # Only on initial form load, not on form submission
            self.fields['course_graduated'].widget.choices = [
                ('', '-- Select your college first --')
            ]

    def clean_graduation_year(self):
        year = self.cleaned_data['graduation_year']
        current_year = datetime.datetime.now().year
        if year < 1970 or year > current_year:
            raise forms.ValidationError(f"Please enter a year between 1970 and {current_year}")
        return year

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course_graduated')
        college = cleaned_data.get('college')

        # Validate that both college and course are selected
        if not college:
            raise forms.ValidationError("Please select your college.")

        if not course:
            raise forms.ValidationError("Please select your course/program.")

        # Validate course-college mapping for non-OTHER courses
        if course and college and course != 'OTHER':
            expected_college = self.COURSE_COLLEGE_MAPPING.get(course)
            if expected_college and college != expected_college:
                # Get college display name for better error message
                from alumni_directory.models import Alumni
                college_dict = dict(Alumni.COLLEGE_CHOICES)
                expected_college_name = college_dict.get(expected_college, expected_college)
                selected_college_name = college_dict.get(college, college)

                raise forms.ValidationError(
                    f"Invalid combination: The course '{course}' does not belong to {selected_college_name}. "
                    f"This course belongs to {expected_college_name}. "
                    f"Please select the correct college first, then choose your course from the available options."
                )

        # Validate that the course is available for the selected college
        if course and college and course != 'OTHER':
            available_courses = [course_code for course_code, _ in self.COURSES_BY_COLLEGE.get(college, [])]
            if course not in available_courses:
                from alumni_directory.models import Alumni
                college_dict = dict(Alumni.COLLEGE_CHOICES)
                college_name = college_dict.get(college, college)
                raise forms.ValidationError(
                    f"The course '{course}' is not available in {college_name}. "
                    f"Please select a different course or choose 'Other Program'."
                )

        return cleaned_data

    @classmethod
    def get_courses_for_college(cls, college_code):
        """
        Get course choices for a specific college.
        Useful for AJAX requests or dynamic form population.
        """
        if not college_code:
            return [('', '-- Select your college first --')]

        courses = cls.COURSES_BY_COLLEGE.get(college_code, [])
        choices = [('', '-- Select your program --')]
        choices.extend(courses)
        choices.append(('OTHER', 'Other Program'))
        return choices

    def save(self, user):
        # Update user's first and last name
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # Create or update primary education record
        Education.objects.update_or_create(
            profile=user.profile,
            is_primary=True,
            defaults={
                'program': self.cleaned_data['course_graduated'],
                'graduation_year': self.cleaned_data['graduation_year'],
            }
        )

        # Update user's profile with employment information
        profile = user.profile
        profile.current_position = self.cleaned_data['present_occupation']
        profile.current_employer = self.cleaned_data['company_name']
        profile.has_completed_registration = True
        profile.save()

        # Create current employment experience
        import datetime
        current_exp = Experience.objects.create(
            profile=profile,
            position=self.cleaned_data['present_occupation'],
            company=self.cleaned_data['company_name'],
            start_date=datetime.date.today(),
            is_current=True,
            career_significance='REGULAR'
        )

        # Create or update Alumni record
        # Auto-determine college if not explicitly selected and course is mapped
        college = self.cleaned_data['college']
        course = self.cleaned_data['course_graduated']
        if not college and course in self.COURSE_COLLEGE_MAPPING:
            college = self.COURSE_COLLEGE_MAPPING[course]

        Alumni.objects.update_or_create(
            user=user,
            defaults={
                'graduation_year': self.cleaned_data['graduation_year'],
                'course': self.cleaned_data['course_graduated'],
                'college': college,
                'current_company': self.cleaned_data['company_name'],
                'job_title': self.cleaned_data['present_occupation'],
                'employment_status': 'EMPLOYED_FULL'  # Assuming full-time employment
            }
        )

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        help_text="Enter your first name"
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        help_text="Enter your last name"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        help_text="Upload a profile picture (JPG, PNG, GIF). Max size: 5MB"
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False,
        help_text="Tell us about yourself"
    )
    country = forms.ChoiceField(
        choices=[('', 'Select Country')] + list(countries),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select your country (optional)"
    )
    
    def clean_country(self):
        country = self.cleaned_data.get('country')
        if country and country not in [code for code, name in countries]:
            raise forms.ValidationError("Please select a valid country.")
        return country
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Convert PhoneNumber object to string if needed
            if hasattr(phone_number, 'as_e164'):
                phone_number = phone_number.as_e164
            elif hasattr(phone_number, 'as_national'):
                phone_number = phone_number.as_national
            elif hasattr(phone_number, 'as_international'):
                phone_number = phone_number.as_international
            else:
                phone_number = str(phone_number)
            
            # Basic phone number validation - allow various formats
            import re
            # Remove all non-digit characters except + at the beginning
            cleaned_phone = re.sub(r'[^\d+]', '', phone_number)
            if len(cleaned_phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone_number

    class Meta:
        model = Profile
        fields = [
            'avatar',
            'bio',
            'birth_date',
            'gender',
            'phone_number',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'linkedin_profile',
            'facebook_profile',
            'twitter_profile',
            'current_position',
            'current_employer',
            'industry',
            'employment_status',
            'salary_range',
            'is_public'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+639519021544', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g. 123 Rizal Street, Barangay Poblacion', 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g. Bayawan City', 'class': 'form-control'}),
            'state': forms.TextInput(attrs={'placeholder': 'e.g. Negros Oriental', 'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'e.g. 6221', 'class': 'form-control'}),
            'linkedin_profile': forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/yourprofile', 'class': 'form-control'}),
            'facebook_profile': forms.URLInput(attrs={'placeholder': 'https://facebook.com/yourprofile', 'class': 'form-control'}),
            'twitter_profile': forms.URLInput(attrs={'placeholder': 'https://twitter.com/yourprofile', 'class': 'form-control'}),
            'current_position': forms.TextInput(attrs={'placeholder': 'e.g. Software Engineer', 'class': 'form-control'}),
            'current_employer': forms.TextInput(attrs={'placeholder': 'e.g. Tech Company Inc.', 'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'placeholder': 'e.g. Information Technology', 'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-select'}),
            'salary_range': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'gender': 'Gender',
            'phone_number': 'Phone Number',
            'address': 'Address',
            'city': 'City',
            'state': 'Province',
            'country': 'Country',
            'postal_code': 'Postal Code',
            'linkedin_profile': 'LinkedIn Profile',
            'facebook_profile': 'Facebook Profile', 
            'twitter_profile': 'Twitter Profile',
            'current_position': 'Current Position',
            'current_employer': 'Current Employer',
            'industry': 'Industry',
            'employment_status': 'Employment Status',
            'salary_range': 'Salary Range',
        }
        help_texts = {
            'gender': 'Select your gender (optional)',
            'phone_number': 'Your mobile number (e.g. +639519021544)',
            'address': 'Your full address (optional)',
            'city': 'Your city (optional)',
            'state': 'Your state or province (optional)',
            'country': 'Select your country (optional)',
            'postal_code': 'Your ZIP or postal code (optional)',
            'linkedin_profile': 'Your LinkedIn profile URL (optional)',
            'facebook_profile': 'Your Facebook profile URL (optional)',
            'twitter_profile': 'Your Twitter profile URL (optional)',
            'salary_range': 'This information will be kept private and used for statistical purposes only.',
            'employment_status': 'Select your current employment status',
            'industry': 'Enter the industry you currently work in',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields not required
        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        # Clean URLs - ensure they have http:// or https:// prefix
        for field in ['linkedin_profile', 'facebook_profile', 'twitter_profile']:
            url = cleaned_data.get(field)
            if url and not url.startswith(('http://', 'https://')):
                cleaned_data[field] = f'https://{url}'
        return cleaned_data

class EducationForm(forms.ModelForm):
    program = forms.ChoiceField(
        choices=Education.PROGRAM_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    school = forms.ChoiceField(
        choices=Education.SCHOOL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    graduation_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Year Graduated'
    )
    
    class Meta:
        model = Education
        fields = ['program', 'major', 'school', 'graduation_year', 'achievements']
        widgets = {
            'major': forms.TextInput(attrs={'class': 'form-control'}),
            'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'graduation_year': 'Year Graduated',
        }
        help_texts = {
            'program': 'Your program',
            'major': 'Your specialization (if any)',
            'school': 'Your campus',
            'graduation_year': 'Year of graduation',
            'achievements': 'Notable achievements, awards, or honors'
        }

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = [
            'company', 'position', 'location', 'start_date', 'end_date', 
            'is_current', 'description', 'career_significance', 
            'achievements', 'salary_range', 'skills_gained'
        ]
        widgets = {
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Accenture Philippines'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Software Developer'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dumaguete City, Negros Oriental'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe your responsibilities and key projects'}),
            'career_significance': forms.Select(attrs={'class': 'form-select'}),
            'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'e.g. Led a team of 5 developers, Increased system efficiency by 30%'}),
            'salary_range': forms.Select(attrs={'class': 'form-select'}),
            'skills_gained': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'e.g. Python, Django, React, Project Management'}),
        }
        help_texts = {
            'is_current': 'Check this if this is your current job. This will update your profile\'s current position.',
            'skills_gained': 'Enter skills gained in this role, separated by commas.',
            'achievements': 'List your key achievements in this role.',
            'location': 'City and province where you worked',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current = cleaned_data.get('is_current')

        if is_current:
            cleaned_data['end_date'] = None
        elif start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be earlier than start date.")

        return cleaned_data

class SkillForm(forms.ModelForm):
    skill_type = forms.ChoiceField(
        choices=[('', '---------')] + list(Skill.SKILL_TYPES),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select skill type'
        })
    )
    proficiency_level = forms.ChoiceField(
        choices=[('', '---------')] + list(Skill.PROFICIENCY_LEVELS),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select proficiency level'
        })
    )
    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter skill name'
        })
    )
    
    class Meta:
        model = Skill
        fields = ['name', 'skill_type', 'proficiency_level']
        help_texts = {
            'name': 'Name of the skill',
            'skill_type': 'Category of the skill',
            'proficiency_level': 'Rate your proficiency from 1 to 5'
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        skill_type = cleaned_data.get('skill_type')
        proficiency_level = cleaned_data.get('proficiency_level')

        if not name and (skill_type or proficiency_level):
            raise forms.ValidationError("Skill name is required if type or proficiency is specified.")
        
        if name and not skill_type:
            raise forms.ValidationError("Please select a skill type.")
            
        if name and not proficiency_level:
            raise forms.ValidationError("Please select a proficiency level.")

        return cleaned_data

class DocumentUploadForm(forms.ModelForm):
    title = forms.CharField(
        max_length=255,
        required=False,
        help_text="Give your document a descriptive title"
    )
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.doc,.docx'
        }),
        help_text="Upload PDF, DOC, or DOCX files (Max size: 5MB)"
    )

    class Meta:
        model = Document
        fields = ['title', 'file']

class TranscriptUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'TRANSCRIPT'
        self.fields['title'].help_text = "Name of your academic transcript"
        self.fields['file'].help_text = "Upload your academic transcript (PDF format preferred)"

class CertificateUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'CERTIFICATE'
        self.fields['title'].help_text = "Name of your certificate"
        self.fields['file'].help_text = "Upload your certificate (PDF format preferred)"

class DiplomaUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'DIPLOMA'
        self.fields['title'].help_text = "Name of your diploma"
        self.fields['file'].help_text = "Upload your diploma (PDF format preferred)"

class ResumeUploadForm(DocumentUploadForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['document_type'] = 'RESUME'
        self.fields['title'].help_text = "Name your resume/CV"
        self.fields['file'].help_text = "Upload your resume/CV (PDF format preferred)"

# Create formsets for related models
EducationFormSet = inlineformset_factory(
    Profile,
    Education,
    form=EducationForm,
    extra=0,
    can_delete=True,
    fields=['program', 'major', 'school', 'graduation_year', 'achievements'],
    widgets={
        'major': forms.TextInput(attrs={'class': 'form-control'}),
        'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
    }
)

ExperienceFormSet = inlineformset_factory(
    Profile,
    Experience,
    form=ExperienceForm,
    extra=0,
    can_delete=True,
    fields=[
        'company', 'position', 'location', 'start_date', 'end_date', 
        'is_current', 'description', 'career_significance', 
        'achievements', 'salary_range', 'skills_gained'
    ],
    widgets={
        'company': forms.TextInput(attrs={'class': 'form-control'}),
        'position': forms.TextInput(attrs={'class': 'form-control'}),
        'location': forms.TextInput(attrs={'class': 'form-control'}),
        'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        'career_significance': forms.Select(attrs={'class': 'form-select'}),
        'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        'salary_range': forms.Select(attrs={'class': 'form-select'}),
        'skills_gained': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
    }
)

SkillFormSet = inlineformset_factory(
    Profile,
    Skill,
    form=SkillForm,
    extra=0,
    can_delete=True,
    validate_min=False,
    fields=['name', 'skill_type', 'proficiency_level']
)

class MentorApplicationForm(forms.ModelForm):
    expertise_areas = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your areas of expertise (comma-separated)'
        }),
        help_text='List your areas of expertise, separated by commas'
    )
    
    years_of_experience = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Years of professional experience'
        })
    )
    
    certifications = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf'
        }),
        help_text='Upload your certifications in PDF format'
    )
    
    training_documents = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf'
        }),
        help_text='Upload your training documents in PDF format'
    )
    
    competency_summary = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe your expertise and competencies'
        }),
        help_text='Provide a detailed summary of your expertise and how you can help mentees'
    )
    
    class Meta:
        model = MentorApplication
        fields = ['expertise_areas', 'years_of_experience', 'certifications', 'training_documents', 'competency_summary']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )
        
    def clean_certifications(self):
        certifications = self.cleaned_data.get('certifications')
        if certifications:
            if not certifications.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed for certifications.')
            if certifications.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('File size must be under 5MB.')
        return certifications
    
    def clean_training_documents(self):
        training_docs = self.cleaned_data.get('training_documents')
        if training_docs:
            if not training_docs.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed for training documents.')
            if training_docs.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('File size must be under 5MB.')
        return training_docs


# Enhanced Password Reset Forms

class PasswordResetEmailForm(forms.Form):
    """Form for requesting password reset email"""
    
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text="Enter the email address associated with your account"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email


class PasswordResetOTPForm(forms.Form):
    """Form for entering OTP verification code"""
    
    verification_code = forms.CharField(
        label="Verification Code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit code',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'one-time-code'
        }),
        help_text="Enter the 6-digit verification code sent to your email"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        if code and not code.isdigit():
            raise forms.ValidationError("Verification code must contain only numbers.")
        return code


class PasswordResetNewPasswordForm(forms.Form):
    """Form for setting new password"""
    
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        }),
        help_text="Password must be at least 8 characters with uppercase, lowercase, number, and special character."
    )
    
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            errors = PasswordValidator.validate_password_strength(password1)
            if errors:
                raise forms.ValidationError(errors)
            
            # Check password history if user exists
            if self.user:
                if not PasswordValidator.check_password_history(self.user, password1):
                    raise forms.ValidationError("You cannot reuse a recently used password.")
        
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data


class EnhancedSignupForm(forms.Form):
    """Enhanced signup form with email verification"""
    
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'autocomplete': 'family-name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autocomplete': 'email'
        })
    )
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password'
        }),
        help_text="Password must be at least 8 characters with uppercase, lowercase, number, and special character."
    )
    
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field if enabled in database
        if is_recaptcha_enabled():
            self.fields['captcha'] = DatabaseReCaptchaField(
                widget=DatabaseReCaptchaV3(
                    attrs={
                        'data-callback': 'onRecaptchaSuccess',
                        'data-expired-callback': 'onRecaptchaExpired',
                        'data-error-callback': 'onRecaptchaError',
                    }
                ),
                label='Security Verification'
            )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            errors = PasswordValidator.validate_password_strength(password1)
            if errors:
                raise forms.ValidationError(" ".join(errors))
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data
    
    def save(self, request=None):
        """Create user account"""
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        
        # Use email as username since we're using email-based authentication
        username = email
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False  # Will be activated after email verification
        )
        
        return user


class EmailVerificationForm(forms.Form):
    """Form for email verification"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
            'required': True
        })
    )
    
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control otp-input',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autocomplete': 'off',
            'required': True
        }),
        help_text="Enter the 6-digit verification code sent to your email."
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        if code:
            if not code.isdigit():
                raise forms.ValidationError("Verification code must contain only numbers.")
        return code