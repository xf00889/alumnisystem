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
                'bio': '',
                'email': 'alumni@norsu.edu.ph',
                'order': 1,
                'is_active': True,
            },
            
            # Staff Members
            {
                'name': 'Sandra S. Balansag, RCrim, MSCJ-Crim',
                'position': 'Staff, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': '',
                'email': '',
                'order': 2,
                'is_active': True,
            },
            {
                'name': 'Urcisciano B. Bato, BSIT',
                'position': 'Technician, Alumni Affairs',
                'department': 'Office of Alumni Affairs',
                'bio': '',
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
                'bio': '',
                'email': '',
                'order': 10,
                'is_active': True,
            },
            {
                'name': 'Ms. Lorna A. Labe',
                'position': 'Bayawan-Sta Catalina Campus-Coordinator',
                'department': 'Bayawan-Sta Catalina Campus',
                'bio': '',
                'email': '',
                'order': 11,
                'is_active': True,
            },
            {
                'name': 'Prof. Cynie T. Antique',
                'position': 'CBA-Coordinator',
                'department': 'College of Business Administration',
                'bio': '',
                'email': '',
                'order': 12,
                'is_active': True,
            },
            {
                'name': 'Prof. Vivian Altamarino',
                'position': 'Bais Campuses I & II-Coordinator',
                'department': 'Bais Campuses I & II',
                'bio': '',
                'email': '',
                'order': 13,
                'is_active': True,
            },
            {
                'name': 'Mr. Dante A. Capistrano',
                'position': 'CCJE-Coordinator',
                'department': 'College of Criminal Justice Education',
                'bio': '',
                'email': '',
                'order': 14,
                'is_active': True,
            },
            {
                'name': 'Prof. Jed Christian L. Cece',
                'position': 'Guihulngan Campus-Coordinator',
                'department': 'Guihulngan Campus',
                'bio': '',
                'email': '',
                'order': 15,
                'is_active': True,
            },
            {
                'name': 'Engr. Angel M. Honculada',
                'position': 'CEA-Coordinators',
                'department': 'College of Engineering and Architecture',
                'bio': '',
                'email': '',
                'order': 16,
                'is_active': True,
            },
            {
                'name': 'Ms. Marecel T. Sayre',
                'position': 'Siaton Campus-Coordinator',
                'department': 'Siaton Campus',
                'bio': '',
                'email': '',
                'order': 17,
                'is_active': True,
            },
            {
                'name': 'Dr. Judy A. Cornelia',
                'position': 'CED-Coordinator',
                'department': 'College of Education',
                'bio': '',
                'email': '',
                'order': 18,
                'is_active': True,
            },
            {
                'name': 'Ms. Divina R. Bulay',
                'position': 'Mabinay Campus-Coordinator',
                'department': 'Mabinay Campus',
                'bio': '',
                'email': '',
                'order': 19,
                'is_active': True,
            },
            {
                'name': 'Prof. Geo Rey A. Tajada',
                'position': 'CIT-Coordinator',
                'department': 'College of Information Technology',
                'bio': '',
                'email': '',
                'order': 20,
                'is_active': True,
            },
            {
                'name': 'Mr. Teresito A. Tabinas',
                'position': 'CAFF/Pamplona Campus-Coordinator',
                'department': 'College of Agriculture, Forestry and Food Science / Pamplona Campus',
                'bio': '',
                'email': '',
                'order': 21,
                'is_active': True,
            },
            {
                'name': 'Dr. Novalisa A. Leon',
                'position': 'CNPAHS-Coordinator',
                'department': 'College of Nursing and Allied Health Sciences',
                'bio': '',
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
            'bio': '',
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
