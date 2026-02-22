"""
Management command to populate test data for Alumni Affairs Officials
Creates 10 sample staff members for testing the officials slider
"""

from django.core.management.base import BaseCommand
from cms.models import StaffMember


class Command(BaseCommand):
    help = 'Populate test data for Alumni Affairs Officials (10 sample staff members)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing staff members before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = StaffMember.objects.all().count()
            StaffMember.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing staff members')
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
                'bio': 'Coordinating alumni relations and fostering lifelong connections between graduates and the university.',
                'email': 'alumni.director@norsu.edu.ph',
                'order': 2,
            },
            {
                'name': 'Sandra S. Balansag, RCrim, MSCJ-Crim',
                'position': 'Staff, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Supporting alumni programs and maintaining strong relationships with NORSU graduates.',
                'email': 'alumni.staff@norsu.edu.ph',
                'order': 3,
            },
            {
                'name': 'Urcisciano B. Bato, BSIT',
                'position': 'Technician, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Managing technical systems and digital platforms for alumni engagement and communication.',
                'email': 'alumni.tech@norsu.edu.ph',
                'order': 4,
            },
            {
                'name': 'Dr. Maria Teresa L. Santos',
                'position': 'Vice President for Academic Affairs',
                'department': 'Office of Academic Affairs',
                'bio': 'Overseeing academic programs and ensuring quality education for current and future alumni.',
                'email': 'vpaa@norsu.edu.ph',
                'order': 5,
            },
            {
                'name': 'Engr. Roberto C. Mendoza',
                'position': 'Vice President for Administration',
                'department': 'Office of Administration',
                'bio': 'Managing university operations and supporting alumni initiatives through administrative excellence.',
                'email': 'vpa@norsu.edu.ph',
                'order': 6,
            },
            {
                'name': 'Dr. Carmen R. Villanueva',
                'position': 'Dean, College of Arts and Sciences',
                'department': 'College of Arts and Sciences',
                'bio': 'Leading the college and maintaining strong connections with arts and sciences alumni.',
                'email': 'cas.dean@norsu.edu.ph',
                'order': 7,
            },
            {
                'name': 'Atty. Jose P. Reyes',
                'position': 'Dean, College of Law',
                'department': 'College of Law',
                'bio': 'Guiding law students and fostering professional networks among law alumni.',
                'email': 'law.dean@norsu.edu.ph',
                'order': 8,
            },
            {
                'name': 'Dr. Elena F. Cruz',
                'position': 'Dean, College of Education',
                'department': 'College of Education',
                'bio': 'Developing future educators and supporting education alumni in their teaching careers.',
                'email': 'coed.dean@norsu.edu.ph',
                'order': 9,
            },
            {
                'name': 'Prof. Antonio M. Garcia',
                'position': 'Coordinator, Alumni Relations',
                'department': 'Office of Alumni Affairs',
                'bio': 'Organizing alumni events and maintaining active communication with graduates worldwide.',
                'email': 'alumni.coordinator@norsu.edu.ph',
                'order': 10,
            },
        ]

        created_count = 0
        for official_data in officials_data:
            staff, created = StaffMember.objects.get_or_create(
                name=official_data['name'],
                defaults=official_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {staff.name} - {staff.position}')
                )
            else:
                # Update existing record
                for key, value in official_data.items():
                    setattr(staff, key, value)
                staff.save()
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated: {staff.name} - {staff.position}')
                )

        self.stdout.write('\n' + '='*70)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully processed {len(officials_data)} staff members'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Created: {created_count}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Updated: {len(officials_data) - created_count}')
        )
        self.stdout.write('\n' + '='*70)
        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ Test data ready! Visit the homepage to see the officials slider in action.'
            )
        )
        self.stdout.write(
            self.style.HTTP_INFO(
                '\nTip: Run with --clear flag to remove existing staff before creating new ones'
            )
        )
