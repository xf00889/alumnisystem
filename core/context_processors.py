"""
Context processors for adding global template variables
"""


TRACER_STUDY_PAGE_NAMES = frozenset({
    'tracer_study_public_list',
    'tracer_study_alumni',
    'tracer_study_employer',
})


def user_role_context(request):
    """
    Add user role information to template context
    """
    context = {
        'is_alumni_coordinator': False,
        'can_access_system_config': False,
        # Shared templates choose their layout based on the authenticated user role.
        'alumni_page_base': 'base.html',
        'use_alumni_layout': False,
        'load_alumni_feature_scripts': False,
        # Public tracer pages retain public chrome for unauthenticated visitors.
        'tracer_study_page_base': 'base_landingpage.html',
        'has_mentee_dashboard': False,
        'has_mentor_dashboard': False,
    }
    
    if request.user.is_authenticated:
        # HR accounts manage job-board content and must retain the legacy
        # management presentation, even when they are not Django staff.
        is_hr_user = False
        if hasattr(request.user, 'profile'):
            context['is_alumni_coordinator'] = request.user.profile.is_alumni_coordinator
            is_hr_user = getattr(request.user.profile, 'is_hr', False)

        # Only regular alumni receive the separate alumni design system.
        # Preserve elevated-role pages and all backend permissions.
        if not (request.user.is_staff or request.user.is_superuser
                or context['is_alumni_coordinator'] or is_hr_user):
            context['alumni_page_base'] = 'base_alumni.html'
            context['use_alumni_layout'] = True
            # The alumni dashboard keeps its minimal script bundle. Only opted-in
            # feature modules need interactive legacy vendor libraries.
            match = getattr(request, 'resolver_match', None)
            context['load_alumni_feature_scripts'] = (
                bool(match) and match.app_name in
                {'accounts', 'alumni_directory', 'jobs', 'mentorship',
                 'alumni_groups', 'connections', 'events', 'announcements',
                 'donations', 'surveys', 'feedback'}
            )

        context['tracer_study_page_base'] = context['alumni_page_base']

        try:
            from accounts.models import Mentor, MentorshipRequest
            context['has_mentor_dashboard'] = Mentor.objects.filter(user=request.user).exists()
            context['has_mentee_dashboard'] = MentorshipRequest.objects.filter(
                mentee=request.user,
                status__in=['PENDING', 'APPROVED', 'PAUSED', 'COMPLETED', 'CANCELLED']
            ).exists()
        except Exception:
            context['has_mentee_dashboard'] = False
            context['has_mentor_dashboard'] = False

        # Only superusers can access system configuration
        context['can_access_system_config'] = request.user.is_superuser
    
    return context


def tracer_study_banner_context(request):
    context = {
        'show_tracer_study_banner': False,
        'show_public_tracer_study_badge': False,
        'public_tracer_study_count': 0,
    }
    current_url_name = getattr(
        getattr(request, 'resolver_match', None), 'url_name', ''
    )
    # Keep the public availability signal compact and persistent in navigation.
    try:
        from surveys.tracer_study import public_tracer_banner_queryset

        public_count = public_tracer_banner_queryset().count()
        context.update({
            'show_public_tracer_study_badge': public_count > 0,
            'public_tracer_study_count': public_count,
        })
    except Exception:
        # Fail closed during migrations or when the surveys table is not
        # available (for example, first-time setup).
        pass

    if current_url_name in TRACER_STUDY_PAGE_NAMES:
        return context

    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return context

    if request.user.is_staff or request.user.is_superuser:
        return context

    try:
        profile = request.user.profile
        if profile.is_alumni_coordinator or not profile.has_completed_registration:
            return context

        alumni = request.user.alumni
        from surveys.models import Survey, SurveyResponse
        from surveys.tracer_study import ALUMNI_TITLE, _get_active_survey

        survey = _get_active_survey(ALUMNI_TITLE, alumni)
        show_banner = bool(
            survey
            and not SurveyResponse.objects.filter(survey=survey, alumni=alumni).exists()
        )
        context.update({
            'show_tracer_study_banner': show_banner,
            'tracer_study_banner_survey': survey,
        })
        return context
    except Exception:
        return context


