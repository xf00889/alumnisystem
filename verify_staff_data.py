"""
Verification script to display seeded staff data.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from cms.models import StaffMember
from colorama import Fore, Style, init

init(autoreset=True)

def main():
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}NORSU ALUMNI AFFAIRS - STAFF & COORDINATORS")
    print(f"{Fore.CYAN}{'=' * 80}\n")
    
    staff_members = StaffMember.objects.filter(is_active=True).order_by('order', 'name')
    
    if not staff_members.exists():
        print(f"{Fore.RED}[!] No staff members found in database.")
        print(f"{Fore.YELLOW}[!] Run 'python manage.py seed_staff_data' to populate staff data.\n")
        return
    
    # Group by category
    president = staff_members.filter(order=0)
    staff = staff_members.filter(order__gte=1, order__lte=9)
    coordinators = staff_members.filter(order__gte=10)
    
    # Display University President
    if president.exists():
        print(f"{Fore.YELLOW}{'─' * 80}")
        print(f"{Fore.YELLOW}UNIVERSITY LEADERSHIP")
        print(f"{Fore.YELLOW}{'─' * 80}\n")
        
        for member in president:
            print(f"{Fore.GREEN}[✓] {member.name}")
            print(f"    Position: {member.position}")
            print(f"    Department: {member.department}")
            if member.email:
                print(f"    Email: {member.email}")
            print(f"    Bio: {member.bio[:150]}...")
            print()
    
    # Display Alumni Affairs Staff
    if staff.exists():
        print(f"{Fore.YELLOW}{'─' * 80}")
        print(f"{Fore.YELLOW}OFFICE OF ALUMNI AFFAIRS")
        print(f"{Fore.YELLOW}{'─' * 80}\n")
        
        for member in staff:
            print(f"{Fore.GREEN}[✓] {member.name}")
            print(f"    Position: {member.position}")
            print(f"    Department: {member.department}")
            if member.email:
                print(f"    Email: {member.email}")
            print()
    
    # Display Campus Coordinators
    if coordinators.exists():
        print(f"{Fore.YELLOW}{'─' * 80}")
        print(f"{Fore.YELLOW}NORSU ALUMNI COORDINATORS")
        print(f"{Fore.YELLOW}{'─' * 80}\n")
        
        for member in coordinators:
            print(f"{Fore.GREEN}[✓] {member.name}")
            print(f"    Position: {member.position}")
            print(f"    Department: {member.department}")
            print()
    
    # Summary
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}SUMMARY")
    print(f"{Fore.CYAN}{'=' * 80}\n")
    print(f"{Fore.GREEN}  Total Staff Members: {staff_members.count()}")
    print(f"{Fore.GREEN}  - University Leadership: {president.count()}")
    print(f"{Fore.GREEN}  - Alumni Affairs Staff: {staff.count()}")
    print(f"{Fore.GREEN}  - Campus Coordinators: {coordinators.count()}")
    print()

if __name__ == '__main__':
    main()
