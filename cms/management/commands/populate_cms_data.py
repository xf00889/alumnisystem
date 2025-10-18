from django.core.management.base import BaseCommand
from django.utils import timezone
from cms.models import (
    SiteConfig, PageSection, Feature, Testimonial, 
    StaffMember, TimelineItem, ContactInfo, FAQ,
    AboutPageConfig, AlumniStatistic
)


class Command(BaseCommand):
    help = 'Populate CMS with default content'

    def handle(self, *args, **options):
        self.stdout.write('Creating default CMS content...')
        
        # Create SiteConfig
        site_config, created = SiteConfig.objects.get_or_create(
            defaults={
                'site_name': 'NORSU Alumni Network',
                'site_tagline': 'Connect. Grow. Succeed.',
                'contact_email': 'alumni@norsu.edu.ph',
                'contact_phone': '+63 35 422 6002',
                'contact_address': 'Negros Oriental State University\nKagawasan, Ave. Rizal\nDumaguete City, 6200\nNegros Oriental, Philippines',
                'facebook_url': 'https://facebook.com/norsuofficial',
                'twitter_url': 'https://twitter.com/norsuofficial',
                'linkedin_url': 'https://linkedin.com/school/norsuofficial',
                'instagram_url': 'https://instagram.com/norsuofficial',
                'youtube_url': 'https://youtube.com/norsuofficial',
                'signup_button_text': 'Join the Network',
                'login_button_text': 'Member Login',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created SiteConfig'))
        else:
            self.stdout.write(self.style.WARNING('SiteConfig already exists'))

        # Create Page Sections
        page_sections_data = [
            {
                'section_type': 'hero',
                'title': 'Connect. Grow. Succeed.',
                'subtitle': 'Join 5,000+ NORSU alumni advancing their careers through meaningful professional connections and exclusive opportunities.',
                'content': '',
                'order': 1,
            },
            {
                'section_type': 'features',
                'title': 'Your Professional Success Platform',
                'subtitle': 'Four key benefits that accelerate your career growth and expand your professional network.',
                'content': '',
                'order': 2,
            },
            {
                'section_type': 'testimonials',
                'title': 'Alumni Achievements',
                'subtitle': 'Real career transformations through our professional network.',
                'content': '',
                'order': 3,
            },
            {
                'section_type': 'cta',
                'title': 'Start Your Success Story',
                'subtitle': 'Join the most powerful professional network of NORSU graduates. Access career-changing opportunities, industry insights, and lifelong connections.',
                'content': 'Join the most powerful professional network of NORSU graduates. Access career-changing opportunities, industry insights, and lifelong connections.',
                'order': 4,
            },
        ]

        for section_data in page_sections_data:
            section, created = PageSection.objects.get_or_create(
                section_type=section_data['section_type'],
                defaults=section_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created {section_data["section_type"]} section'))
            else:
                self.stdout.write(self.style.WARNING(f'{section_data["section_type"]} section already exists'))

        # Create Features
        features_data = [
            {
                'title': 'Career Growth',
                'content': '• Exclusive job opportunities<br>• Professional development resources<br>• Industry leader connections',
                'icon': 'fas fa-rocket',
                'icon_class': 'growth',
                'link_url': '/accounts/login/',
                'link_text': 'Explore Opportunities',
                'order': 1,
            },
            {
                'title': 'Global Network',
                'content': '• 5,000+ active alumni worldwide<br>• 25+ industry groups<br>• Fortune 500 connections',
                'icon': 'fas fa-network-wired',
                'icon_class': 'networking',
                'link_url': '/accounts/login/',
                'link_text': 'Join Network',
                'order': 2,
            },
            {
                'title': 'Expert Mentorship',
                'content': '• Personalized career guidance<br>• Experienced professional mentors<br>• Strategic career planning',
                'icon': 'fas fa-lightbulb',
                'icon_class': 'info',
                'link_url': '/accounts/login/',
                'link_text': 'Find Mentors',
                'order': 3,
            },
            {
                'title': 'Premium Events',
                'content': '• Exclusive networking events<br>• Industry conferences<br>• Professional gatherings',
                'icon': 'fas fa-trophy',
                'icon_class': 'achievement',
                'link_url': '/accounts/login/',
                'link_text': 'View Events',
                'order': 4,
            },
        ]

        for feature_data in features_data:
            feature, created = Feature.objects.get_or_create(
                title=feature_data['title'],
                defaults=feature_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created feature: {feature_data["title"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Feature "{feature_data["title"]}" already exists'))

        # Create Testimonials
        testimonials_data = [
            {
                'name': 'Maria Santos',
                'position': 'Software Engineer',
                'company': 'Microsoft',
                'quote': 'Connected with a mentor who helped me transition into tech and land my dream job at Microsoft.',
                'order': 1,
            },
            {
                'name': 'John Dela Cruz',
                'position': 'CEO',
                'company': 'TechStart Philippines',
                'quote': 'Alumni connections helped me secure funding and grow my startup from idea to successful business.',
                'order': 2,
            },
            {
                'name': 'Ana Rodriguez',
                'position': 'Marketing Director',
                'company': 'Globe Telecom',
                'quote': 'Professional development resources and networking events advanced my career by two positions in one year.',
                'order': 3,
            },
        ]

        for testimonial_data in testimonials_data:
            testimonial, created = Testimonial.objects.get_or_create(
                name=testimonial_data['name'],
                defaults=testimonial_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created testimonial: {testimonial_data["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Testimonial "{testimonial_data["name"]}" already exists'))

        # Create Staff Members
        staff_data = [
            {
                'name': 'Dr. Maria Santos',
                'position': 'Alumni Relations Director',
                'department': 'Office of Alumni Affairs',
                'bio': 'Leading alumni engagement and relationship building initiatives.',
                'email': 'maria.santos@norsu.edu.ph',
                'order': 1,
            },
            {
                'name': 'Prof. Juan Dela Cruz',
                'position': 'Alumni Engagement Coordinator',
                'department': 'Office of Alumni Affairs',
                'bio': 'Coordinating alumni events and professional development programs.',
                'email': 'juan.delacruz@norsu.edu.ph',
                'order': 2,
            },
            {
                'name': 'Ms. Ana Rodriguez',
                'position': 'Alumni Database Manager',
                'department': 'Information Technology Services',
                'bio': 'Managing alumni data and digital platform operations.',
                'email': 'ana.rodriguez@norsu.edu.ph',
                'order': 3,
            },
        ]

        for staff_data_item in staff_data:
            staff, created = StaffMember.objects.get_or_create(
                name=staff_data_item['name'],
                defaults=staff_data_item
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created staff member: {staff_data_item["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Staff member "{staff_data_item["name"]}" already exists'))

        # Create Timeline Items
        timeline_data = [
            {
                'year': '2004',
                'title': 'University Establishment',
                'description': 'NORSU was established through the merger of several educational institutions in Negros Oriental.',
                'icon': 'fas fa-university',
                'order': 1,
            },
            {
                'year': '2010',
                'title': 'Alumni Association Formation',
                'description': 'The official NORSU Alumni Association was formed to strengthen connections among graduates.',
                'icon': 'fas fa-users',
                'order': 2,
            },
            {
                'year': '2020',
                'title': 'Digital Transformation',
                'description': 'Launch of the digital alumni network platform to enhance connectivity and engagement.',
                'icon': 'fas fa-laptop',
                'order': 3,
            },
            {
                'year': '2024',
                'title': 'Platform Enhancement',
                'description': 'Major upgrade of the alumni system with new features for career services and mentorship programs.',
                'icon': 'fas fa-rocket',
                'order': 4,
            },
        ]

        for timeline_item_data in timeline_data:
            timeline_item, created = TimelineItem.objects.get_or_create(
                year=timeline_item_data['year'],
                title=timeline_item_data['title'],
                defaults=timeline_item_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created timeline item: {timeline_item_data["year"]} - {timeline_item_data["title"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Timeline item "{timeline_item_data["year"]} - {timeline_item_data["title"]}" already exists'))

        # Create Contact Information
        contact_data = [
            {
                'contact_type': 'address',
                'value': 'Negros Oriental State University\nKagawasan, Ave. Rizal\nDumaguete City, 6200\nNegros Oriental, Philippines',
                'is_primary': True,
                'order': 1,
            },
            {
                'contact_type': 'phone',
                'value': '+63 35 422 6002\n+63 35 225 2376',
                'is_primary': True,
                'order': 2,
            },
            {
                'contact_type': 'email',
                'value': 'alumni@norsu.edu.ph\ninfo@norsu.edu.ph',
                'is_primary': True,
                'order': 3,
            },
            {
                'contact_type': 'hours',
                'value': 'Monday - Friday: 8:00 AM - 5:00 PM\nSaturday: 8:00 AM - 12:00 PM\nSunday: Closed',
                'is_primary': True,
                'order': 4,
            },
        ]

        for contact_item_data in contact_data:
            contact_info, created = ContactInfo.objects.get_or_create(
                contact_type=contact_item_data['contact_type'],
                is_primary=True,
                defaults=contact_item_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created contact info: {contact_item_data["contact_type"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Contact info "{contact_item_data["contact_type"]}" already exists'))

        # Create FAQs
        faq_data = [
            {
                'question': 'How do I register for the alumni network?',
                'answer': 'Click on the "Sign Up" button in the navigation menu and fill out the registration form with your details. You\'ll need to provide your graduation year, course, and other relevant information for verification.',
                'order': 1,
            },
            {
                'question': 'How can I update my profile information?',
                'answer': 'After logging in, go to your profile page where you can edit your personal information, contact details, professional background, and other profile settings.',
                'order': 2,
            },
            {
                'question': 'How do I find and connect with other alumni?',
                'answer': 'Use the Alumni Directory to search for classmates and colleagues. You can filter by graduation year, course, location, or industry. Send connection requests to build your professional network.',
                'order': 3,
            },
            {
                'question': 'Can I post job opportunities on the platform?',
                'answer': 'Yes! Registered alumni can post job opportunities through the Job Board. This helps fellow alumni find career opportunities and strengthens our professional network.',
                'order': 4,
            },
        ]

        for faq_item_data in faq_data:
            faq, created = FAQ.objects.get_or_create(
                question=faq_item_data['question'],
                defaults=faq_item_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created FAQ: {faq_item_data["question"][:50]}...'))
            else:
                self.stdout.write(self.style.WARNING(f'FAQ "{faq_item_data["question"][:50]}..." already exists'))

        # Create About Page Configuration
        about_config, created = AboutPageConfig.objects.get_or_create(
            defaults={
                'university_name': 'Negros Oriental State University',
                'university_short_name': 'NORSU',
                'university_description': 'Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services.',
                'university_extended_description': 'Established in 2004 through the merger of several educational institutions, NORSU has grown to become a leading center of learning in the Visayas region. Our university is dedicated to developing competent professionals who contribute to national development and global competitiveness.',
                'establishment_year': '2004',
                'mission': 'To provide quality and relevant education through instruction, research, extension, and production services for the holistic development of individuals and communities towards a progressive society.',
                'vision': 'A premier state university in the Asia-Pacific region recognized for excellence in instruction, research, extension, and production that produces globally competitive graduates and empowered communities.',
                'about_page_title': 'About NORSU Alumni Network',
                'about_page_subtitle': 'Learn more about our university, mission, and the people behind our alumni community',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created About Page Configuration'))
        else:
            self.stdout.write(self.style.WARNING('About Page Configuration already exists'))

        # Create Alumni Statistics
        statistics_data = [
            {
                'statistic_type': 'alumni_members',
                'value': '5,000+',
                'label': 'Alumni Members',
                'icon': 'fas fa-graduation-cap',
                'icon_color': 'primary',
                'order': 1,
            },
            {
                'statistic_type': 'alumni_groups',
                'value': '25+',
                'label': 'Alumni Groups',
                'icon': 'fas fa-users',
                'icon_color': 'success',
                'order': 2,
            },
            {
                'statistic_type': 'annual_events',
                'value': '50+',
                'label': 'Annual Events',
                'icon': 'fas fa-calendar-alt',
                'icon_color': 'warning',
                'order': 3,
            },
            {
                'statistic_type': 'job_opportunities',
                'value': '100+',
                'label': 'Job Opportunities',
                'icon': 'fas fa-briefcase',
                'icon_color': 'info',
                'order': 4,
            },
        ]

        for stat_data in statistics_data:
            stat, created = AlumniStatistic.objects.get_or_create(
                statistic_type=stat_data['statistic_type'],
                defaults=stat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created statistic: {stat_data["label"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Statistic "{stat_data["label"]}" already exists'))


        self.stdout.write(self.style.SUCCESS('\n🎉 CMS content population completed successfully!'))
        self.stdout.write('You can now access the admin interface to manage your content.')
