"""
Visual verification of aspect ratio preservation in exports
Creates sample PDF and Excel files for manual inspection
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.export_utils import ExportMixin
from PIL import Image

User = get_user_model()


def create_sample_exports():
    """Create sample PDF and Excel exports for visual verification"""
    
    print("=" * 80)
    print("Creating Sample Exports for Visual Verification")
    print("=" * 80)
    
    # Get or create test users
    users = User.objects.all()[:10]
    
    if users.count() == 0:
        print("\nCreating test users...")
        for i in range(5):
            User.objects.create_user(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                first_name=f'Test{i}',
                last_name=f'User{i}'
            )
        users = User.objects.all()[:10]
    
    print(f"\n✓ Using {users.count()} users for test data")
    
    mixin = ExportMixin()
    
    # Create PDF export (portrait)
    print("\n" + "-" * 80)
    print("Creating Portrait PDF Export")
    print("-" * 80)
    
    pdf_response = mixin.export_pdf(
        queryset=users,
        filename='test_aspect_ratio_portrait',
        field_names=['id', 'username', 'email', 'first_name', 'last_name'],
        field_labels=['ID', 'Username', 'Email', 'First Name', 'Last Name'],
        title='Portrait PDF - Aspect Ratio Test'
    )
    
    with open('test_aspect_ratio_portrait.pdf', 'wb') as f:
        f.write(pdf_response.content)
    
    print(f"✓ Created: test_aspect_ratio_portrait.pdf ({len(pdf_response.content)} bytes)")
    
    # Create PDF export (landscape)
    print("\n" + "-" * 80)
    print("Creating Landscape PDF Export")
    print("-" * 80)
    
    pdf_landscape_response = mixin.export_pdf(
        queryset=users,
        filename='test_aspect_ratio_landscape',
        field_names=[
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ],
        field_labels=[
            'ID', 'Username', 'Email', 'First Name', 'Last Name',
            'Active', 'Staff', 'Superuser', 'Date Joined', 'Last Login'
        ],
        title='Landscape PDF - Aspect Ratio Test'
    )
    
    with open('test_aspect_ratio_landscape.pdf', 'wb') as f:
        f.write(pdf_landscape_response.content)
    
    print(f"✓ Created: test_aspect_ratio_landscape.pdf ({len(pdf_landscape_response.content)} bytes)")
    
    # Create Excel export
    print("\n" + "-" * 80)
    print("Creating Excel Export")
    print("-" * 80)
    
    excel_response = mixin.export_excel(
        queryset=users,
        filename='test_aspect_ratio',
        field_names=['id', 'username', 'email', 'first_name', 'last_name'],
        field_labels=['ID', 'Username', 'Email', 'First Name', 'Last Name'],
        sheet_name='Aspect Ratio Test'
    )
    
    with open('test_aspect_ratio.xlsx', 'wb') as f:
        f.write(excel_response.content)
    
    print(f"✓ Created: test_aspect_ratio.xlsx ({len(excel_response.content)} bytes)")
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION INSTRUCTIONS")
    print("=" * 80)
    print("\nPlease manually verify the following:")
    print("\n1. PDF Files (portrait and landscape):")
    print("   - Open test_aspect_ratio_portrait.pdf")
    print("   - Open test_aspect_ratio_landscape.pdf")
    print("   - Check that the NORSU logo appears in the header")
    print("   - Verify the logo is NOT distorted (should be square)")
    print("   - Verify the logo fits within the header area")
    print("   - Check that institutional text appears next to logo")
    print("   - Verify separator line appears below header")
    print("\n2. Excel File:")
    print("   - Open test_aspect_ratio.xlsx")
    print("   - Check that the NORSU logo appears in cell A1")
    print("   - Verify the logo is NOT distorted (should be square)")
    print("   - Verify the logo fits within the cell")
    print("   - Check that institutional text appears in cells B1:D1")
    print("   - Check that system name appears in cells B2:D2")
    print("   - Verify data headers start at row 4")
    print("\n3. Aspect Ratio:")
    print("   - The logo should maintain its original square aspect ratio")
    print("   - No stretching or squashing should be visible")
    print("   - Logo should be clear and not pixelated")
    print("\n✅ Sample files created successfully!")
    print("\nFiles created:")
    print("  - test_aspect_ratio_portrait.pdf")
    print("  - test_aspect_ratio_landscape.pdf")
    print("  - test_aspect_ratio.xlsx")
    
    return True


if __name__ == '__main__':
    success = create_sample_exports()
    sys.exit(0 if success else 1)
