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
        # Don't add captcha field - it's handled in the template and adapter

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
        # Don't add captcha field - it's handled in the template
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

    # Campus-specific program mapping
    # Format: Campus -> College -> Programs
    # Note: All campuses now show all programs under each college
    PROGRAMS_BY_CAMPUS = {
        'NORSU-MAIN': 'ALL',
        'NORSU-BSC': 'ALL',
        'NORSU-BAIS': 'ALL',
        'NORSU-GUI': 'ALL',
        'NORSU-MAB': 'ALL',
        'NORSU-SIA': 'ALL',
        'NORSU-PAM': 'ALL',
        'OTHER': 'ALL',
    }

    # Organize courses by college for cascading dropdown functionality (fallback for campuses with 'ALL')
    COURSES_BY_COLLEGE = {
        'CAS': [  # College of Arts and Sciences
            ('BSBIO', 'BS in Biology'),
            ('BSCHEM', 'BS in Chemistry'),
            ('BSCS', 'BS in Computer Science'),
            ('BSGEO', 'BS in Geology'),
            ('BSIT', 'BS in Information Technology'),
            ('BMC', 'Bachelor of Mass Communication'),
            ('BSM', 'BS in Mathematics'),
            ('BSP', 'BS in Psychology'),
        ],
        'CBA': [  # College of Business (formerly College of Business Administration)
            ('BSA', 'BS in Accountancy'),
            ('BSBA', 'BS in Business Administration'),
            ('BSBA-HRDM', 'BSBA Major in Human Resource Development Management'),
            ('BSBA-FM', 'BSBA Major in Financial Management'),
            ('BSOSM', 'BS in Office Systems Management'),
        ],
        'CEA': [  # College of Engineering (formerly College of Engineering and Architecture)
            ('BSARCH', 'BS in Architecture'),
            ('BSCE', 'BS in Civil Engineering'),
            ('BSCPE', 'BS in Computer Engineering'),
            ('BSEE', 'BS in Electrical Engineering'),
            ('BSECE', 'BS in Electronics and Communication Engineering'),
            ('BSGE', 'BS in Geodetic Engineering'),
            ('BSGTHE', 'BS in Geothermal Engineering'),
            ('BSME', 'BS in Mechanical Engineering'),
        ],
        'CNPAHS': [  # College of Nursing, Pharmacy and Allied Health Sciences
            ('BSN', 'BS in Nursing'),
            ('BSP', 'BS in Pharmacy'),
            ('MIDWIFERY', 'Midwifery'),
            ('AMDNA', 'AMDNA'),
        ],
        'CTHM': [  # College of Tourism and Hospitality Management
            ('BSHM', 'BS in Hospitality Management'),
            ('BSTM', 'BS in Tourism'),
        ],
        'CAFF': [  # College of Agriculture, Forestry and Fisheries
            ('BSF', 'BS in Forestry'),
            ('BSA-AGRI', 'BS in Agriculture'),
            ('BSA-AGRON', 'BS in Agriculture Major in Agronomy'),
            ('BSA-HORT', 'BS in Agriculture Major in Horticulture'),
            ('BSA-ANSCI', 'BS in Agriculture Major in Animal Science'),
            ('BSA-AGEXT', 'BS in Agriculture Major in Agricultural Extension'),
        ],
        'CCJE': [  # College of Criminal Justice Education
            ('BSCRIM', 'BS in Criminology'),
        ],
        'CIT': [  # College of Industrial Technology
            ('BIT', 'Bachelor of Science in Industrial Technology'),
            ('BSAT', 'BS in Automotive Technology'),
            ('BSAM', 'BS in Aviation Maintenance'),
            ('BSCT', 'BS in Civil Technology'),
            ('BSCET', 'BS in Computer and Electronics Technology'),
            ('BSET', 'BS in Electrical Technology'),
            ('BSFT', 'BS in Food Technology'),
            ('BSIT-INDTECH', 'BS in Industrial Technology'),
            ('BSMT', 'BS in Mechanical Technology'),
            ('BSRACT', 'BS in Refrigeration and Air-Conditioning Technology'),
        ],
        'CTE': [  # College of Education (formerly College of Teacher Education)
            ('BSED', 'BS in Elementary Education'),
            ('BEED', 'BS in Secondary Education'),
        ],
        'COL': [  # College of Law
            ('LLB', 'Bachelor of Law'),
        ],
    }

    # Majors available for specific programs
    # Format: Program Code -> List of majors
    # Note: This is a general list. Campus-specific majors are defined in MAJORS_BY_CAMPUS_PROGRAM
    MAJORS_BY_PROGRAM = {
        # Bachelor of Secondary Education
        'BSED': [
            ('ENGLISH', 'Major in English'),
            ('FILIPINO', 'Major in Filipino'),
            ('MATHEMATICS', 'Major in Mathematics'),
            ('SCIENCE', 'Major in Science'),
            ('SOCIAL_STUDIES', 'Major in Social Studies'),
            ('VALUES_EDUCATION', 'Major in Religious and Values Education'),
        ],
        'BSED-ENG': [('ENGLISH', 'Major in English')],
        'BSED-MATH': [('MATHEMATICS', 'Major in Mathematics')],
        'BSED-SCI': [('SCIENCE', 'Major in Science')],
        'BSED-SS': [('SOCIAL_STUDIES', 'Major in Social Studies')],
        
        # Bachelor of Elementary Education
        'BEED': [
            ('GENERAL_EDUCATION', 'Major in General Education'),
            ('EARLY_CHILDHOOD', 'Major in Early Childhood Education'),
            ('SPECIAL_EDUCATION', 'Major in Special Education'),
            ('ENGLISH', 'Major in English'),
            ('FILIPINO', 'Major in Filipino'),
            ('MATHEMATICS', 'Major in Mathematics'),
            ('SCIENCE', 'Major in Science'),
            ('SOCIAL_STUDIES', 'Major in Social Studies'),
            ('MAPE', 'Major in Music, Arts and Physical Education'),
            ('THE', 'Major in Technology and Home Economics'),
        ],
        'BEED-GC': [('GENERAL_EDUCATION', 'Major in General Education')],
        
        # Bachelor of Industrial Technology
        'BIT': [
            ('AUTOMOTIVE', 'Major in Automotive Technology'),
            ('COMPUTER', 'Major in Computer Technology'),
            ('ELECTRICAL', 'Major in Electrical Technology'),
            ('ELECTRONICS', 'Major in Electronics Technology'),
            ('DRAFTING', 'Major in Drafting Technology'),
            ('FOOD_PROCESSING', 'Major in Food Processing Technology'),
            ('WELDING', 'Major in Welding and Fabrication Technology'),
        ],
        'BIT-AT': [('AUTOMOTIVE', 'Major in Automotive Technology')],
        'BIT-CT': [('COMPUTER', 'Major in Computer Technology')],
        'BIT-ELT': [('ELECTRICAL', 'Major in Electrical Technology')],
        'BIT-ELXT': [('ELECTRONICS', 'Major in Electronics Technology')],
        'BSIT-AT': [('AUTOMOTIVE', 'Major in Automotive Technology')],
        'BSIT-ET': [('ELECTRONICS', 'Major in Electronics Technology')],
        'BSIT-FPSM': [('FOOD_PROCESSING', 'Major in Food Processing and Service Management')],
        
        # Bachelor of Science in Business Administration
        'BSBA': [
            ('HRDM', 'Major in Human Resource Development Management'),
            ('FINANCIAL_MANAGEMENT', 'Major in Financial Management'),
        ],
        'BSBA-HRDM': [('HRDM', 'Major in Human Resource Development Management')],
        'BSBA-FM': [('FINANCIAL_MANAGEMENT', 'Major in Financial Management')],
        
        # Bachelor of Science in Agriculture
        'BSA-AGRI': [
            ('AGRONOMY', 'Major in Agronomy'),
            ('ANIMAL_SCIENCE', 'Major in Animal Science'),
            ('FORESTRY', 'Major in Forestry'),
        ],
        'BSA-AGRON': [('AGRONOMY', 'Major in Agronomy')],
        'BSA-HORT': [('HORTICULTURE', 'Major in Horticulture')],
        'BSA-ANSCI': [('ANIMAL_SCIENCE', 'Major in Animal Science')],
        'BSA-AGEXT': [('AGRICULTURAL_EXTENSION', 'Major in Agricultural Extension')],
        
        # Programs without majors: BSIT, BSCS, BSA, BSHM, BSTM, BSN, BSCRIM, etc.
    }

    # Campus-specific major restrictions
    # Format: Campus Code -> Program Code -> List of majors
    MAJORS_BY_CAMPUS_PROGRAM = {
        'NORSU-BSC': {  # Bayawan-Sta. Catalina Campus - Specific majors only
            'BSED': [
                ('SCIENCE', 'Major in Science'),
                ('MATHEMATICS', 'Major in Mathematics'),
                ('ENGLISH', 'Major in English'),
            ],
            'BEED': [
                ('GENERAL_CURRICULUM', 'Major in General Curriculum'),
            ],
            'BIT': [
                ('AUTOMOTIVE', 'Major in Automotive Technology'),
                ('COMPUTER', 'Major in Computer Technology'),
                ('ELECTRICAL', 'Major in Electrical Technology'),
                ('ELECTRONICS', 'Major in Electronics Technology'),
            ],
            # BSCS, BSIT, BSCRIM, BSOA, BSHM, BSBA have no majors at BSC
        },
        # Other campuses use the general MAJORS_BY_PROGRAM
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
        help_text="Enter your first name as it appears on your diploma",
        label="First Name"
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        help_text="Enter your last name as it appears on your diploma",
        label="Last Name"
    )
    campus = forms.ChoiceField(
        choices=SCHOOL_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select your campus",
        label="Campus"
    )
    college = forms.ChoiceField(
        choices=COLLEGE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select your campus first to see available colleges",
        label="College"
    )
    course_graduated = forms.ChoiceField(
        choices=ALL_PROGRAM_CHOICES,  # Use all choices for validation
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select your campus and college first to see available programs",
        label="Program/Course"
    )
    major = forms.ChoiceField(
        choices=[('', '-- Select your program first --')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text="Select your program first to see available majors (if applicable)",
        label="Major/Specialization"
    )
    major_other = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your major/specialization',
        }),
        help_text="Specify your major if not listed above",
        label="Specify Major"
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
        label="Graduation Year"
    )
    present_occupation = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Software Engineer, Teacher, Nurse'
        }),
        help_text="Your current job title or position",
        label="Present Occupation"
    )
    company_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Accenture Philippines, DepEd, Provincial Hospital'
        }),
        help_text="The name of the company or organization you currently work for",
        label="Company Name"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initially set college and course choices to be empty (will be populated by JavaScript)
        # But keep all choices available for validation
        if not self.data:  # Only on initial form load, not on form submission
            self.fields['college'].widget.choices = [
                ('', '-- Select your campus first --')
            ]
            self.fields['course_graduated'].widget.choices = [
                ('', '-- Select your campus and college first --')
            ]
            self.fields['major'].widget.choices = [
                ('', '-- Select your program first --')
            ]
        else:
            # On form submission, dynamically set major choices based on submitted data
            campus = self.data.get('campus')
            course = self.data.get('course_graduated')
            
            if campus and course:
                # Get available majors for this program and campus
                major_choices = self.get_majors_for_program(course, campus)
                if major_choices:
                    self.fields['major'].choices = major_choices
                else:
                    # No majors for this program - set to empty choice
                    self.fields['major'].choices = [('', 'No major required')]
                    # Make sure the field doesn't validate against choices
                    self.fields['major'].required = False
            else:
                # No course selected yet, set default choices
                self.fields['major'].choices = [('', '-- Select your program first --')]
                self.fields['major'].required = False

    def clean_major(self):
        """Clean and validate the major field."""
        major = self.cleaned_data.get('major', '')
        course = self.data.get('course_graduated', '')
        
        # If major is empty, None, or 'NONE', treat it as empty string
        if not major or major in ['NONE', 'None', 'none']:
            major = ''
        
        # If no course selected yet, allow empty major
        if not course:
            return ''
        
        # Get available majors for the selected program
        campus = self.data.get('campus', '')
        available_majors = self.get_majors_for_program(course, campus)
        
        # If program has no majors, empty major is valid
        if not available_majors:
            return ''
        
        # If major is empty but program has majors, that's okay (major is optional)
        if not major:
            return ''
        
        # If major is provided, validate it's in the available choices
        valid_major_codes = [m[0] for m in available_majors]
        if major and major not in valid_major_codes:
            # Allow it anyway since major is optional
            return ''
        
        return major

    def clean_graduation_year(self):
        year = self.cleaned_data['graduation_year']
        current_year = datetime.datetime.now().year
        if year < 1970 or year > current_year:
            raise forms.ValidationError(f"Please enter a year between 1970 and {current_year}")
        return year

    def clean(self):
        cleaned_data = super().clean()
        campus = cleaned_data.get('campus')
        course = cleaned_data.get('course_graduated')
        college = cleaned_data.get('college')

        # Validate that campus, college and course are selected
        if not campus:
            raise forms.ValidationError("Please select your campus.")

        if not college:
            raise forms.ValidationError("Please select your college.")

        if not course:
            raise forms.ValidationError("Please select your course/program.")

        # Validate campus-college-course combination for non-OTHER courses
        if campus and college and course and course != 'OTHER':
            # Get available programs for this campus and college
            campus_programs = self.PROGRAMS_BY_CAMPUS.get(campus)
            
            if campus_programs and campus_programs != 'ALL':
                # Campus has specific program restrictions
                if college not in campus_programs:
                    from alumni_directory.models import Alumni
                    college_dict = dict(Alumni.COLLEGE_CHOICES)
                    college_name = college_dict.get(college, college)
                    raise forms.ValidationError(
                        f"{college_name} is not available at the selected campus. "
                        f"Please select a different college or campus."
                    )
                
                # Check if course is available for this campus-college combination
                available_courses = [course_code for course_code, _ in campus_programs.get(college, [])]
                if course not in available_courses:
                    from alumni_directory.models import Alumni
                    college_dict = dict(Alumni.COLLEGE_CHOICES)
                    college_name = college_dict.get(college, college)
                    raise forms.ValidationError(
                        f"The course '{course}' is not available in {college_name} at the selected campus. "
                        f"Please select a different course."
                    )
            else:
                # Campus allows all programs - use fallback validation
                expected_college = self.COURSE_COLLEGE_MAPPING.get(course)
                if expected_college and college != expected_college:
                    from alumni_directory.models import Alumni
                    college_dict = dict(Alumni.COLLEGE_CHOICES)
                    expected_college_name = college_dict.get(expected_college, expected_college)
                    selected_college_name = college_dict.get(college, college)

                    raise forms.ValidationError(
                        f"Invalid combination: The course '{course}' does not belong to {selected_college_name}. "
                        f"This course belongs to {expected_college_name}. "
                        f"Please select the correct college first, then choose your course from the available options."
                    )

        # Validate major_other field if major is "OTHER"
        major = cleaned_data.get('major')
        major_other = cleaned_data.get('major_other')
        
        if major == 'OTHER' and not major_other:
            raise forms.ValidationError("Please specify your major when selecting 'Other'.")

        return cleaned_data

    @classmethod
    def get_colleges_for_campus(cls, campus_code):
        """
        Get college choices for a specific campus.
        """
        if not campus_code:
            return [('', '-- Select your campus first --')]

        campus_programs = cls.PROGRAMS_BY_CAMPUS.get(campus_code)
        
        if campus_programs == 'ALL' or not campus_programs:
            # Return all colleges
            return cls.COLLEGE_CHOICES
        
        # Return only colleges available at this campus
        from alumni_directory.models import Alumni
        available_colleges = [('', '-- Select your college --')]
        for college_code in campus_programs.keys():
            college_name = dict(Alumni.COLLEGE_CHOICES).get(college_code, college_code)
            available_colleges.append((college_code, college_name))
        
        return available_colleges

    @classmethod
    def get_courses_for_campus_college(cls, campus_code, college_code):
        """
        Get course choices for a specific campus and college combination.
        """
        if not campus_code or not college_code:
            return [('', '-- Select your campus and college first --')]

        campus_programs = cls.PROGRAMS_BY_CAMPUS.get(campus_code)
        
        if campus_programs == 'ALL' or not campus_programs:
            # Use fallback - all courses for this college
            courses = cls.COURSES_BY_COLLEGE.get(college_code, [])
        else:
            # Use campus-specific programs
            courses = campus_programs.get(college_code, [])
        
        choices = [('', '-- Select your program --')]
        choices.extend(courses)
        choices.append(('OTHER', 'Other Program'))
        return choices

    @classmethod
    def get_courses_for_college(cls, college_code):
        """
        Get course choices for a specific college (legacy method for backward compatibility).
        """
        if not college_code:
            return [('', '-- Select your college first --')]

        courses = cls.COURSES_BY_COLLEGE.get(college_code, [])
        choices = [('', '-- Select your program --')]
        choices.extend(courses)
        choices.append(('OTHER', 'Other Program'))
        return choices

    @classmethod
    def get_majors_for_program(cls, program_code, campus_code=None):
        """
        Get major choices for a specific program, optionally filtered by campus.
        Returns empty list if program has no majors.
        """
        if not program_code or program_code == 'OTHER':
            return []

        # Check if campus has specific major restrictions
        if campus_code and campus_code in cls.MAJORS_BY_CAMPUS_PROGRAM:
            campus_majors = cls.MAJORS_BY_CAMPUS_PROGRAM[campus_code].get(program_code, [])
            if campus_majors or program_code in cls.MAJORS_BY_CAMPUS_PROGRAM[campus_code]:
                # Campus has specific majors for this program (even if empty list)
                majors = campus_majors
            else:
                # Campus doesn't specify this program, use general list
                majors = cls.MAJORS_BY_PROGRAM.get(program_code, [])
        else:
            # No campus specified or campus not in restrictions, use general list
            majors = cls.MAJORS_BY_PROGRAM.get(program_code, [])
        
        if not majors:
            return []
        
        choices = [('', '-- Select your major --')]
        choices.extend(majors)
        choices.append(('OTHER', 'Other (Please specify)'))
        return choices

    def save(self, user):
        # Update user's first and last name
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # Determine the major to save
        major = self.cleaned_data.get('major', '')
        if major == 'OTHER':
            # Use custom major input
            major = self.cleaned_data.get('major_other', '')

        # Get the course/program
        course = self.cleaned_data.get('course_graduated', '')

        # Create or update primary education record
        Education.objects.update_or_create(
            profile=user.profile,
            is_primary=True,
            defaults={
                'program': course,
                'major': major,
                'school': self.cleaned_data['campus'],
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
        campus = self.cleaned_data['campus']
        
        if not college and course in self.COURSE_COLLEGE_MAPPING:
            college = self.COURSE_COLLEGE_MAPPING[course]

        # Map campus code to Alumni model campus format
        campus_mapping = {
            'NORSU-MAIN': 'MAIN',
            'NORSU-BAIS': 'BAIS1',
            'NORSU-GUI': 'GUI',
            'NORSU-MAB': 'MAB',
            'NORSU-BSC': 'BSC',
            'NORSU-SIA': 'SIATON',
            'NORSU-PAM': 'PAM',
            'OTHER': 'MAIN',  # Default to main for other
        }
        alumni_campus = campus_mapping.get(campus, 'MAIN')

        Alumni.objects.update_or_create(
            user=user,
            defaults={
                'graduation_year': self.cleaned_data['graduation_year'],
                'course': course,
                'college': college,
                'campus': alumni_campus,
                'current_company': self.cleaned_data['company_name'],
                'job_title': self.cleaned_data['present_occupation'],
                'employment_status': 'EMPLOYED_FULL'  # Assuming full-time employment
            }
        )

        # ── Layer 3: Registry Verification ──────────────────────────────────
        # Check if an imported (unregistered) alumni record matches this user.
        # The import creates Alumni records with is_active=False placeholder users.
        # If a match is found by name + campus + graduation year,
        # we reassign that Alumni record to this real user and mark them verified.
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        try:
            grad_year = self.cleaned_data['graduation_year']

            # Find imported alumni with matching name + campus + graduation year
            imported_match = Alumni.objects.filter(
                user__is_active=False,
                user__first_name__iexact=user.first_name.strip(),
                user__last_name__iexact=user.last_name.strip(),
                graduation_year=grad_year,
                campus=alumni_campus,
            ).exclude(user=user).first()

            if imported_match:
                old_placeholder_user = imported_match.user

                # Reassign the Alumni record to the real registered user
                imported_match.user = user
                imported_match.is_verified = True
                imported_match.graduation_year = grad_year
                imported_match.course = course
                imported_match.college = college
                imported_match.campus = alumni_campus
                imported_match.current_company = self.cleaned_data['company_name']
                imported_match.job_title = self.cleaned_data['present_occupation']
                imported_match.employment_status = 'EMPLOYED_FULL'
                imported_match.save()

                # Remove the auto-generated placeholder user from the import
                old_placeholder_user.delete()

                _logger.info(
                    f"Registry match: user={user.id} ({user.email}) "
                    f"linked to imported alumni record. Auto-verified."
                )
            else:
                # No registry match — leave is_verified=False for admin review
                try:
                    alumni_record = Alumni.objects.get(user=user)
                    if alumni_record.is_verified:
                        alumni_record.is_verified = False
                        alumni_record.save(update_fields=['is_verified'])
                except Alumni.DoesNotExist:
                    pass
                _logger.info(
                    f"No registry match for user={user.id} ({user.email}). "
                    f"Pending admin review."
                )
        except Exception as e:
            _logger.error(
                f"Registry verification error for user={user.id}: {e}",
                exc_info=True
            )
            # Non-fatal — registration still completes, just without auto-verification

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
    # Simple form with all fields enabled
    campus = forms.ChoiceField(
        choices=PostRegistrationForm.SCHOOL_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Campus"
    )
    college = forms.ChoiceField(
        choices=PostRegistrationForm.COLLEGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="College"
    )
    program = forms.ChoiceField(
        choices=PostRegistrationForm.ALL_PROGRAM_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Program/Course"
    )
    major = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Major/Specialization",
        help_text="Your specialization (if any)"
    )
    graduation_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1970, 'max': datetime.datetime.now().year}),
        label='Graduation Year'
    )
    
    class Meta:
        model = Education
        fields = ['program', 'major', 'school', 'graduation_year', 'achievements']
        widgets = {
            'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'graduation_year': 'Graduation Year',
        }
        help_texts = {
            'achievements': 'Notable achievements, awards, or honors'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Map the school field to campus for consistency
        if self.instance and self.instance.pk:
            self.fields['campus'].initial = self.instance.school
            
            # Try to get college from Alumni model
            try:
                alumni = self.instance.profile.user.alumni
                if alumni and alumni.college:
                    self.fields['college'].initial = alumni.college
            except:
                pass
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Map campus back to school field
        instance.school = self.cleaned_data.get('campus')
        
        # Update Alumni college if provided
        college = self.cleaned_data.get('college')
        if college and commit:
            try:
                from alumni_directory.models import Alumni
                alumni, created = Alumni.objects.get_or_create(user=instance.profile.user)
                alumni.college = college
                alumni.save(update_fields=['college'])
            except:
                pass
        
        if commit:
            instance.save()
        return instance

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
        try:
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
        except Exception as e:
            # If reCAPTCHA configuration fails, continue without it
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"reCAPTCHA configuration error in PasswordResetEmailForm: {str(e)}")
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email


class PasswordResetOTPForm(forms.Form):
    """Form for entering OTP verification code"""
    
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text="Enter the email address you used to request password reset"
    )
    
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
        try:
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
        except Exception as e:
            # If reCAPTCHA configuration fails, continue without it
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"reCAPTCHA configuration error in PasswordResetOTPForm: {str(e)}")
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
    
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
        try:
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
        except Exception as e:
            # If reCAPTCHA configuration fails, continue without it
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"reCAPTCHA configuration error in PasswordResetNewPasswordForm: {str(e)}")
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if password1:
            errors = PasswordValidator.validate_password_strength(password1)
            if errors:
                raise forms.ValidationError(errors)
            
            # Check password history if user exists
            if self.user:
                # Check if new password matches current password
                from django.contrib.auth.hashers import check_password
                if check_password(password1, self.user.password):
                    raise forms.ValidationError("Your new password cannot be the same as your old password.")
                
                # Check password history
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