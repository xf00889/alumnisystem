"""
Display all officials data in a formatted way
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from cms.models import StaffMember

def main():
    print("\n" + "="*80)
    print("ALUMNI AFFAIRS OFFICIALS - TEST DATA")
    print("="*80)
    
    staff_members = StaffMember.objects.filter(is_active=True).order_by('order')
    
    if not staff_members.exists():
        print("\n✗ No active staff members found!")
        print("Run: python manage.py populate_officials_test_data")
        return
    
    print(f"\nTotal Active Officials: {staff_members.count()}")
    print("\n" + "-"*80)
    
    for i, staff in enumerate(staff_members, 1):
        print(f"\n{i}. {staff.name}")
        print(f"   Position: {staff.position}")
        print(f"   Department: {staff.department}")
        print(f"   Email: {staff.email}")
        if staff.bio:
            print(f"   Bio: {staff.bio[:70]}...")
        print(f"   Order: {staff.order}")
        print(f"   Has Image: {'Yes' if staff.image else 'No'}")
        print("-"*80)
    
    print("\n" + "="*80)
    print("SLIDER PREVIEW")
    print("="*80)
    
    print("\nDesktop View (4 per slide):")
    for i in range(0, staff_members.count(), 4):
        slide_num = (i // 4) + 1
        slide_staff = staff_members[i:i+4]
        names = [s.name.split()[0] + " " + s.name.split()[-1] for s in slide_staff]
        print(f"  Slide {slide_num}: {' | '.join(names)}")
    
    print("\nTablet View (3 per slide):")
    for i in range(0, staff_members.count(), 3):
        slide_num = (i // 3) + 1
        slide_staff = staff_members[i:i+3]
        names = [s.name.split()[0] + " " + s.name.split()[-1] for s in slide_staff]
        print(f"  Slide {slide_num}: {' | '.join(names)}")
    
    print("\nMobile View (1 per slide):")
    for i, staff in enumerate(staff_members[:5], 1):
        short_name = staff.name.split()[0] + " " + staff.name.split()[-1]
        print(f"  Slide {i}: {short_name}")
    if staff_members.count() > 5:
        print(f"  ... and {staff_members.count() - 5} more slides")
    
    print("\n" + "="*80)
    print("\n✓ Test data is ready!")
    print("\nTo view the slider:")
    print("  1. Start server: python manage.py runserver")
    print("  2. Visit: http://localhost:8000/")
    print("  3. Scroll to 'Office of the University Alumni Affairs Officials'")
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
