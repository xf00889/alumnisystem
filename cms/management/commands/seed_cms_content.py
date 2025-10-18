"""
Management command to seed the CMS with default content.
This command creates default content for all CMS models when the database is empty.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from cms.models import (
    SiteConfig, PageSection, StaticPage, StaffMember, 
    TimelineItem, ContactInfo, FAQ, Feature, Testimonial
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed the CMS with default content for empty database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force seeding even if content already exists',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip models that already have content',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        skip_existing = options.get('skip_existing', False)
        
        self.stdout.write(
            self.style.SUCCESS('🌱 Starting CMS content seeding...')
        )

        try:
            with transaction.atomic():
                # Seed Site Configuration
                self.seed_site_config(force, skip_existing)
                
                # Seed Page Sections
                self.seed_page_sections(force, skip_existing)
                
                # Seed Static Pages
                self.seed_static_pages(force, skip_existing)
                
                # Seed Features
                self.seed_features(force, skip_existing)
                
                # Seed Testimonials
                self.seed_testimonials(force, skip_existing)
                
                # Seed Staff Members
                self.seed_staff_members(force, skip_existing)
                
                # Seed Timeline Items
                self.seed_timeline_items(force, skip_existing)
                
                # Seed Contact Information
                self.seed_contact_info(force, skip_existing)
                
                # Seed FAQs
                self.seed_faqs(force, skip_existing)

            self.stdout.write(
                self.style.SUCCESS('✅ CMS content seeding completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error seeding CMS content: {e}')
            )
            raise CommandError(f'Seeding failed: {e}')

    def seed_site_config(self, force=False, skip_existing=False):
        """Seed site configuration"""
        if SiteConfig.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Site config already exists, skipping...')
            return
            
        if SiteConfig.objects.exists() and not force:
            self.stdout.write('⚠️  Site config already exists. Use --force to overwrite.')
            return

        if force and SiteConfig.objects.exists():
            SiteConfig.objects.all().delete()

        site_config = SiteConfig.get_site_config()
        self.stdout.write('✅ Site configuration created')

    def seed_page_sections(self, force=False, skip_existing=False):
        """Seed page sections"""
        if PageSection.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Page sections already exist, skipping...')
            return

        if force and PageSection.objects.exists():
            PageSection.objects.all().delete()

        sections_data = [
            {
                'section_type': 'hero',
                'title': 'Connect. Grow. Succeed.',
                'subtitle': 'Join the NORSU Alumni Network and stay connected with your fellow graduates, discover new opportunities, and continue your journey of success.',
                'content': '<p>Welcome to the official alumni network of Negros Oriental State University. Connect with fellow graduates, discover career opportunities, and be part of our growing community.</p>',
                'order': 1,
            },
            {
                'section_type': 'features',
                'title': 'Why Join Our Network?',
                'subtitle': 'Discover the benefits of being part of the NORSU Alumni Network',
                'content': '<p>Our alumni network provides numerous benefits to help you grow personally and professionally.</p>',
                'order': 2,
            },
            {
                'section_type': 'testimonials',
                'title': 'What Our Alumni Say',
                'subtitle': 'Hear from successful graduates who are making a difference',
                'content': '<p>Our alumni are making waves in various industries and communities.</p>',
                'order': 3,
            },
            {
                'section_type': 'cta',
                'title': 'Ready to Get Started?',
                'subtitle': 'Join thousands of NORSU alumni who are already connected',
                'content': '<p>Create your profile today and start building meaningful connections with your fellow graduates.</p>',
                'order': 4,
            },
        ]

        for section_data in sections_data:
            PageSection.objects.get_or_create(
                section_type=section_data['section_type'],
                defaults=section_data
            )

        self.stdout.write('✅ Page sections created')

    def seed_static_pages(self, force=False, skip_existing=False):
        """Seed static pages"""
        if StaticPage.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Static pages already exist, skipping...')
            return

        if force and StaticPage.objects.exists():
            StaticPage.objects.all().delete()

        pages_data = [
            {
                'page_type': 'about',
                'title': 'About NORSU Alumni Network',
                'content': '''
                <h2>Our Mission</h2>
                <p>The NORSU Alumni Network is dedicated to fostering lifelong connections among graduates of Negros Oriental State University. We aim to create a vibrant community that supports personal growth, professional development, and meaningful relationships.</p>
                
                <h2>Our Vision</h2>
                <p>To be the premier alumni network that empowers NORSU graduates to achieve their full potential while contributing to the betterment of society.</p>
                
                <h2>Our Values</h2>
                <ul>
                    <li><strong>Excellence:</strong> We strive for excellence in everything we do</li>
                    <li><strong>Integrity:</strong> We uphold the highest standards of honesty and ethics</li>
                    <li><strong>Service:</strong> We are committed to serving our community and society</li>
                    <li><strong>Innovation:</strong> We embrace new ideas and technologies</li>
                    <li><strong>Collaboration:</strong> We believe in the power of working together</li>
                </ul>
                ''',
                'meta_description': 'Learn about the NORSU Alumni Network, our mission, vision, and values in connecting graduates worldwide.',
            },
            {
                'page_type': 'contact',
                'title': 'Contact Us',
                'content': '''
                <h2>Get in Touch</h2>
                <p>We'd love to hear from you! Whether you have questions, suggestions, or just want to say hello, don't hesitate to reach out to us.</p>
                
                <h3>Office Hours</h3>
                <p>Monday to Friday: 8:00 AM - 5:00 PM<br>
                Saturday: 9:00 AM - 12:00 PM<br>
                Sunday: Closed</p>
                
                <h3>Response Time</h3>
                <p>We typically respond to inquiries within 24-48 hours during business days.</p>
                ''',
                'meta_description': 'Contact the NORSU Alumni Network. Get in touch with our team for support, questions, or feedback.',
            },
            {
                'page_type': 'privacy',
                'title': 'Privacy Policy',
                'content': '''
                <h2>Privacy Policy</h2>
                <p>Last updated: [Date]</p>
                
                <h3>Information We Collect</h3>
                <p>We collect information you provide directly to us, such as when you create an account, update your profile, or contact us.</p>
                
                <h3>How We Use Your Information</h3>
                <p>We use the information we collect to provide, maintain, and improve our services, communicate with you, and ensure the security of our platform.</p>
                
                <h3>Information Sharing</h3>
                <p>We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy.</p>
                
                <h3>Data Security</h3>
                <p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.</p>
                ''',
                'meta_description': 'Read our privacy policy to understand how we collect, use, and protect your personal information.',
            },
            {
                'page_type': 'terms',
                'title': 'Terms of Service',
                'content': '''
                <h2>Terms of Service</h2>
                <p>Last updated: [Date]</p>
                
                <h3>Acceptance of Terms</h3>
                <p>By accessing and using the NORSU Alumni Network, you accept and agree to be bound by the terms and provision of this agreement.</p>
                
                <h3>Use License</h3>
                <p>Permission is granted to temporarily download one copy of the materials on the NORSU Alumni Network for personal, non-commercial transitory viewing only.</p>
                
                <h3>User Conduct</h3>
                <p>Users agree to use the platform responsibly and in accordance with all applicable laws and regulations.</p>
                
                <h3>Limitation of Liability</h3>
                <p>In no event shall NORSU Alumni Network or its suppliers be liable for any damages arising out of the use or inability to use the materials on the platform.</p>
                ''',
                'meta_description': 'Read our terms of service to understand the rules and guidelines for using the NORSU Alumni Network.',
            },
        ]

        for page_data in pages_data:
            StaticPage.objects.get_or_create(
                page_type=page_data['page_type'],
                defaults=page_data
            )

        self.stdout.write('✅ Static pages created')

    def seed_features(self, force=False, skip_existing=False):
        """Seed features"""
        if Feature.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Features already exist, skipping...')
            return

        if force and Feature.objects.exists():
            Feature.objects.all().delete()

        features_data = [
            {
                'title': 'Professional Networking',
                'content': 'Connect with fellow alumni across different industries and build meaningful professional relationships.',
                'icon': 'fas fa-network-wired',
                'icon_class': 'primary',
                'order': 1,
            },
            {
                'title': 'Career Opportunities',
                'content': 'Access exclusive job postings, career resources, and mentorship opportunities from successful alumni.',
                'icon': 'fas fa-briefcase',
                'icon_class': 'success',
                'order': 2,
            },
            {
                'title': 'Alumni Events',
                'content': 'Stay updated on reunions, networking events, and professional development workshops.',
                'icon': 'fas fa-calendar-alt',
                'icon_class': 'info',
                'order': 3,
            },
            {
                'title': 'Knowledge Sharing',
                'content': 'Share your expertise, learn from others, and contribute to the collective knowledge of our community.',
                'icon': 'fas fa-lightbulb',
                'icon_class': 'warning',
                'order': 4,
            },
            {
                'title': 'Mentorship Program',
                'content': 'Give back by mentoring current students or receive guidance from experienced alumni.',
                'icon': 'fas fa-hands-helping',
                'icon_class': 'danger',
                'order': 5,
            },
            {
                'title': 'Alumni Directory',
                'content': 'Find and connect with classmates, professors, and alumni from your batch or department.',
                'icon': 'fas fa-users',
                'icon_class': 'secondary',
                'order': 6,
            },
        ]

        for feature_data in features_data:
            Feature.objects.get_or_create(
                title=feature_data['title'],
                defaults=feature_data
            )

        self.stdout.write('✅ Features created')

    def seed_testimonials(self, force=False, skip_existing=False):
        """Seed testimonials"""
        if Testimonial.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Testimonials already exist, skipping...')
            return

        if force and Testimonial.objects.exists():
            Testimonial.objects.all().delete()

        testimonials_data = [
            {
                'name': 'Dr. Maria Santos',
                'position': 'Medical Director',
                'company': 'Regional Medical Center',
                'quote': 'The NORSU Alumni Network has been instrumental in my career growth. Through this platform, I\'ve connected with fellow medical professionals and found amazing mentorship opportunities.',
                'order': 1,
            },
            {
                'name': 'Engr. John Rodriguez',
                'position': 'Senior Software Engineer',
                'company': 'Tech Solutions Inc.',
                'quote': 'Being part of this network has opened doors I never knew existed. The job opportunities and professional connections have been invaluable to my career development.',
                'order': 2,
            },
            {
                'name': 'Prof. Ana Dela Cruz',
                'position': 'University Professor',
                'company': 'State University',
                'quote': 'The knowledge sharing and collaboration opportunities in this network are exceptional. It\'s wonderful to see how our alumni are making a difference in various fields.',
                'order': 3,
            },
        ]

        for testimonial_data in testimonials_data:
            Testimonial.objects.get_or_create(
                name=testimonial_data['name'],
                defaults=testimonial_data
            )

        self.stdout.write('✅ Testimonials created')

    def seed_staff_members(self, force=False, skip_existing=False):
        """Seed staff members"""
        if StaffMember.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Staff members already exist, skipping...')
            return

        if force and StaffMember.objects.exists():
            StaffMember.objects.all().delete()

        staff_data = [
            {
                'name': 'Dr. Roberto Mendez',
                'position': 'Alumni Relations Director',
                'department': 'Alumni Affairs Office',
                'bio': 'Dr. Mendez has been leading alumni relations for over 10 years, fostering strong connections between the university and its graduates.',
                'email': 'alumni.director@norsu.edu.ph',
                'order': 1,
            },
            {
                'name': 'Ms. Sarah Johnson',
                'position': 'Alumni Coordinator',
                'department': 'Alumni Affairs Office',
                'bio': 'Sarah coordinates alumni events and programs, ensuring smooth communication between the university and alumni community.',
                'email': 'alumni.coordinator@norsu.edu.ph',
                'order': 2,
            },
        ]

        for staff_data_item in staff_data:
            StaffMember.objects.get_or_create(
                name=staff_data_item['name'],
                defaults=staff_data_item
            )

        self.stdout.write('✅ Staff members created')

    def seed_timeline_items(self, force=False, skip_existing=False):
        """Seed timeline items"""
        if TimelineItem.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Timeline items already exist, skipping...')
            return

        if force and TimelineItem.objects.exists():
            TimelineItem.objects.all().delete()

        timeline_data = [
            {
                'year': '2004',
                'title': 'NORSU Founded',
                'description': 'Negros Oriental State University was established, marking the beginning of our educational journey.',
                'icon': 'fas fa-university',
                'order': 1,
            },
            {
                'year': '2010',
                'title': 'First Alumni Reunion',
                'description': 'The first official alumni reunion was held, bringing together graduates from the early years.',
                'icon': 'fas fa-users',
                'order': 2,
            },
            {
                'year': '2015',
                'title': 'Alumni Network Launch',
                'description': 'The official NORSU Alumni Network was launched, providing a digital platform for alumni connections.',
                'icon': 'fas fa-globe',
                'order': 3,
            },
            {
                'year': '2020',
                'title': 'Virtual Events Initiative',
                'description': 'Launched virtual events and online networking opportunities to adapt to changing times.',
                'icon': 'fas fa-video',
                'order': 4,
            },
        ]

        for timeline_item in timeline_data:
            TimelineItem.objects.get_or_create(
                year=timeline_item['year'],
                title=timeline_item['title'],
                defaults=timeline_item
            )

        self.stdout.write('✅ Timeline items created')

    def seed_contact_info(self, force=False, skip_existing=False):
        """Seed contact information"""
        if ContactInfo.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  Contact info already exists, skipping...')
            return

        if force and ContactInfo.objects.exists():
            ContactInfo.objects.all().delete()

        contact_data = [
            {
                'contact_type': 'email',
                'value': 'alumni@norsu.edu.ph',
                'is_primary': True,
                'order': 1,
            },
            {
                'contact_type': 'phone',
                'value': '+63 35 422 6002',
                'is_primary': True,
                'order': 1,
            },
            {
                'contact_type': 'address',
                'value': 'Negros Oriental State University\nKagawasan, Ave. Rizal\nDumaguete City, 6200\nNegros Oriental, Philippines',
                'is_primary': True,
                'order': 1,
            },
            {
                'contact_type': 'hours',
                'value': 'Monday to Friday: 8:00 AM - 5:00 PM\nSaturday: 9:00 AM - 12:00 PM\nSunday: Closed',
                'is_primary': True,
                'order': 1,
            },
        ]

        for contact_item in contact_data:
            ContactInfo.objects.get_or_create(
                contact_type=contact_item['contact_type'],
                value=contact_item['value'],
                defaults=contact_item
            )

        self.stdout.write('✅ Contact information created')

    def seed_faqs(self, force=False, skip_existing=False):
        """Seed FAQs"""
        if FAQ.objects.exists() and not force and skip_existing:
            self.stdout.write('⏭️  FAQs already exist, skipping...')
            return

        if force and FAQ.objects.exists():
            FAQ.objects.all().delete()

        faqs_data = [
            {
                'question': 'How do I join the NORSU Alumni Network?',
                'answer': 'Simply create an account on our platform using your NORSU email address or any email address if you graduated before the email system was implemented. You\'ll need to verify your graduation status.',
                'order': 1,
            },
            {
                'question': 'Is there a membership fee?',
                'answer': 'Basic membership to the NORSU Alumni Network is free. However, some premium features and exclusive events may require a small fee to cover operational costs.',
                'order': 2,
            },
            {
                'question': 'How can I update my profile information?',
                'answer': 'You can update your profile information at any time by logging into your account and navigating to the "My Profile" section. Make sure to keep your contact information current.',
                'order': 3,
            },
            {
                'question': 'How do I find alumni from my batch or department?',
                'answer': 'Use our alumni directory search feature. You can filter by graduation year, department, location, and other criteria to find specific alumni.',
                'order': 4,
            },
            {
                'question': 'Can I post job opportunities on the platform?',
                'answer': 'Yes! Alumni are encouraged to share job opportunities with fellow graduates. You can post job openings in the jobs section or share them in relevant groups.',
                'order': 5,
            },
            {
                'question': 'How do I get involved in mentorship programs?',
                'answer': 'You can sign up to be a mentor or request a mentor through our mentorship program section. We match mentors and mentees based on industry, experience, and goals.',
                'order': 6,
            },
        ]

        for faq_data in faqs_data:
            FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )

        self.stdout.write('✅ FAQs created')
