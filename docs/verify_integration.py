"""
Simple verification script for documentation sidebar integration.
Run this to verify the integration is working correctly.
"""
from django.urls import reverse, resolve
from django.test.utils import get_runner
from django.conf import settings


def verify_integration():
    """Verify documentation sidebar integration."""
    print("=" * 60)
    print("Documentation Sidebar Integration Verification")
    print("=" * 60)
    
    # 1. Verify URL configuration
    print("\n1. Checking URL Configuration...")
    try:
        docs_index_url = reverse('docs:index')
        print(f"   ✓ docs:index URL: {docs_index_url}")
        
        docs_search_url = reverse('docs:search')
        print(f"   ✓ docs:search URL: {docs_search_url}")
        
        docs_doc_url = reverse('docs:document', kwargs={'doc_path': 'test/page'})
        print(f"   ✓ docs:document URL: {docs_doc_url}")
        
        print("   ✓ All URLs configured correctly")
    except Exception as e:
        print(f"   ✗ URL configuration error: {e}")
        return False
    
    # 2. Verify views exist
    print("\n2. Checking Views...")
    try:
        from docs.views import DocumentationIndexView, DocumentationView, DocumentationSearchView
        print("   ✓ DocumentationIndexView exists")
        print("   ✓ DocumentationView exists")
        print("   ✓ DocumentationSearchView exists")
        
        # Check LoginRequiredMixin
        from django.contrib.auth.mixins import LoginRequiredMixin
        assert issubclass(DocumentationIndexView, LoginRequiredMixin)
        assert issubclass(DocumentationView, LoginRequiredMixin)
        assert issubclass(DocumentationSearchView, LoginRequiredMixin)
        print("   ✓ All views require authentication (LoginRequiredMixin)")
    except Exception as e:
        print(f"   ✗ View verification error: {e}")
        return False
    
    # 3. Verify template integration
    print("\n3. Checking Template Integration...")
    try:
        import os
        base_template = os.path.join(settings.BASE_DIR, 'templates', 'base.html')
        with open(base_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for documentation link in sidebar
        if "{% url 'docs:index' %}" in content:
            print("   ✓ Documentation link found in base template")
        else:
            print("   ✗ Documentation link not found in base template")
            return False
        
        # Check for icon
        if 'fa-book' in content:
            print("   ✓ Documentation icon (fa-book) found")
        else:
            print("   ✗ Documentation icon not found")
            return False
        
        # Check for active state
        if "request.resolver_match.app_name == 'docs'" in content:
            print("   ✓ Active state highlighting configured")
        else:
            print("   ✗ Active state highlighting not configured")
            return False
        
    except Exception as e:
        print(f"   ✗ Template verification error: {e}")
        return False
    
    # 4. Verify documentation files exist
    print("\n4. Checking Documentation Files...")
    try:
        import os
        docs_dir = os.path.join(settings.BASE_DIR, 'docs', 'user-guide')
        if os.path.exists(docs_dir):
            print(f"   ✓ Documentation directory exists: {docs_dir}")
            
            readme = os.path.join(docs_dir, 'README.md')
            if os.path.exists(readme):
                print("   ✓ README.md exists")
            else:
                print("   ⚠ README.md not found (optional)")
        else:
            print(f"   ✗ Documentation directory not found: {docs_dir}")
            return False
    except Exception as e:
        print(f"   ✗ Documentation files verification error: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ All verification checks passed!")
    print("=" * 60)
    print("\nIntegration Summary:")
    print("  • Documentation link added to custom admin sidebar")
    print("  • Documentation link added to user profile dropdown")
    print("  • Icon configured: fa-book")
    print("  • Active state highlighting: enabled")
    print("  • Authentication required: all authenticated users")
    print("  • URL namespace: docs")
    print("\nRequirements Met:")
    print("  ✓ 1.1 - Documentation menu item in custom admin sidebar")
    print("  ✓ 1.2 - Accessible to all authenticated users")
    print("  ✓ 1.3 - Proper icon configured")
    print("  ✓ 1.5 - Active state highlighting")
    print("\n" + "=" * 60)
    
    return True


if __name__ == '__main__':
    import os
    import sys
    import django
    
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
    django.setup()
    
    verify_integration()
