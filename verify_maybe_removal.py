#!/usr/bin/env python
"""
Quick verification script to check that "maybe" RSVPs have been removed.
Run with: python verify_maybe_removal.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from events.models import EventRSVP

def verify_maybe_removal():
    """Verify that no 'maybe' RSVPs exist in the database."""
    
    print("=" * 60)
    print("RSVP 'Maybe' Option Removal Verification")
    print("=" * 60)
    
    # Check for any remaining 'maybe' RSVPs
    maybe_count = EventRSVP.objects.filter(status='maybe').count()
    
    print(f"\n1. Checking for 'maybe' RSVPs...")
    if maybe_count == 0:
        print("   ✓ No 'maybe' RSVPs found (expected)")
    else:
        print(f"   ✗ Found {maybe_count} 'maybe' RSVPs (unexpected!)")
    
    # Check total RSVP counts
    total_rsvps = EventRSVP.objects.count()
    yes_count = EventRSVP.objects.filter(status='yes').count()
    no_count = EventRSVP.objects.filter(status='no').count()
    
    print(f"\n2. RSVP Statistics:")
    print(f"   Total RSVPs: {total_rsvps}")
    print(f"   Attending (yes): {yes_count}")
    print(f"   Not Attending (no): {no_count}")
    
    # Verify all RSVPs are accounted for
    if yes_count + no_count == total_rsvps:
        print("   ✓ All RSVPs accounted for")
    else:
        print(f"   ✗ Mismatch: {yes_count + no_count} != {total_rsvps}")
    
    # Check model choices
    print(f"\n3. Model Choices:")
    choices = EventRSVP.RSVP_CHOICES
    print(f"   Available choices: {choices}")
    
    has_maybe = any(choice[0] == 'maybe' for choice in choices)
    if not has_maybe:
        print("   ✓ 'maybe' option removed from model")
    else:
        print("   ✗ 'maybe' option still in model (unexpected!)")
    
    print("\n" + "=" * 60)
    
    if maybe_count == 0 and not has_maybe and yes_count + no_count == total_rsvps:
        print("✓ VERIFICATION PASSED: 'Maybe' option successfully removed")
    else:
        print("✗ VERIFICATION FAILED: Issues detected")
    
    print("=" * 60)

if __name__ == '__main__':
    verify_maybe_removal()
