"""
Django management command to seed Alumni Affairs staff and coordinators.

This command populates the StaffMember model with the official NORSU Alumni Affairs
team including the Director, staff members, and campus coordinators.

Usage:
    python manage.py seed_staff_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from cms.models import StaffMember


class Command(BaseCommand):
    help = 'Seeds Alumni Affairs staff and coordinators with official NORSU data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing staff data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting staff data seeding...'))
        self.stdout.write('')

        # ============================================================
        # ALUMNI AFFAIRS STAFF DATA
        # ============================================================
        STAFF_DATA = [
            # Director
            {
                'name': 'Pio S. Sapat, Ph.D.',
                'position': 'Director, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Dr. Pio S. Sapat serves as the Director of the Office of Alumni Affairs at Negros Oriental State University. He leads the strategic initiatives to strengthen alumni engagement, foster professional networks, and support the continuous growth of the NORSU alumni community worldwide.',
                'email': 'alumni@norsu.edu.ph',
                'order': 1,
                'is_active': True,
            },
            
            # Staff Members
            {
                'name': 'Sandra S. Balansag, RCrim, MSCJ-Crim',
                'position': 'Staff, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Sandra S. Balansag provides administrative and operational support to the Office of Alumni Affairs, ensuring smooth coordination of alumni programs, events, and communications.',
                'email': '',
                'order': 2,
                'is_active': True,
            },
            {
                'name': 'Urcisciano B. Bato, BSIT',
                'position': 'Technician, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': 'Urcisciano B. Bato serves as the technical specialist for the Office of Alumni Affairs, managing the alumni database, website, and digital communication platforms.',
                'email': '',
                'order': 3,
                'is_active': True,
            },
        ]

        # ============================================================
        # CAMPUS COORDINATORS DATA
        # ============================================================
        COORDINATORS_DATA = [
            {
                'name': 'Dr. Jacel Angeline V. Lingcong',
                'position': 'CAS-Coordinator',
                'department': 'College of Arts and Sciences',
                'bio': 'Dr. Jacel Angeline V. Lingcong coordinates alumni affairs for the College of Arts and Sciences, facilitating connections between CAS alumni and current students while promoting academic and professional development opportunities.',
                'email': '',
                'order': 10,
                'is_active': True,
            },
            {
                'name': 'Ms. Lorna A. Labe',
                'position': 'Bayawan-Sta Catalina Campus-Coordinator',
                'department': 'Bayawan-Sta Catalina Campus',
                'bio': 'Ms. Lorna A. Labe serves as the alumni coordinator for the Bayawan-Sta Catalina Campus, building strong relationships with campus alumni and organizing local engagement activities.',
                'email': '',
                'order': 11,
                'is_active': True,
            },
            {
                'name': 'Prof. Cynie T. Antique',
                'position': 'CBA-Coordinator',
                'department': 'College of Business Administration',
                'bio': 'Prof. Cynie T. Antique coordinates alumni relations for the College of Business Administration, connecting business alumni with networking opportunities and career advancement resources.',
                'email': '',
                'order': 12,
                'is_active': True,
            },
            {
                'name': 'Prof. Vivian Altamarino',
                'position': 'Bais Campuses I & II-Coordinator',
                'department': 'Bais Campuses I & II',
                'bio': 'Prof. Vivian Altamarino manages alumni affairs for both Bais Campus I and Bais Campus II, fostering alumni engagement and supporting campus development initiatives.',
                'email': '',
                'order': 13,
                'is_active': True,
            },
            {
                'name': 'Mr. Dante A. Capistrano',
                'position': 'CCJE-Coordinator',
                'department': 'College of Criminal Justice Education',
                'bio': 'Mr. Dante A. Capistrano coordinates alumni activities for the College of Criminal Justice Education, maintaining connections with law enforcement and criminal justice professionals in the alumni network.',
                'email': '',
                'order': 14,
                'is_active': True,
            },
            {
                'name': 'Prof. Jed Christian L. Cece',
                'position': 'Guihulngan Campus-Coordinator',
                'department': 'Guihulngan Campus',
                'bio': 'Prof. Jed Christian L. Cece serves as the alumni coordinator for Guihulngan Campus, organizing alumni events and strengthening ties between the campus and its graduates.',
                'email': '',
                'order': 15,
                'is_active': True,
            },
            {
                'name': 'Engr. Angel M. Honculada',
                'position': 'CEA-Coordinators',
                'department': 'College of Engineering and Architecture',
                'bio': 'Engr. Angel M. Honculada coordinates alumni relations for the College of Engineering and Architecture, connecting engineering and architecture alumni with industry opportunities and professional development.',
                'email': '',
                'order': 16,
                'is_active': True,
            },
            {
                'name': 'Ms. Marecel T. Sayre',
                'position': 'Siaton Campus-Coordinator',
                'department': 'Siaton Campus',
                'bio': 'Ms. Marecel T. Sayre manages alumni affairs for Siaton Campus, facilitating alumni engagement and supporting campus programs through alumni participation.',
                'email': '',
                'order': 17,
                'is_active': True,
            },
            {
                'name': 'Dr. Judy A. Cornelia',
                'position': 'CED-Coordinator',
                'department': 'College of Education',
                'bio': 'Dr. Judy A. Cornelia coordinates alumni activities for the College of Education, connecting education alumni with teaching opportunities and professional development in the education sector.',
                'email': '',
                'order': 18,
                'is_active': True,
            },
            {
                'name': 'Ms. Divina R. Bulay',
                'position': 'Mabinay Campus-Coordinator',
                'department': 'Mabinay Campus',
                'bio': 'Ms. Divina R. Bulay serves as the alumni coordinator for Mabinay Campus, organizing local alumni activities and maintaining strong campus-alumni relationships.',
                'email': '',
                'order': 19,
                'is_active': True,
            },
            {
                'name': 'Prof. Geo Rey A. Tajada',
                'position': 'CIT-Coordinator',
                'department': 'College of Information Technology',
                'bio': 'Prof. Geo Rey A. Tajada coordinates alumni relations for the College of Information Technology, connecting IT alumni with technology industry opportunities and innovation initiatives.',
                'email': '',
                'order': 20,
                'is_active': True,
            },
            {
                'name': 'Mr. Teresito A. Tabinas',
                'position': 'CAFF/Pamplona Campus-Coordinator',
                'department': 'College of Agriculture, Forestry and Food Science / Pamplona Campus',
                'bio': 'Mr. Teresito A. Tabinas manages alumni affairs for the College of Agriculture, Forestry and Food Science and Pamplona Campus, supporting agricultural and environmental science alumni networks.',
                'email': '',
                'order': 21,
                'is_active': True,
            },
            {
                'name': 'Dr. Novalisa A. Leon',
                'position': 'CNPAHS-Coordinator',
                'department': 'College of Nursing and Allied Health Sciences',
                'bio': 'Dr. Novalisa A. Leon coordinates alumni activities for the College of Nursing and Allied Health Sciences, connecting healthcare professionals in the alumni network with continuing education and career opportunities.',
                'email': '',
                'order': 22,
                'is_active': True,
            },
        ]

        # ============================================================
        # UNIVERSITY PRESIDENT (Optional - can be added to officials)
        # ============================================================
        PRESIDENT_DATA = {
            'name': 'Dr. Noel Marjon E. Yasi',
            'position': 'University President',
            'department': 'Office of the President',
            'bio': 'Dr. Noel Marjon E. Yasi serves as the University President of Negros Oriental State University, providing visionary leadership and strategic direction to advance the university\'s mission of academic excellence, research innovation, and community service.',
            'email': 'president@norsu.edu.ph',
            'order': 0,
            'is_active': True,
        }

        # ============================================================
        # EXECUTION
        # ============================================================
        
        created_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                # Clear existing data if requested
                if options['clear']:
                    deleted_count = StaffMember.objects.all().count()
                    StaffMember.objects.all().delete()
                    self.stdout.write(
                        self.style.WARNING(f'[!] Cleared {deleted_count} existing staff record(s)')
                    )
                    self.stdout.write('')
                
                # Seed University President (optional)
                self.stdout.write(self.style.HTTP_INFO('[*] Seeding University President...'))
                self.stdout.write('-' * 60)
                
                president, created = StaffMember.objects.update_or_create(
                    name=PRESIDENT_DATA['name'],
                    defaults=PRESIDENT_DATA
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  [+] Created: {president.name} - {president.position}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  [~] Updated: {president.name} - {president.position}')
                    )
                
                # Seed Alumni Affairs Staff
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO('[*] Seeding Alumni Affairs Staff...'))
                self.stdout.write('-' * 60)
                
                for staff_data in STAFF_DATA:
                    staff, created = StaffMember.objects.update_or_create(
                        name=staff_data['name'],
                        defaults=staff_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  [+] Created: {staff.name} - {staff.position}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  [~] Updated: {staff.name} - {staff.position}')
                        )
                
                # Seed Campus Coordinators
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO('[*] Seeding Campus Coordinators...'))
                self.stdout.write('-' * 60)
                
                for coordinator_data in COORDINATORS_DATA:
                    coordinator, created = StaffMember.objects.update_or_create(
                        name=coordinator_data['name'],
                        defaults=coordinator_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  [+] Created: {coordinator.name} - {coordinator.position}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  [~] Updated: {coordinator.name} - {coordinator.position}')
                        )
                
                # Summary
                self.stdout.write('')
                self.stdout.write('=' * 60)
                self.stdout.write(self.style.HTTP_INFO('[*] SEEDING SUMMARY'))
                self.stdout.write('=' * 60)
                self.stdout.write(
                    self.style.SUCCESS(f'  [+] Created:  {created_count} staff member(s)')
                )
                self.stdout.write(
                    self.style.WARNING(f'  [~] Updated:  {updated_count} staff member(s)')
                )
                self.stdout.write(
                    f'  [*] Total:    {created_count + updated_count} staff member(s)'
                )
                self.stdout.write('=' * 60)
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('[OK] Staff data seeding completed successfully!')
                )
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO('Staff members have been organized as follows:'))
                self.stdout.write('  • University President (order: 0)')
                self.stdout.write('  • Alumni Affairs Director & Staff (order: 1-3)')
                self.stdout.write('  • Campus & College Coordinators (order: 10-22)')
                
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(
                self.style.ERROR(f'✗ Error during seeding: {str(e)}')
            )
            raise
