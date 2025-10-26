from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DonationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donations'
    verbose_name = _('Donations & Fundraising')

    def ready(self):
        import donations.signals  # noqa
        
        # Auto-populate campaign types if none exist
        try:
            from .models import CampaignType
            if CampaignType.objects.count() == 0:
                self._populate_campaign_types()
        except Exception:
            # Ignore errors during app startup (e.g., during migrations)
            pass
    
    def _populate_campaign_types(self):
        """Populate default campaign types if none exist"""
        from .models import CampaignType
        
        campaign_types = [
            {
                'name': 'Scholarship Fund',
                'description': 'Fundraising campaigns for student scholarships and financial aid'
            },
            {
                'name': 'Infrastructure Development',
                'description': 'Campaigns to improve university facilities and infrastructure'
            },
            {
                'name': 'Research & Innovation',
                'description': 'Funding for research projects and innovation initiatives'
            },
            {
                'name': 'Student Support',
                'description': 'Support for student activities, organizations, and programs'
            },
            {
                'name': 'Alumni Events',
                'description': 'Funding for alumni reunions, conferences, and networking events'
            },
            {
                'name': 'Emergency Relief',
                'description': 'Emergency funds for students and alumni in need'
            },
            {
                'name': 'Technology Upgrade',
                'description': 'Modernizing university technology and equipment'
            },
            {
                'name': 'Community Outreach',
                'description': 'Programs that benefit the local community and society'
            }
        ]
        
        for ct_data in campaign_types:
            CampaignType.objects.get_or_create(
                name=ct_data['name'],
                defaults={'description': ct_data['description']}
            )