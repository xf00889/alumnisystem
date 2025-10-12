from django.db.models import Count
from .models.page_content import SiteConfiguration, PageSection, Testimonial, StaffMember

def site_configuration(request):
    """
    Add site configuration to the context of all templates
    """
    try:
        config = SiteConfiguration.objects.first()
        if not config:
            config = SiteConfiguration.objects.create()
    except:
        config = None
    
    return {
        'site_config': config
    }

def dynamic_content(request):
    """
    Add dynamic page sections to the context of all templates
    """
    context = {}
    
    # Get active page sections
    try:
        hero_sections = PageSection.objects.filter(section_type='HERO', is_active=True).order_by('order')
        feature_sections = PageSection.objects.filter(section_type='FEATURE', is_active=True).order_by('order')
        about_sections = PageSection.objects.filter(section_type='ABOUT', is_active=True).order_by('order')
        cta_sections = PageSection.objects.filter(section_type='CTA', is_active=True).order_by('order')
        statistic_sections = PageSection.objects.filter(section_type='STATISTIC', is_active=True).order_by('order')
        footer_sections = PageSection.objects.filter(section_type='FOOTER', is_active=True).order_by('order')
        
        # Get first section of each type for template compatibility
        hero_section = hero_sections.first()
        feature_section = feature_sections.first()
        testimonial_section = PageSection.objects.filter(section_type='TESTIMONIAL', is_active=True).order_by('order').first()
        cta_section = cta_sections.first()
        
        # Get all feature sections as a list for the features loop
        features = list(feature_sections)
        
        context.update({
            'hero_sections': hero_sections,
            'feature_sections': feature_sections,
            'about_sections': about_sections,
            'cta_sections': cta_sections,
            'statistic_sections': statistic_sections,
            'footer_sections': footer_sections,
            # Template-compatible variables
            'hero_section': hero_section,
            'feature_section': feature_section,
            'testimonial_section': testimonial_section,
            'cta_section': cta_section,
            'features': features,
        })
    except:
        pass
    
    # Get active testimonials
    try:
        testimonials = Testimonial.objects.filter(is_active=True).order_by('-is_featured', 'order')[:6]
        context['testimonials'] = testimonials
    except:
        pass
    
    # Get active staff members
    try:
        staff_members = StaffMember.objects.filter(is_active=True).order_by('staff_type', 'order')
        context['staff_members'] = staff_members
    except:
        pass
    
    # Get dynamic statistics
    try:
        from alumni_directory.models import Alumni
        from alumni_groups.models import AlumniGroup
        from jobs.models import JobPosting
        
        config = SiteConfiguration.objects.first()
        
        # Use overrides if available, otherwise use actual counts
        alumni_count = config.alumni_count_override if config and config.alumni_count_override else Alumni.objects.count()
        groups_count = config.groups_count_override if config and config.groups_count_override else AlumniGroup.objects.count()
        jobs_count = config.jobs_count_override if config and config.jobs_count_override else JobPosting.objects.count()
        
        context.update({
            'alumni_count': alumni_count,
            'groups_count': groups_count,
            'jobs_count': jobs_count,
            # Template-compatible display variables
            'alumni_count_display': f"{alumni_count:,}" if alumni_count else "5,000+",
            'group_count_display': f"{groups_count:,}" if groups_count else "25+",
            'job_count_display': f"{jobs_count:,}" if jobs_count else "100+",
        })
    except:
        pass
    
    return context