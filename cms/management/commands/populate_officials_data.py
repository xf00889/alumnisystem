"""
Management command to populate test data for University Alumni Affairs Officials
"""
from django.core.management.base import BaseCommand
from cms.models import StaffMember


class Command(BaseCommand):
    help = 'Populate test data for University Alumni Affairs Officials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing staff members before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = StaffMember.objects.count()
            StaffMember.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Cleared {count} existing staff members')
            )

        # Sample officials data
        officials_data = [
            {
                'name': 'HON. MARJON E. YASI, Psy.D',
                'position': 'University President',
                'department': 'Office of the President',
                'bio': 'Leading NORSU with vision and dedication to academic excellence and alumni engagement.',
                'email': 'president@norsu.edu.ph',
                'order': 1,
            },
            {
                'name': 'Pio S. Supat, Ph.D.',
                'position': 'Director, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Coordinating alumni relations and fostering lifelong connections with NORSU graduates.',
                'email': 'alumni.director@norsu.edu.ph',
                'order': 2,
            },
            {
                'name': 'Sandra S. Balansag, RCrim, MSCJ-Crim',
                'position': 'Staff, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Supporting alumni programs and maintaining strong relationships with graduates.',
                'email': 'alumni.staff@norsu.edu.ph',
                'order': 3,
            },
            {
                'name': 'Urcisciano B. Bato, BSIT',
                'position': 'Technician, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Managing technical systems and digital platforms for alumni engagement.',
                'email': 'alumni.tech@norsu.edu.ph',
                'order': 4,
            },
            {
                'name': 'Dr. Maria Santos',
                'position': 'Vice President for Academic Affairs',
                'department': 'Academic Affairs Office',
                'bio': 'Overseeing academic programs and ensuring quality education for all students.',
                'email': 'vpaa@norsu.edu.ph',
                'order': 5,
            },
            {
                'name': 'Prof. Juan Dela Cruz',
                'position': 'Dean, College of Arts and Sciences',
                'department': 'College of Arts and Sciences',
                'bio': 'Leading the college in providing comprehensive liberal arts education.',
                'email': 'cas.dean@norsu.edu.ph',
                'order': 6,
            },
            {
                'name': 'Dr. Ana Reyes',
                'position': 'Dean, College of Engineering',
                'department': 'College of Engineering',
                'bio': 'Advancing engineering education and research at NORSU.',
                'email': 'coe.dean@norsu.edu.ph',
                'order': 7,
            },
            {
                'name': 'Prof. Roberto Garcia',
                'position': 'Dean, College of Business Administration',
                'department': 'College of Business Administration',
                'bio': 'Developing future business leaders and entrepreneurs.',
                'email': 'cba.dean@norsu.edu.ph',
                'order': 8,
            },
            {
                'name': 'Dr. Elena Martinez',
                'position': 'Dean, College of Education',
                'department': 'College of Education',
                'bio': 'Preparing competent and compassionate educators for the future.',
                'email': 'coed.dean@norsu.edu.ph',
                'order': 9,
            },
            {
                'name': 'Prof. Carlos Fernandez',
                'position': 'Director, Research and Development',
                'department': 'Research and Development Office',
                'bio': 'Promoting research excellence and innovation across the university.',
                'email': 'rnd.director@norsu.edu.ph',
                'order': 10,
            },
        ]

        created_count = 0
        updated_count = 0

        for official_data in officials_data:
            staff, created = StaffMember.objects.update_or_create(
                name=official_data['name'],
                defaults=official_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {staff.name} - {staff.position}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {staff.name} - {staff.position}')
                )

        self.stdout.write('\n' + '='*70)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully populated officials data!'
                f'\n  - Created: {created_count} new officials'
                f'\n  - Updated: {updated_count} existing officials'
                f'\n  - Total: {StaffMember.objects.filter(is_active=True).count()} active officials'
            )
        )
        self.stdout.write('='*70 + '\n')
        
        # Display instructions
        self.stdout.write(
            self.style.HTTP_INFO(
                '\nNext steps:'
                '\n  1. Run: python manage.py runserver'
                '\n  2. Visit: http://localhost:8000/'
                '\n  3. Scroll to "Office of the University Alumni Affairs Officials"'
                '\n  4. Test the slider navigation'
                '\n'
            )
        )
        
        # Display management tips
        self.stdout.write(
            self.style.HTTP_INFO(
                'Management commands:'
                '\n  - Add more officials: python manage.py populate_officials_data'
                '\n  - Clear and repopulate: python manage.py populate_officials_data --clear'
                '\n  - Manage via admin: http://localhost:8000/admin/cms/staffmember/'
                '\n'
            )
        )
