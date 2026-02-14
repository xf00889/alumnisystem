"""
Management command to populate default footer links
"""
from django.core.management.base import BaseCommand
from cms.models import FooterLink


class Command(BaseCommand):
    help = 'Populate default footer links for the CMS'

    def handle(self, *args, **options):
        self.stdout.write('Populating default footer links...')

        # Define default footer links
        default_links = [
            # Quick Links
            {
                'title': 'Home',
                'url': 'core:home',
                'section': 'quick_links',
                'icon': 'fas fa-home',
                'order': 1,
            },
            {
                'title': 'Events',
                'url': 'core:landing_events',
                'section': 'quick_links',
                'icon': 'fas fa-calendar-alt',
                'order': 2,
            },
            {
                'title': 'Announcements',
                'url': 'core:landing_announcements',
                'section': 'quick_links',
                'icon': 'fas fa-bullhorn',
                'order': 3,
            },
            {
                'title': 'Login',
                'url': 'account_login',
                'section': 'quick_links',
                'icon': 'fas fa-sign-in-alt',
                'order': 4,
            },
            {
                'title': 'Sign Up',
                'url': 'account_login',
                'section': 'quick_links',
                'icon': 'fas fa-user-plus',
                'order': 5,
            },
            
            # Information
            {
                'title': 'About Us',
                'url': 'core:about_us',
                'section': 'information',
                'icon': 'fas fa-info-circle',
                'order': 1,
            },
            {
                'title': 'Contact Us',
                'url': 'core:contact_us',
                'section': 'information',
                'icon': 'fas fa-envelope',
                'order': 2,
            },
            {
                'title': 'FAQs',
                'url': 'core:contact_us',
                'section': 'information',
                'icon': 'fas fa-question-circle',
                'order': 3,
            },
            
            # Legal
            {
                'title': 'Privacy Policy',
                'url': '#',
                'section': 'legal',
                'icon': 'fas fa-shield-alt',
                'order': 1,
            },
            {
                'title': 'Terms of Service',
                'url': '#',
                'section': 'legal',
                'icon': 'fas fa-file-contract',
                'order': 2,
            },
            {
                'title': 'Cookie Policy',
                'url': '#',
                'section': 'legal',
                'icon': 'fas fa-cookie-bite',
                'order': 3,
            },
        ]

        created_count = 0
        updated_count = 0

        for link_data in default_links:
            link, created = FooterLink.objects.get_or_create(
                title=link_data['title'],
                section=link_data['section'],
                defaults=link_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {link.title} ({link.get_section_display()})')
                )
            else:
                # Update existing link
                for key, value in link_data.items():
                    setattr(link, key, value)
                link.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {link.title} ({link.get_section_display()})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully populated footer links: {created_count} created, {updated_count} updated'
            )
        )
