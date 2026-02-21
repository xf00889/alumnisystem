"""
Django management command to seed CMS with default organizational data.

This command populates all CMS models with production-ready default data
from the NORSU Office of Alumni Affairs. It can be run multiple times safely
using update_or_create logic that automatically updates existing records.

Usage:
    python manage.py seed_cms_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from cms.models import (
    SiteConfig,
    AboutPageConfig,
    Feature,
    Testimonial,
    StaffMember,
    TimelineItem,
    ContactInfo,
    FAQ,
    AlumniStatistic,
)


class Command(BaseCommand):
    help = 'Seeds the CMS with default organizational data from NORSU Alumni Affairs (automatically updates existing records)'

    def add_arguments(self, parser):
        # Removed --force flag as update behavior is now default
        pass

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting CMS data seeding...'))
        self.stdout.write(self.style.WARNING('Note: Existing records will be updated with new data'))
        self.stdout.write('')

        # ============================================================
        # DATA DEFINITIONS
        # ============================================================
        
        # ------------------------------------------------------------
        # 1. SITE CONFIGURATION DATA (Singleton)
        # Global site settings including branding, contact info, and social media links
        # ------------------------------------------------------------
        SITE_CONFIG_DATA = {
            'site_name': 'NORSU Alumni Network',
            'site_tagline': 'Connecting Norsunians Worldwide',
            'contact_email': 'alumni@norsu.edu.ph',
            'contact_phone': '+63 35 422 6002',
            'contact_address': '''Office of Alumni Affairs
Negros Oriental State University
Kagawasan, Ave. Rizal
Dumaguete City, 6200
Negros Oriental, Philippines''',
            'facebook_url': 'https://www.facebook.com/NORSUAlumniAffairs',
            'twitter_url': '',
            'linkedin_url': '',
            'instagram_url': '',
            'youtube_url': '',
            'signup_button_text': 'Join the Network',
            'login_button_text': 'Member Login',
        }

        # ------------------------------------------------------------
        # 2. ABOUT PAGE CONFIGURATION DATA (Singleton)
        # University information, mission, vision, and about page content
        # ------------------------------------------------------------
        ABOUT_PAGE_CONFIG_DATA = {
            'university_name': 'Negros Oriental State University',
            'university_short_name': 'NORSU',
            'university_description': '''Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services.''',
            'university_extended_description': '''Established in 2004 through the merger of several educational institutions, NORSU has grown to become a leading center of learning in the Visayas region. Our university is dedicated to developing competent professionals who contribute to national development and global competitiveness.''',
            'establishment_year': '2004',
            'mission': '''To provide quality and relevant education through instruction, research, extension, and production services for the holistic development of individuals and communities towards a progressive society.''',
            'vision': '''A premier state university in the Asia-Pacific region recognized for excellence in instruction, research, extension, and production that produces globally competitive graduates and empowered communities.''',
            'about_page_title': 'About NORSU Alumni Network',
            'about_page_subtitle': 'Learn more about our university, mission, and the people behind our alumni community',
        }

        # ------------------------------------------------------------
        # 3. FEATURES DATA
        # Platform capabilities and features displayed on homepage
        # ------------------------------------------------------------
        FEATURES_DATA = [
            {
                'title': 'Alumni Directory',
                'content': 'Connect with fellow Norsunians through our comprehensive alumni directory. Search by batch, program, or location to find and reconnect with classmates.',
                'icon': 'fas fa-users',
                'icon_class': 'primary',
                'link_url': '',
                'link_text': 'Browse Directory',
                'order': 1,
                'is_active': True,
            },
            {
                'title': 'Events & Reunions',
                'content': 'Stay updated on upcoming alumni events, homecoming celebrations, and networking opportunities. Register and participate in activities that strengthen our community.',
                'icon': 'fas fa-calendar-alt',
                'icon_class': 'success',
                'link_url': '',
                'link_text': 'View Events',
                'order': 2,
                'is_active': True,
            },
            {
                'title': 'Career Opportunities',
                'content': 'Access exclusive job postings and career resources. Post opportunities or find your next career move within the NORSU alumni network.',
                'icon': 'fas fa-briefcase',
                'icon_class': 'info',
                'link_url': '',
                'link_text': 'Explore Jobs',
                'order': 3,
                'is_active': True,
            },
            {
                'title': 'Mentorship Program',
                'content': 'Give back by mentoring current students or recent graduates. Connect with experienced alumni who can guide your professional journey.',
                'icon': 'fas fa-hands-helping',
                'icon_class': 'warning',
                'link_url': '',
                'link_text': 'Learn More',
                'order': 4,
                'is_active': True,
            },
            {
                'title': 'Alumni Groups',
                'content': 'Join or create alumni groups based on shared interests, professions, or locations. Build meaningful connections within specialized communities.',
                'icon': 'fas fa-user-friends',
                'icon_class': 'danger',
                'link_url': '',
                'link_text': 'Join Groups',
                'order': 5,
                'is_active': True,
            },
        ]

        # ------------------------------------------------------------
        # 4. TESTIMONIALS DATA
        # Alumni testimonials displayed on homepage
        # ------------------------------------------------------------
        TESTIMONIALS_DATA = [
            {
                'name': 'Maria Santos',
                'position': 'Software Engineer',
                'company': 'Tech Solutions Inc.',
                'quote': 'The NORSU Alumni Network has been instrumental in my career growth. Through the platform, I connected with mentors who guided me and found amazing job opportunities. Proud to be a Norsunian!',
                'order': 1,
                'is_active': True,
            },
            {
                'name': 'Juan dela Cruz',
                'position': 'Business Owner',
                'company': 'JDC Enterprises',
                'quote': 'Being part of this network opened doors I never imagined. The connections I made here led to business partnerships and lifelong friendships. NORSU truly prepares us for success.',
                'order': 2,
                'is_active': True,
            },
            {
                'name': 'Dr. Ana Reyes',
                'position': 'Medical Director',
                'company': 'City General Hospital',
                'quote': 'The alumni community continues to support each other long after graduation. I found my first job through this network and now I mentor young graduates. It\'s a cycle of giving back.',
                'order': 3,
                'is_active': True,
            },
        ]

        # ------------------------------------------------------------
        # 5. STAFF MEMBERS DATA
        # Office of Alumni Affairs staff members
        # ------------------------------------------------------------
        STAFF_MEMBERS_DATA = [
            {
                'name': 'Dr. Roberto Garcia',
                'position': 'Director',
                'department': 'Office of Alumni Affairs',
                'bio': 'Dr. Garcia leads the Office of Alumni Affairs with over 15 years of experience in alumni relations and community engagement. He is dedicated to strengthening the bond between NORSU and its graduates.',
                'email': 'roberto.garcia@norsu.edu.ph',
                'order': 1,
                'is_active': True,
            },
            {
                'name': 'Ms. Linda Fernandez',
                'position': 'Alumni Relations Coordinator',
                'department': 'Office of Alumni Affairs',
                'bio': 'Ms. Fernandez manages alumni engagement programs and coordinates events. She ensures that alumni stay connected and informed about university activities and opportunities.',
                'email': 'linda.fernandez@norsu.edu.ph',
                'order': 2,
                'is_active': True,
            },
            {
                'name': 'Mr. Carlos Mendoza',
                'position': 'Database Administrator',
                'department': 'Office of Alumni Affairs',
                'bio': 'Mr. Mendoza maintains the alumni database and provides technical support for the network platform. He ensures data accuracy and system reliability.',
                'email': 'carlos.mendoza@norsu.edu.ph',
                'order': 3,
                'is_active': True,
            },
        ]

        # ------------------------------------------------------------
        # 6. TIMELINE ITEMS DATA
        # Key organizational milestones and history
        # ------------------------------------------------------------
        TIMELINE_ITEMS_DATA = [
            {
                'year': '2004',
                'title': 'NORSU Established',
                'description': 'Negros Oriental State University was established through the merger of several educational institutions, marking the beginning of a new era in higher education in the region.',
                'icon': 'fas fa-university',
                'order': 1,
                'is_active': True,
            },
            {
                'year': '2010',
                'title': 'First Alumni Homecoming',
                'description': 'The inaugural alumni homecoming brought together hundreds of graduates, establishing a tradition of reconnection and celebration.',
                'icon': 'fas fa-home',
                'order': 2,
                'is_active': True,
            },
            {
                'year': '2015',
                'title': 'Alumni Association Formed',
                'description': 'The official NORSU Alumni Association was established to formalize alumni engagement and support university development initiatives.',
                'icon': 'fas fa-handshake',
                'order': 3,
                'is_active': True,
            },
            {
                'year': '2020',
                'title': 'Digital Network Launch',
                'description': 'The NORSU Alumni Network platform was launched, providing digital tools for alumni to connect, collaborate, and support each other globally.',
                'icon': 'fas fa-globe',
                'order': 4,
                'is_active': True,
            },
            {
                'year': '2024',
                'title': '20th Anniversary Celebration',
                'description': 'NORSU celebrates 20 years of excellence with over 50,000 alumni worldwide contributing to various fields and industries.',
                'icon': 'fas fa-trophy',
                'order': 5,
                'is_active': True,
            },
        ]

        # ------------------------------------------------------------
        # 7. CONTACT INFORMATION DATA
        # Contact details for the Office of Alumni Affairs
        # ------------------------------------------------------------
        CONTACT_INFO_DATA = [
            {
                'contact_type': 'phone',
                'value': '+63 35 422 6002',
                'is_primary': True,
                'order': 1,
                'is_active': True,
            },
            {
                'contact_type': 'email',
                'value': 'alumni@norsu.edu.ph',
                'is_primary': True,
                'order': 2,
                'is_active': True,
            },
            {
                'contact_type': 'address',
                'value': '''Office of Alumni Affairs
Negros Oriental State University
Kagawasan, Ave. Rizal
Dumaguete City, 6200
Negros Oriental, Philippines''',
                'is_primary': True,
                'order': 3,
                'is_active': True,
            },
            {
                'contact_type': 'hours',
                'value': '''Monday - Friday: 8:00 AM - 5:00 PM
Saturday: 8:00 AM - 12:00 PM
Sunday: Closed''',
                'is_primary': False,
                'order': 4,
                'is_active': True,
            },
        ]

        # ------------------------------------------------------------
        # 8. FAQ DATA
        # Frequently asked questions about the alumni network
        # ------------------------------------------------------------
        FAQ_DATA = [
            {
                'question': 'How do I register for the NORSU Alumni Network?',
                'answer': 'Click on the "Join the Network" button on the homepage and fill out the registration form with your alumni information. You will need to provide your student ID number and graduation year for verification.',
                'order': 1,
                'is_active': True,
            },
            {
                'question': 'Is there a membership fee?',
                'answer': 'No, membership in the NORSU Alumni Network is completely free for all NORSU graduates. We believe in keeping our community accessible to everyone.',
                'order': 2,
                'is_active': True,
            },
            {
                'question': 'How can I update my profile information?',
                'answer': 'Log in to your account and navigate to your profile page. Click on "Edit Profile" to update your personal information, contact details, and professional background.',
                'order': 3,
                'is_active': True,
            },
            {
                'question': 'Can I post job opportunities on the platform?',
                'answer': 'Yes! Alumni can post job opportunities through the Jobs section. Simply log in, go to the Jobs page, and click "Post a Job" to share opportunities with fellow Norsunians.',
                'order': 4,
                'is_active': True,
            },
            {
                'question': 'How do I find classmates from my batch?',
                'answer': 'Use the Alumni Directory search feature to filter by graduation year, program, or campus. You can also join your batch-specific alumni group to connect with classmates.',
                'order': 5,
                'is_active': True,
            },
            {
                'question': 'What events are organized for alumni?',
                'answer': 'We organize various events including annual homecoming, professional networking sessions, career fairs, and regional meetups. Check the Events page regularly for upcoming activities.',
                'order': 6,
                'is_active': True,
            },
            {
                'question': 'How can I contribute to the university?',
                'answer': 'There are many ways to give back: mentor current students, participate in career talks, donate to scholarship funds, or volunteer for alumni events. Visit the Donations page to learn more.',
                'order': 7,
                'is_active': True,
            },
            {
                'question': 'Who do I contact for technical support?',
                'answer': 'For technical issues with the platform, please email alumni@norsu.edu.ph or call +63 35 422 6002 during office hours. Our technical team will assist you promptly.',
                'order': 8,
                'is_active': True,
            },
        ]

        # ------------------------------------------------------------
        # 9. ALUMNI STATISTICS DATA
        # Key metrics about the alumni network
        # ------------------------------------------------------------
        ALUMNI_STATISTICS_DATA = [
            {
                'statistic_type': 'alumni_members',
                'value': '50,000+',
                'label': 'Alumni Members',
                'icon': 'fas fa-users',
                'icon_color': '#007bff',
                'order': 1,
                'is_active': True,
            },
            {
                'statistic_type': 'alumni_groups',
                'value': '150+',
                'label': 'Alumni Groups',
                'icon': 'fas fa-user-friends',
                'icon_color': '#28a745',
                'order': 2,
                'is_active': True,
            },
            {
                'statistic_type': 'annual_events',
                'value': '25+',
                'label': 'Annual Events',
                'icon': 'fas fa-calendar-check',
                'icon_color': '#ffc107',
                'order': 3,
                'is_active': True,
            },
            {
                'statistic_type': 'job_opportunities',
                'value': '500+',
                'label': 'Job Opportunities Posted',
                'icon': 'fas fa-briefcase',
                'icon_color': '#17a2b8',
                'order': 4,
                'is_active': True,
            },
            {
                'statistic_type': 'countries',
                'value': '30+',
                'label': 'Countries Represented',
                'icon': 'fas fa-globe-americas',
                'icon_color': '#6f42c1',
                'order': 5,
                'is_active': True,
            },
            {
                'statistic_type': 'mentors',
                'value': '200+',
                'label': 'Active Mentors',
                'icon': 'fas fa-chalkboard-teacher',
                'icon_color': '#fd7e14',
                'order': 6,
                'is_active': True,
            },
        ]

        # ------------------------------------------------------------
        # 10. PAGE SECTIONS DATA
        # ============================================================
        # MAIN EXECUTION FLOW
        # ============================================================
        
        import time
        start_time = time.time()
        
        # Track overall results
        overall_results = {
            'total_created': 0,
            'total_updated': 0,
            'total_skipped': 0,
            'errors': [],
        }

        try:
            # Seed singleton models first
            self.stdout.write(self.style.HTTP_INFO('\n[*] Seeding Singleton Models...'))
            self.stdout.write('-' * 60)
            
            # 1. Seed SiteConfig
            try:
                _, created = self.seed_with_transaction(
                    self.seed_singleton_model,
                    SiteConfig,
                    SITE_CONFIG_DATA
                )
                if created:
                    overall_results['total_created'] += 1
                else:
                    overall_results['total_updated'] += 1
            except Exception as e:
                overall_results['errors'].append(f'SiteConfig: {str(e)}')
            
            # 2. Seed AboutPageConfig
            try:
                _, created = self.seed_with_transaction(
                    self.seed_singleton_model,
                    AboutPageConfig,
                    ABOUT_PAGE_CONFIG_DATA
                )
                if created:
                    overall_results['total_created'] += 1
                else:
                    overall_results['total_updated'] += 1
            except Exception as e:
                overall_results['errors'].append(f'AboutPageConfig: {str(e)}')
            
            # Seed multiple record models
            self.stdout.write(self.style.HTTP_INFO('\n[*] Seeding Multiple Record Models...'))
            self.stdout.write('-' * 60)
            
            # 3. Seed Features
            try:
                stats = self.seed_with_transaction(
                    self.seed_multiple_records,
                    Feature,
                    FEATURES_DATA,
                    ['title']
                )
                overall_results['total_created'] += stats['created']
                overall_results['total_updated'] += stats['updated']
                overall_results['total_skipped'] += stats['skipped']
            except Exception as e:
                overall_results['errors'].append(f'Feature: {str(e)}')
            
            # 4. Seed Testimonials
            try:
                stats = self.seed_with_transaction(
                    self.seed_multiple_records,
                    Testimonial,
                    TESTIMONIALS_DATA,
                    ['name', 'position']
                )
                overall_results['total_created'] += stats['created']
                overall_results['total_updated'] += stats['updated']
                overall_results['total_skipped'] += stats['skipped']
            except Exception as e:
                overall_results['errors'].append(f'Testimonial: {str(e)}')
            
            # 5. Seed StaffMembers
            try:
                stats = self.seed_with_transaction(
                    self.seed_multiple_records,
                    StaffMember,
                    STAFF_MEMBERS_DATA,
                    ['name', 'position']
                )
                overall_results['total_created'] += stats['created']
                overall_results['total_updated'] += stats['updated']
                overall_results['total_skipped'] += stats['skipped']
            except Exception as e:
                overall_results['errors'].append(f'StaffMember: {str(e)}')
            
            # 6. Seed TimelineItems
            try:
                stats = self.seed_with_transaction(
                    self.seed_multiple_records,
                    TimelineItem,
                    TIMELINE_ITEMS_DATA,
                    ['year', 'title']
                )
                overall_results['total_created'] += stats['created']
                overall_results['total_updated'] += stats['updated']
                overall_results['total_skipped'] += stats['skipped']
            except Exception as e:
                overall_results['errors'].append(f'TimelineItem: {str(e)}')
            
            # 7. Seed ContactInfo
            try:
                stats = self.seed_with_transaction(
                    self.seed_multiple_records,
                    ContactInfo,
                    CONTACT_INFO_DATA,
                    ['contact_type', 'value']
                )
                overall_results['total_created'] += stats['created']
                overall_results['total_updated'] += stats['updated']
                overall_results['total_skipped'] += stats['skipped']
            except Exception as e:
                overall_results['errors'].append(f'ContactInfo: {str(e)}')
            
            # 8. Seed FAQs
            try:
                stats = self.seed_with_transaction(
                    self.seed_multiple_records,
                    FAQ,
                    FAQ_DATA,
                    ['question']
                )
                overall_results['total_created'] += stats['created']
                overall_results['total_updated'] += stats['updated']
                overall_results['total_skipped'] += stats['skipped']
            except Exception as e:
                overall_results['errors'].append(f'FAQ: {str(e)}')
            
            # 9. Seed AlumniStatistics
            try:
                stats = self.seed_with_transaction(
                    self.seed_multiple_records,
                    AlumniStatistic,
                    ALUMNI_STATISTICS_DATA,
                    ['statistic_type']
                )
                overall_results['total_created'] += stats['created']
                overall_results['total_updated'] += stats['updated']
                overall_results['total_skipped'] += stats['skipped']
            except Exception as e:
                overall_results['errors'].append(f'AlumniStatistic: {str(e)}')
            
            # Calculate execution time
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Generate and display summary report
            self.generate_summary_report(overall_results, execution_time)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n[X] Critical error during seeding: {str(e)}'
                )
            )
            raise

    def generate_summary_report(self, results, execution_time):
        """
        Generates and displays a comprehensive summary report of the seeding operation.
        
        Shows statistics about created and updated records, along with
        any errors encountered. Uses color-coded output for better readability.
        
        Args:
            results: Dictionary containing seeding statistics
            execution_time: Total time taken for seeding operation (in seconds)
        """
        self.stdout.write('\n')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.HTTP_INFO('[*] SEEDING SUMMARY REPORT'))
        self.stdout.write('=' * 60)
        
        # Display mode
        self.stdout.write(f'\nMode: {self.style.WARNING("UPDATE MODE (Overwrite existing)")}')
        
        # Display statistics
        self.stdout.write('\n[*] Statistics:')
        self.stdout.write('-' * 60)
        
        if results['total_created'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'  [+] Created:  {results["total_created"]} record(s)'
                )
            )
        
        if results['total_updated'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'  [~] Updated:  {results["total_updated"]} record(s)'
                )
            )
        
        if results['total_skipped'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'  [-] Skipped:  {results["total_skipped"]} record(s)'
                )
            )
        
        # Display errors if any
        if results['errors']:
            self.stdout.write('\n[!] Errors:')
            self.stdout.write('-' * 60)
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f'  [X] {error}'))
        
        # Display execution time
        self.stdout.write('\n[*] Performance:')
        self.stdout.write('-' * 60)
        self.stdout.write(f'  Execution time: {execution_time:.2f} seconds')
        
        # Display final status
        self.stdout.write('\n')
        self.stdout.write('=' * 60)
        
        if results['errors']:
            self.stdout.write(
                self.style.WARNING(
                    '[!] Seeding completed with errors. Please review the error messages above.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '[OK] CMS data seeding completed successfully!'
                )
            )
        
        self.stdout.write('=' * 60)
        self.stdout.write('')

    # ============================================================
    # CORE SEEDING LOGIC FUNCTIONS
    # ============================================================

    def seed_singleton_model(self, model_class, data):
        """
        Seeds a singleton model (models that should have only one instance).
        
        Uses update_or_create() to ensure idempotent behavior. Always updates
        the singleton instance with the latest data, creating it if it doesn't exist.
        
        Args:
            model_class: The Django model class to seed
            data: Dictionary of field values for the model
            force: Deprecated parameter, kept for compatibility
            
        Returns:
            tuple: (instance, created) where created is True if new instance
        
        Raises:
            ValidationError: If data fails model validation
            DatabaseError: If database operation fails
        """
        model_name = model_class.__name__
        
        try:
            # Validate data by creating a temporary instance
            temp_instance = model_class(**data)
            temp_instance.full_clean()  # Validates all fields
            
            # Get the first instance (singleton pattern)
            existing_instance = model_class.objects.first()
            
            if existing_instance:
                # Update existing instance using update_or_create
                # For singleton, we use the pk as the lookup
                instance, created = model_class.objects.update_or_create(
                    pk=existing_instance.pk,
                    defaults=data
                )
                self.stdout.write(
                    self.style.WARNING(
                        f'  [~] Updated {model_name}'
                    )
                )
                return instance, False
            else:
                # Create new instance
                instance = model_class.objects.create(**data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [+] Created {model_name}'
                    )
                )
                return instance, True
                
        except Exception as e:
            error_msg = f'  [X] Error seeding {model_name}: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            raise

    def seed_multiple_records(self, model_class, data_list, unique_fields, force=False):
        """
        Seeds multiple records for a model with duplicate checking.
        
        Uses update_or_create() for each record to ensure idempotent behavior.
        Always updates existing records with new data instead of skipping them.
        
        Args:
            model_class: The Django model class to seed
            data_list: List of dictionaries, each containing field values
            unique_fields: List of field names that uniquely identify a record
            force: Deprecated parameter, kept for compatibility
            
        Returns:
            dict: Statistics with 'created', 'updated', and 'skipped' counts
        
        Raises:
            ValidationError: If any data fails model validation
            DatabaseError: If database operation fails
        """
        model_name = model_class.__name__
        stats = {'created': 0, 'updated': 0, 'skipped': 0}
        
        try:
            for data in data_list:
                # Build lookup dictionary using unique fields
                lookup = {field: data[field] for field in unique_fields if field in data}
                
                # Validate data by creating a temporary instance
                temp_instance = model_class(**data)
                temp_instance.full_clean()  # Validates all fields
                
                # Always use update_or_create to insert or update
                # Separate lookup fields from defaults
                defaults = {k: v for k, v in data.items() if k not in unique_fields}
                instance, created = model_class.objects.update_or_create(
                    **lookup,
                    defaults=defaults
                )
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
            
            # Output summary
            if stats['created'] > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [+] Created {stats["created"]} {model_name} record(s)'
                    )
                )
            if stats['updated'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [~] Updated {stats["updated"]} {model_name} record(s)'
                    )
                )
            if stats['skipped'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [-] Skipped {stats["skipped"]} {model_name} record(s) (already exist)'
                    )
                )
            
            return stats
            
        except Exception as e:
            error_msg = f'  [X] Error seeding {model_name}: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            raise

    def seed_with_transaction(self, seeding_function, *args, **kwargs):
        """
        Wraps a seeding operation in a database transaction.
        
        Ensures atomicity - either all operations succeed or all are rolled back.
        Provides detailed error logging with field-specific information.
        
        Args:
            seeding_function: The function to execute within transaction
            *args: Positional arguments to pass to seeding_function
            **kwargs: Keyword arguments to pass to seeding_function
            
        Returns:
            The return value from seeding_function
            
        Raises:
            Exception: Re-raises any exception after logging and rollback
        """
        try:
            with transaction.atomic():
                result = seeding_function(*args, **kwargs)
                return result
        except Exception as e:
            # Log detailed error information
            self.stdout.write(
                self.style.ERROR(
                    f'\n[X] Transaction failed and rolled back: {str(e)}'
                )
            )
            # Re-raise to allow caller to handle
            raise
