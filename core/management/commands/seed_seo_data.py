"""
Django management command to seed SEO configuration with default data.

This command populates PageSEO and OrganizationSchema models with production-ready
default data for the NORSU Alumni System. It can be run multiple times safely
using update_or_create logic.

Usage:
    python manage.py seed_seo_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models.seo import PageSEO, OrganizationSchema


class Command(BaseCommand):
    help = 'Seeds SEO configuration with default data for all major pages'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting SEO data seeding...'))
        self.stdout.write('')

        # ============================================================
        # PAGE SEO DATA
        # ============================================================
        PAGE_SEO_DATA = [
            {
                'page_path': '/',
                'meta_title': 'NORSU Alumni Network - Connect, Network, and Grow',
                'meta_description': 'Official alumni platform for Negros Oriental State University. Connect with fellow alumni, find mentors, discover jobs, and stay updated with events.',
                'meta_keywords': 'NORSU alumni, Negros Oriental State University, alumni network, alumni directory, NORSU graduates, alumni events',
                'sitemap_priority': 1.0,
                'sitemap_changefreq': 'daily',
                'is_active': True,
            },
            {
                'page_path': '/about/',
                'meta_title': 'About NORSU Alumni Network - Our Mission and Vision',
                'meta_description': 'Learn about NORSU Alumni Network, our mission to connect graduates worldwide, and how we support professional growth and community engagement.',
                'meta_keywords': 'about NORSU, NORSU mission, NORSU vision, alumni association, university history, NORSU establishment',
                'sitemap_priority': 0.9,
                'sitemap_changefreq': 'monthly',
                'is_active': True,
            },
            {
                'page_path': '/contact/',
                'meta_title': 'Contact Us - NORSU Alumni Affairs Office Information',
                'meta_description': 'Get in touch with NORSU Office of Alumni Affairs. Find contact details, office hours, and location information for support and inquiries.',
                'meta_keywords': 'contact NORSU, alumni affairs office, NORSU contact, alumni support, office hours, Dumaguete City',
                'sitemap_priority': 0.8,
                'sitemap_changefreq': 'monthly',
                'is_active': True,
            },
            {
                'page_path': '/alumni/',
                'meta_title': 'Alumni Directory - Find and Connect with NORSU Graduates',
                'meta_description': 'Search the NORSU alumni directory to find classmates and colleagues. Filter by graduation year, program, location, or industry to reconnect.',
                'meta_keywords': 'alumni directory, find alumni, NORSU graduates, search alumni, classmates, alumni search, batch mates',
                'sitemap_priority': 0.9,
                'sitemap_changefreq': 'daily',
                'is_active': True,
            },
            {
                'page_path': '/events/',
                'meta_title': 'Alumni Events - Reunions, Networking, and Homecoming',
                'meta_description': 'Discover upcoming NORSU alumni events including homecoming, reunions, networking sessions, and professional development opportunities.',
                'meta_keywords': 'alumni events, NORSU homecoming, alumni reunion, networking events, professional development, alumni gatherings',
                'sitemap_priority': 0.8,
                'sitemap_changefreq': 'weekly',
                'is_active': True,
            },
            {
                'page_path': '/jobs/',
                'meta_title': 'Job Board - Career Opportunities for NORSU Alumni',
                'meta_description': 'Explore exclusive job opportunities posted by and for NORSU alumni. Find your next career move or post openings for fellow graduates.',
                'meta_keywords': 'alumni jobs, career opportunities, job board, NORSU careers, employment, job postings, alumni hiring',
                'sitemap_priority': 0.9,
                'sitemap_changefreq': 'daily',
                'is_active': True,
            },
            {
                'page_path': '/mentorship/',
                'meta_title': 'Mentorship Program - Connect with Experienced Alumni',
                'meta_description': 'Join the NORSU mentorship program. Connect with experienced alumni mentors for career guidance or become a mentor to help fellow graduates.',
                'meta_keywords': 'mentorship program, alumni mentors, career guidance, professional mentoring, mentor matching, career advice',
                'sitemap_priority': 0.8,
                'sitemap_changefreq': 'weekly',
                'is_active': True,
            },
            {
                'page_path': '/groups/',
                'meta_title': 'Alumni Groups - Join Interest-Based Communities',
                'meta_description': 'Join or create NORSU alumni groups based on shared interests, professions, or locations. Build meaningful connections within specialized communities.',
                'meta_keywords': 'alumni groups, interest groups, professional groups, alumni communities, networking groups, batch groups',
                'sitemap_priority': 0.7,
                'sitemap_changefreq': 'weekly',
                'is_active': True,
            },
            {
                'page_path': '/donations/',
                'meta_title': 'Support NORSU - Donations and Giving Back Programs',
                'meta_description': 'Support NORSU through donations and giving back programs. Contribute to scholarships, infrastructure, and initiatives that benefit current students.',
                'meta_keywords': 'NORSU donations, alumni giving, scholarship fund, support NORSU, charitable giving, alumni contributions',
                'sitemap_priority': 0.7,
                'sitemap_changefreq': 'monthly',
                'is_active': True,
            },
            {
                'page_path': '/accounts/login/',
                'meta_title': 'Login - Access Your NORSU Alumni Network Account',
                'meta_description': 'Login to your NORSU Alumni Network account to connect with fellow graduates, access exclusive resources, and stay updated with alumni activities.',
                'meta_keywords': 'alumni login, member login, NORSU account, alumni portal, sign in, member access',
                'sitemap_priority': 0.6,
                'sitemap_changefreq': 'never',
                'is_active': True,
            },
            {
                'page_path': '/accounts/signup/',
                'meta_title': 'Join NORSU Alumni Network - Register Your Account',
                'meta_description': 'Register for the NORSU Alumni Network to connect with fellow graduates, access career resources, and participate in alumni events and programs.',
                'meta_keywords': 'alumni registration, join alumni network, sign up, create account, alumni membership, register',
                'sitemap_priority': 0.7,
                'sitemap_changefreq': 'never',
                'is_active': True,
            },
        ]

        # ============================================================
        # ORGANIZATION SCHEMA DATA
        # ============================================================
        ORGANIZATION_SCHEMA_DATA = {
            'name': 'Negros Oriental State University Alumni Network',
            'logo': 'https://norsu-alumni.edu.ph/static/images/norsu-logo.png',
            'url': 'https://norsu-alumni.edu.ph',
            'telephone': '+63-35-422-6002',
            'email': 'alumni@norsu.edu.ph',
            'street_address': 'Kagawasan, Ave. Rizal',
            'address_locality': 'Dumaguete City',
            'address_region': 'Negros Oriental',
            'postal_code': '6200',
            'address_country': 'PH',
            'is_active': True,
        }

        # ============================================================
        # EXECUTION
        # ============================================================
        
        created_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                # Seed PageSEO entries
                self.stdout.write(self.style.HTTP_INFO('[*] Seeding Page SEO entries...'))
                self.stdout.write('-' * 60)
                
                for seo_data in PAGE_SEO_DATA:
                    page_path = seo_data['page_path']
                    obj, created = PageSEO.objects.update_or_create(
                        page_path=page_path,
                        defaults=seo_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  [+] Created: {page_path}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  [~] Updated: {page_path}')
                        )
                
                # Seed OrganizationSchema
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO('[*] Seeding Organization Schema...'))
                self.stdout.write('-' * 60)
                
                org_schema, created = OrganizationSchema.objects.update_or_create(
                    name=ORGANIZATION_SCHEMA_DATA['name'],
                    defaults=ORGANIZATION_SCHEMA_DATA
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  [+] Created: {org_schema.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  [~] Updated: {org_schema.name}')
                    )
                
                # Summary
                self.stdout.write('')
                self.stdout.write('=' * 60)
                self.stdout.write(self.style.HTTP_INFO('[*] SEEDING SUMMARY'))
                self.stdout.write('=' * 60)
                self.stdout.write(
                    self.style.SUCCESS(f'  [+] Created:  {created_count} record(s)')
                )
                self.stdout.write(
                    self.style.WARNING(f'  [~] Updated:  {updated_count} record(s)')
                )
                self.stdout.write(
                    f'  [*] Total:    {created_count + updated_count} record(s)'
                )
                self.stdout.write('=' * 60)
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('[OK] SEO data seeding completed successfully!')
                )
                
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(
                self.style.ERROR(f'✗ Error during seeding: {str(e)}')
            )
            raise
