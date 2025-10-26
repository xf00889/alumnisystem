from django.core.management.base import BaseCommand
from donations.models import CampaignType


class Command(BaseCommand):
    help = 'Populate the database with default campaign types'

    def handle(self, *args, **options):
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

        created_count = 0
        for ct_data in campaign_types:
            campaign_type, created = CampaignType.objects.get_or_create(
                name=ct_data['name'],
                defaults={'description': ct_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created campaign type: {campaign_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Campaign type already exists: {campaign_type.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(campaign_types)} campaign types. '
                f'Created {created_count} new types.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Total campaign types in database: {CampaignType.objects.count()}'
            )
        )

