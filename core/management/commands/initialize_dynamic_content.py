from django.core.management.base import BaseCommand
from django.db import transaction
from core.models.page_content import SiteConfiguration, PageSection, Testimonial, StaffMember
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Initialize default dynamic content for the site'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting initialization of dynamic content...'))
        
        with transaction.atomic():
            # Create or update site configuration
            self._create_site_configuration()
            
            # Create page sections
            self._create_hero_section()
            self._create_feature_section()
            self._create_testimonial_section()
            self._create_cta_section()
            
            # Create testimonials
            self._create_testimonials()
            
            # Create staff members
            self._create_staff_members()
            
        self.stdout.write(self.style.SUCCESS('Successfully initialized dynamic content!'))
    
    def _create_site_configuration(self):
        site_config, created = SiteConfiguration.objects.get_or_create(
            defaults={
                'site_name': 'NORSU Alumni Network',
                'site_tagline': 'Connecting Graduates, Building Futures',
                'contact_email': 'alumni@norsu.edu.ph',
                'contact_phone': '+63 35 422 6002',
                'contact_address': 'Negros Oriental State University\nKagawasan Ave. Rizal\nDumaguete City, 6200\nNegros Oriental, Philippines',
                'facebook_url': 'https://facebook.com/norsuofficial',
                'twitter_url': 'https://twitter.com/norsuofficial',
                'instagram_url': 'https://instagram.com/norsuofficial',
                'linkedin_url': 'https://linkedin.com/school/norsuofficial',
                'youtube_url': 'https://youtube.com/norsuofficial',
                'footer_text': 'The NORSU Alumni Network connects graduates worldwide, fostering professional growth and community engagement.',
                'copyright_text': '© 2024 Negros Oriental State University. All rights reserved.',
                'meta_description': 'NORSU Alumni Network - Connect with fellow graduates, access career opportunities, and stay updated with university news.',
                'meta_keywords': 'NORSU, alumni, university, graduates, network, education, Philippines'
            }
        )
        
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status} site configuration'))
    
    def _create_hero_section(self):
        hero_section, created = PageSection.objects.update_or_create(
            name='home_hero_section',
            defaults={
                'section_type': 'HERO',
                'title': 'Welcome to NORSU Alumni Network',
                'subtitle': 'Connect with fellow graduates, access exclusive resources, and advance your career',
                'content': 'Join our thriving community of NORSU graduates to expand your professional network, discover job opportunities, and stay connected with your alma mater.',
                'order': 1,
                'is_active': True
            }
        )
        
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status} hero section'))
    
    def _create_feature_section(self):
        feature_section, created = PageSection.objects.update_or_create(
            name='home_feature_section',
            defaults={
                'section_type': 'FEATURE',
                'title': 'Exclusive Benefits',
                'subtitle': 'Discover what our alumni network offers',
                'order': 2,
                'is_active': True
            }
        )
        
        # Create individual feature sections
        features = [
            {
                'name': 'feature_career_growth',
                'title': 'Career Growth',
                'content': 'Access exclusive job listings, career counseling, and professional development workshops.',
                'order': 1
            },
            {
                'name': 'feature_global_network',
                'title': 'Global Network',
                'content': 'Connect with alumni worldwide through our directory, groups, and networking events.',
                'order': 2
            },
            {
                'name': 'feature_mentorship',
                'title': 'Expert Mentorship',
                'content': 'Learn from experienced alumni through our structured mentorship program.',
                'order': 3
            },
            {
                'name': 'feature_events',
                'title': 'Premium Events',
                'content': 'Attend exclusive alumni gatherings, reunions, and professional conferences.',
                'order': 4
            }
        ]
        
        for feature in features:
            feature_item, created = PageSection.objects.update_or_create(
                name=feature['name'],
                defaults={
                    'section_type': 'FEATURE',
                    'title': feature['title'],
                    'content': feature['content'],
                    'order': feature['order'],
                    'is_active': True
                }
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{status} feature: {feature["title"]}'))
    
    def _create_testimonial_section(self):
        testimonial_section, created = PageSection.objects.update_or_create(
            name='home_testimonial_section',
            defaults={
                'section_type': 'TESTIMONIAL',
                'title': 'Alumni Voices',
                'subtitle': 'Hear what our graduates have to say',
                'order': 3,
                'is_active': True
            }
        )
        
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status} testimonial section'))
    
    def _create_cta_section(self):
        cta_section, created = PageSection.objects.update_or_create(
            name='home_cta_section',
            defaults={
                'section_type': 'CTA',
                'title': 'Join Our Growing Community',
                'content': 'Be part of the NORSU Alumni Network and connect with fellow graduates worldwide. Access exclusive opportunities, events, and resources designed for your professional growth.',
                'order': 4,
                'is_active': True
            }
        )
        
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status} CTA section'))
    
    def _create_testimonials(self):
        testimonials = [
            {
                'name': 'Maria Santos',
                'position': 'Software Engineer',
                'company': 'Tech Innovations Inc.',
                'graduation_year': 2018,
                'quote': 'The NORSU Alumni Network helped me land my dream job through their exclusive job board. The connections I\'ve made continue to be invaluable for my career growth.',
                'is_featured': True,
                'order': 1
            },
            {
                'name': 'Juan Dela Cruz',
                'position': 'Marketing Director',
                'company': 'Global Brands PH',
                'graduation_year': 2015,
                'quote': 'Being part of this network has opened doors I never thought possible. The mentorship program paired me with industry leaders who guided my career path.',
                'is_featured': True,
                'order': 2
            },
            {
                'name': 'Ana Reyes',
                'position': 'Healthcare Administrator',
                'company': 'Dumaguete Medical Center',
                'graduation_year': 2016,
                'quote': 'The professional development workshops offered through the alumni network have kept my skills current and competitive in the rapidly evolving healthcare industry.',
                'is_featured': False,
                'order': 3
            }
        ]
        
        for testimonial_data in testimonials:
            testimonial, created = Testimonial.objects.update_or_create(
                name=testimonial_data['name'],
                defaults={
                    'position': testimonial_data['position'],
                    'company': testimonial_data['company'],
                    'graduation_year': testimonial_data['graduation_year'],
                    'quote': testimonial_data['quote'],
                    'is_featured': testimonial_data['is_featured'],
                    'order': testimonial_data['order'],
                    'is_active': True
                }
            )
            
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{status} testimonial: {testimonial_data["name"]}'))
    
    def _create_staff_members(self):
        staff_members = [
            {
                'name': 'Dr. Carlos Mendoza',
                'position': 'Alumni Relations Director',
                'staff_type': 'LEADERSHIP',
                'department': 'Alumni Affairs Office',
                'bio': 'Dr. Mendoza has been leading the Alumni Relations Office since 2018. He is dedicated to strengthening connections between the university and its graduates.',
                'email': 'carlos.mendoza@norsu.edu.ph',
                'order': 1
            },
            {
                'name': 'Maria Reyes',
                'position': 'Career Services Coordinator',
                'staff_type': 'ADMIN',
                'department': 'Career Development Center',
                'bio': 'Maria oversees career counseling, job placement, and professional development programs for alumni.',
                'email': 'maria.reyes@norsu.edu.ph',
                'order': 2
            },
            {
                'name': 'John Santos',
                'position': 'Events Manager',
                'staff_type': 'ADMIN',
                'department': 'Alumni Affairs Office',
                'bio': 'John coordinates alumni gatherings, reunions, and networking events throughout the year.',
                'email': 'john.santos@norsu.edu.ph',
                'order': 3
            },
            {
                'name': 'Ana Rodriguez',
                'position': 'Alumni Database Manager',
                'staff_type': 'SUPPORT',
                'department': 'Information Technology Services',
                'bio': 'Ana maintains the alumni database and provides technical support for the alumni portal.',
                'email': 'ana.rodriguez@norsu.edu.ph',
                'order': 4
            }
        ]
        
        for staff_data in staff_members:
            staff, created = StaffMember.objects.update_or_create(
                name=staff_data['name'],
                defaults={
                    'position': staff_data['position'],
                    'staff_type': staff_data['staff_type'],
                    'department': staff_data['department'],
                    'bio': staff_data['bio'],
                    'email': staff_data['email'],
                    'order': staff_data['order'],
                    'is_active': True
                }
            )
            
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{status} staff member: {staff_data["name"]}'))