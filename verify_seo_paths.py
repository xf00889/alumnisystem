"""
Script to verify that all PageSEO entries match actual URL patterns.

This script checks if the page_path in PageSEO database entries
correspond to actual URL patterns defined in the Django URL configuration.

Usage:
    python verify_seo_paths.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.urls import get_resolver
from core.models.seo import PageSEO
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

def get_all_url_patterns():
    """Extract all URL patterns from Django URL configuration."""
    resolver = get_resolver()
    url_patterns = []
    
    def extract_patterns(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                # This is an include(), recurse into it
                new_prefix = prefix + str(pattern.pattern)
                extract_patterns(pattern.url_patterns, new_prefix)
            else:
                # This is a regular URL pattern
                full_pattern = prefix + str(pattern.pattern)
                # Clean up the pattern
                full_pattern = full_pattern.replace('^', '').replace('$', '')
                if not full_pattern.startswith('/'):
                    full_pattern = '/' + full_pattern
                url_patterns.append(full_pattern)
    
    extract_patterns(resolver.url_patterns)
    return url_patterns

def main():
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}SEO PATH VERIFICATION")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # Get all PageSEO entries
    seo_entries = PageSEO.objects.all()
    
    if not seo_entries:
        print(f"{Fore.YELLOW}[!] No PageSEO entries found in database.")
        print(f"{Fore.YELLOW}[!] Run 'python manage.py seed_seo_data' to populate SEO data.\n")
        return
    
    # Known URL patterns (manually verified)
    known_urls = {
        '/': 'Home page',
        '/about-us/': 'About Us page',
        '/contact-us/': 'Contact Us page',
        '/news/': 'News landing page',
        '/landing/events/': 'Events landing page',
        '/landing/announcements/': 'Announcements landing page',
        '/alumni/': 'Alumni directory',
        '/jobs/': 'Job board',
        '/mentorship/': 'Mentorship program',
        '/groups/': 'Alumni groups',
        '/donations/': 'Donations (redirects to campaigns)',
        '/donations/campaigns/': 'Donation campaigns',
        '/accounts/login/': 'Login page',
        '/accounts/signup/': 'Signup page',
    }
    
    print(f"{Fore.CYAN}[*] Checking {len(seo_entries)} PageSEO entries...\n")
    print(f"{'-'*70}\n")
    
    valid_count = 0
    invalid_count = 0
    warnings_count = 0
    
    for seo in seo_entries:
        page_path = seo.page_path
        
        if page_path in known_urls:
            valid_count += 1
            print(f"{Fore.GREEN}[✓] {page_path:<30} → {known_urls[page_path]}")
        else:
            # Check if it's a pattern that might be valid but not in our known list
            if any(pattern in page_path for pattern in ['/events/', '/jobs/', '/alumni/', '/groups/', '/mentorship/', '/donations/']):
                warnings_count += 1
                print(f"{Fore.YELLOW}[?] {page_path:<30} → Might be valid (not in known URLs)")
            else:
                invalid_count += 1
                print(f"{Fore.RED}[✗] {page_path:<30} → URL pattern not found!")
    
    # Summary
    print(f"\n{'-'*70}\n")
    print(f"{Fore.CYAN}[*] VERIFICATION SUMMARY")
    print(f"{'-'*70}")
    print(f"{Fore.GREEN}[✓] Valid paths:   {valid_count}")
    if warnings_count > 0:
        print(f"{Fore.YELLOW}[?] Warnings:      {warnings_count}")
    if invalid_count > 0:
        print(f"{Fore.RED}[✗] Invalid paths: {invalid_count}")
    print(f"{'='*70}\n")
    
    # Recommendations
    if invalid_count > 0:
        print(f"{Fore.YELLOW}[!] RECOMMENDATIONS:")
        print(f"{Fore.YELLOW}    1. Run 'python manage.py fix_seo_paths' to fix known path mismatches")
        print(f"{Fore.YELLOW}    2. Manually update invalid paths in the admin panel")
        print(f"{Fore.YELLOW}    3. Or run 'python manage.py seed_seo_data' to reset with correct paths\n")
    else:
        print(f"{Fore.GREEN}[✓] All SEO paths are valid!\n")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n{Fore.RED}[✗] Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
