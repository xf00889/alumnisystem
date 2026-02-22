#!/usr/bin/env python
"""
Verify New Officials Slider Implementation
Tests that the new Swiper-based slider is properly configured
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from cms.models import StaffMember

def verify_slider():
    """Verify the new slider implementation"""
    print("=" * 70)
    print("OFFICIALS SLIDER VERIFICATION - NEW SWIPER IMPLEMENTATION")
    print("=" * 70)
    
    # Check staff members
    staff_count = StaffMember.objects.filter(is_active=True).count()
    print(f"\n✓ Active Staff Members: {staff_count}")
    
    if staff_count == 0:
        print("\n⚠ WARNING: No active staff members found!")
        print("  The slider will not display. Add staff members via admin.")
        return False
    
    # Check files exist
    files_to_check = [
        ('static/js/officials_slider.js', 'JavaScript'),
        ('static/css/officials_slider.css', 'CSS'),
        ('templates/home.html', 'Template'),
        ('docs/officials-slider-implementation.md', 'Documentation'),
        ('docs/officials-slider-visual-guide.md', 'Visual Guide'),
        ('docs/officials-slider-migration-summary.md', 'Migration Summary')
    ]
    
    print("\n" + "=" * 70)
    print("FILE VERIFICATION")
    print("=" * 70)
    
    all_exist = True
    for filepath, description in files_to_check:
        exists = os.path.exists(filepath)
        status = "✓" if exists else "✗"
        print(f"{status} {description}: {filepath}")
        if not exists:
            all_exist = False
    
    # Check template content
    print("\n" + "=" * 70)
    print("TEMPLATE VERIFICATION")
    print("=" * 70)
    
    with open('templates/home.html', 'r', encoding='utf-8') as f:
        content = f.read()
        
        checks = [
            ('swiper officials-swiper', 'Swiper container class'),
            ('swiper-wrapper', 'Swiper wrapper'),
            ('swiper-slide', 'Swiper slide'),
            ('swiper-button-prev', 'Previous button'),
            ('swiper-button-next', 'Next button'),
            ('swiper-pagination', 'Pagination'),
            ('swiper@11/swiper-bundle.min.css', 'Swiper CSS CDN'),
            ('swiper@11/swiper-bundle.min.js', 'Swiper JS CDN')
        ]
        
        for check_str, description in checks:
            found = check_str in content
            status = "✓" if found else "✗"
            print(f"{status} {description}")
            if not found:
                all_exist = False
    
    # Check JavaScript content
    print("\n" + "=" * 70)
    print("JAVASCRIPT VERIFICATION")
    print("=" * 70)
    
    with open('static/js/officials_slider.js', 'r', encoding='utf-8') as f:
        js_content = f.read()
        
        js_checks = [
            ('new Swiper', 'Swiper initialization'),
            ('slidesPerView', 'Slides per view config'),
            ('breakpoints', 'Responsive breakpoints'),
            ('navigation', 'Navigation config'),
            ('pagination', 'Pagination config'),
            ('keyboard', 'Keyboard navigation'),
            ('a11y', 'Accessibility config'),
            ('lazy', 'Lazy loading')
        ]
        
        for check_str, description in js_checks:
            found = check_str in js_content
            status = "✓" if found else "✗"
            print(f"{status} {description}")
            if not found:
                all_exist = False
    
    # Display staff members
    print("\n" + "=" * 70)
    print("STAFF MEMBERS DATA")
    print("=" * 70)
    
    staff_members = StaffMember.objects.filter(is_active=True).order_by('order', 'name')
    
    for i, staff in enumerate(staff_members, 1):
        print(f"\n{i}. {staff.name}")
        print(f"   Position: {staff.position}")
        if staff.department:
            print(f"   Department: {staff.department}")
        if staff.email:
            print(f"   Email: {staff.email}")
        print(f"   Has Image: {'Yes' if staff.image else 'No'}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    if all_exist and staff_count > 0:
        print("\n✓ ALL CHECKS PASSED!")
        print("\nThe new Swiper-based slider is properly configured.")
        print("\nNext steps:")
        print("1. Run: python manage.py runserver")
        print("2. Visit: http://localhost:8000/")
        print("3. Scroll to 'Meet Our Team' section")
        print("4. Test swipe gestures on mobile")
        print("5. Test keyboard navigation (arrow keys)")
        print("6. Test navigation arrows and dots")
        return True
    else:
        print("\n✗ SOME CHECKS FAILED")
        print("\nPlease review the errors above and fix them.")
        return False

if __name__ == '__main__':
    try:
        success = verify_slider()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