def recaptcha_context(request):
    """
    Add reCAPTCHA configuration to template context
    """
    try:
        from core.recaptcha_utils import get_recaptcha_public_key, get_recaptcha_config
        
        # Get the config to check if reCAPTCHA is enabled
        config = get_recaptcha_config()
        public_key = get_recaptcha_public_key()
        
        return {
            'recaptcha_public_key': public_key if public_key else '',
            'recaptcha_site_key': public_key if public_key else '',  # Alias for compatibility
            'recaptcha_enabled': bool(config and config.enabled) if config else False,
        }
    except Exception:
        # Return empty values if there's an error
        return {
            'recaptcha_public_key': '',
            'recaptcha_site_key': '',
            'recaptcha_enabled': False,
        }


def sso_context(request):
    """
    Add SSO configuration to template context
    """
    try:
        from core.sso_utils import get_enabled_sso_providers
        enabled_providers = get_enabled_sso_providers()
        return {
            'sso_providers': enabled_providers,
            'enabled_sso_providers': enabled_providers,  # Alias for template compatibility
        }
    except Exception:
        return {
            'sso_providers': [],
            'enabled_sso_providers': [],
        }


def cms_contact_info(request):
    """
    Add CMS contact information to template context
    """
    try:
        from cms.models import ContactInfo
        contact_info = ContactInfo.objects.filter(is_active=True).order_by('contact_type', 'order')
        return {
            'cms_contact_info': contact_info,
        }
    except Exception:
        return {
            'cms_contact_info': [],
        }


def seo_context(request):
    """
    Add SEO information to template context
    """
    try:
        from core.models.seo import PageSEO, OrganizationSchema
        
        # Get SEO data for current page if available
        path = request.path
        page_seo = PageSEO.objects.filter(page_path=path, is_active=True).first()
        
        # Get organization schema for default values
        org_schema = OrganizationSchema.objects.filter(is_active=True).first()
        
        # Default values
        default_title = 'NORSU Alumni Network'
        default_description = 'Connect with NORSU alumni, access exclusive opportunities, and stay engaged with the university community.'
        default_keywords = 'NORSU, alumni, network, university, graduates'
        
        # Build SEO object with proper fallbacks
        seo_data = {
            'title': page_seo.meta_title if page_seo else default_title,
            'description': page_seo.meta_description if page_seo else default_description,
            'keywords': page_seo.meta_keywords if page_seo else default_keywords,
            'canonical_url': page_seo.canonical_url if (page_seo and page_seo.canonical_url) else request.build_absolute_uri(path),
            'og_image': page_seo.og_image.url if (page_seo and page_seo.og_image) else (org_schema.logo if org_schema else ''),
            'twitter_image': page_seo.twitter_image.url if (page_seo and page_seo.twitter_image) else '',
            'og_type': 'website',  # Default to website
            'site_name': org_schema.name if org_schema else default_title,
        }
        
        return {
            'page_seo': page_seo,
            'seo': seo_data,
        }
    except Exception as e:
        # Return default SEO data if there's an error
        return {
            'page_seo': None,
            'seo': {
                'title': 'NORSU Alumni Network',
                'description': 'Connect with NORSU alumni, access exclusive opportunities, and stay engaged with the university community.',
                'keywords': 'NORSU, alumni, network, university, graduates',
                'canonical_url': request.build_absolute_uri(request.path),
                'og_image': '',
                'twitter_image': '',
                'og_type': 'website',
                'site_name': 'NORSU Alumni Network',
            },
        }


def footer_links(request):
    """
    Add footer links to template context
    """
    try:
        from cms.models import FooterLink, LegalPage
        links = FooterLink.objects.filter(is_active=True).order_by('order')
        legal_pages = list(LegalPage.objects.filter(is_published=True))
        return {
            'footer_links': links,
            'legal_pages': legal_pages,
            'legal_terms_page': next((page for page in legal_pages if page.page_type == 'terms'), None),
            'legal_privacy_page': next((page for page in legal_pages if page.page_type == 'privacy'), None),
        }
    except Exception:
        return {
            'footer_links': [],
            'legal_pages': [],
            'legal_terms_page': None,
            'legal_privacy_page': None,
        }
