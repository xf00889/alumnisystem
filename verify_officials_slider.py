"""
Quick verification script for Officials Slider implementation
Checks if all components are in place and data is ready
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from cms.models import StaffMember
from django.conf import settings

def check_files():
    """Check if all required files exist"""
    print("\n" + "="*70)
    print("CHECKING FILES")
    print("="*70)
    
    files_to_check = [
        ('static/js/officials_slider.js', 'JavaScript'),
        ('static/css/officials_slider.css', 'CSS'),
        ('templates/home.html', 'Template'),
    ]
    
    all_exist = True
    for file_path, file_type in files_to_check:
        full_path = os.path.join(settings.BASE_DIR, file_path)
        exists = os.path.exists(full_path)
        status = "✓" if exists else "✗"
        print(f"{status} {file_type}: {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_static_files():
    """Check if static files are collected"""
    print("\n" + "="*70)
    print("CHECKING STATIC FILES")
    print("="*70)
    
    staticfiles_dir = os.path.join(settings.BASE_DIR, 'staticfiles')
    
    files_to_check = [
        'js/officials_slider.js',
        'css/officials_slider.css',
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = os.path.join(staticfiles_dir, file_path)
        exists = os.path.exists(full_path)
        status = "✓" if exists else "✗"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n⚠ Run: python manage.py collectstatic --noinput")
    
    return all_exist

def check_data():
    """Check if staff members data exists"""
    print("\n" + "="*70)
    print("CHECKING DATA")
    print("="*70)
    
    total_staff = StaffMember.objects.count()
    active_staff = StaffMember.objects.filter(is_active=True).count()
    
    print(f"Total staff members: {total_staff}")
    print(f"Active staff members: {active_staff}")
    
    if active_staff == 0:
        print("\n✗ No active staff members found!")
        print("⚠ Run: python manage.py populate_officials_test_data")
        return False
    
    print(f"\n✓ Found {active_staff} active staff members")
    
    # Show first 5
    print("\nFirst 5 officials:")
    for i, staff in enumerate(StaffMember.objects.filter(is_active=True).order_by('order')[:5], 1):
        print(f"  {i}. {staff.name} - {staff.position}")
    
    if active_staff > 5:
        print(f"  ... and {active_staff - 5} more")
    
    return True

def check_slider_requirements():
    """Check if slider will work properly"""
    print("\n" + "="*70)
    print("SLIDER REQUIREMENTS")
    print("="*70)
    
    active_staff = StaffMember.objects.filter(is_active=True).count()
    
    if active_staff < 5:
        print(f"⚠ Warning: Only {active_staff} officials (recommended: 5+ for best slider experience)")
        print("  Slider will still work but navigation may be limited")
    else:
        print(f"✓ {active_staff} officials (good for slider)")
    
    # Check responsive breakpoints
    print("\nSlider behavior:")
    print(f"  Desktop (≥1200px): Shows 4 officials at once")
    print(f"  Tablet (992-1199px): Shows 3 officials at once")
    print(f"  Small Tablet (768-991px): Shows 2 officials at once")
    print(f"  Mobile (<768px): Shows 1 official at once")
    
    if active_staff > 4:
        print(f"\n✓ Navigation controls will be visible (more than 4 officials)")
    else:
        print(f"\n⚠ Navigation controls will be hidden (4 or fewer officials)")
    
    return True

def main():
    print("\n" + "="*70)
    print("OFFICIALS SLIDER VERIFICATION")
    print("="*70)
    
    files_ok = check_files()
    static_ok = check_static_files()
    data_ok = check_data()
    slider_ok = check_slider_requirements()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    all_ok = files_ok and static_ok and data_ok and slider_ok
    
    if all_ok:
        print("\n✓ All checks passed!")
        print("\n🚀 Ready to test!")
        print("\nNext steps:")
        print("  1. Make sure development server is running:")
        print("     python manage.py runserver")
        print("  2. Open browser: http://localhost:8000/")
        print("  3. Scroll to 'Office of the University Alumni Affairs Officials'")
        print("  4. Test navigation:")
        print("     - Click arrow buttons")
        print("     - Click dots")
        print("     - Use keyboard arrows")
        print("     - Swipe on mobile")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
    
    print("\n" + "="*70)
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
