# NORSU Alumni Affairs Staff Seeder

## Overview

This document describes the staff data seeding command for the NORSU Alumni System. The command populates the `StaffMember` model with official NORSU Alumni Affairs personnel.

## Command Usage

### Basic Usage
```bash
python manage.py seed_staff_data
```

### Clear Existing Data Before Seeding
```bash
python manage.py seed_staff_data --clear
```

## Seeded Data Structure

### 1. University Leadership (Order: 0)
- **Dr. Noel Marjon E. Yasi** - University President

### 2. Office of Alumni Affairs (Order: 1-3)
- **Pio S. Sapat, Ph.D.** - Director, Alumni Affairs
- **Sandra S. Balansag, RCrim, MSCJ-Crim** - Staff, Alumni Affairs
- **Urcisciano B. Bato, BSIT** - Technician, Alumni Affairs

### 3. NORSU Alumni Coordinators (Order: 10-22)

#### College Coordinators
- **Dr. Jacel Angeline V. Lingcong** - CAS-Coordinator (College of Arts and Sciences)
- **Prof. Cynie T. Antique** - CBA-Coordinator (College of Business Administration)
- **Mr. Dante A. Capistrano** - CCJE-Coordinator (College of Criminal Justice Education)
- **Engr. Angel M. Honculada** - CEA-Coordinators (College of Engineering and Architecture)
- **Dr. Judy A. Cornelia** - CED-Coordinator (College of Education)
- **Prof. Geo Rey A. Tajada** - CIT-Coordinator (College of Information Technology)
- **Mr. Teresito A. Tabinas** - CAFF/Pamplona Campus-Coordinator (College of Agriculture, Forestry and Food Science)
- **Dr. Novalisa A. Leon** - CNPAHS-Coordinator (College of Nursing and Allied Health Sciences)

#### Campus Coordinators
- **Ms. Lorna A. Labe** - Bayawan-Sta Catalina Campus-Coordinator
- **Prof. Vivian Altamarino** - Bais Campuses I & II-Coordinator
- **Prof. Jed Christian L. Cece** - Guihulngan Campus-Coordinator
- **Ms. Marecel T. Sayre** - Siaton Campus-Coordinator
- **Ms. Divina R. Bulay** - Mabinay Campus-Coordinator

## Features

### ✅ Idempotent Operation
- Safe to run multiple times
- Uses `update_or_create` to prevent duplicates
- Updates existing records with new data

### ✅ Organized Hierarchy
- Order field ensures proper display sequence
- President (0) → Staff (1-3) → Coordinators (10-22)

### ✅ Complete Information
- Full names with titles and credentials
- Position and department details
- Professional biographies
- Contact information (where available)

### ✅ Audit Trail
- All operations are logged
- CREATE and UPDATE actions tracked
- Timestamp information preserved

## Verification

### View Seeded Data
```bash
python verify_staff_data.py
```

### Check in Django Admin
1. Navigate to: `/admin/cms/staffmember/`
2. View all staff members organized by order
3. Edit or add new staff members as needed

### Query in Django Shell
```python
from cms.models import StaffMember

# Get all active staff
staff = StaffMember.objects.filter(is_active=True).order_by('order')

# Get by category
president = staff.filter(order=0)
alumni_staff = staff.filter(order__gte=1, order__lte=9)
coordinators = staff.filter(order__gte=10)

# Display
for member in staff:
    print(f"{member.name} - {member.position}")
```

## Data Source

The staff data is based on official NORSU Alumni Affairs documentation:
- Alumni Affairs Office organizational structure
- Campus coordinator assignments
- University leadership information

## Maintenance

### Adding New Staff Members
1. Edit `cms/management/commands/seed_staff_data.py`
2. Add new entry to appropriate data list (STAFF_DATA or COORDINATORS_DATA)
3. Run the command: `python manage.py seed_staff_data`

### Updating Existing Staff
1. Modify the data in the command file
2. Re-run the command (it will update existing records)

### Removing Staff Members
- Set `is_active=False` in the data
- Or use `--clear` flag and re-seed with updated data

## Integration

### Display on Website
Staff members can be displayed on:
- About Us page
- Contact Us page
- Alumni Affairs page
- Staff directory

### Template Usage
```django
{% load static %}

<div class="staff-section">
    <h2>Office of Alumni Affairs</h2>
    {% for member in staff_members %}
        <div class="staff-card">
            {% if member.image %}
                <img src="{{ member.image.url }}" alt="{{ member.name }}">
            {% endif %}
            <h3>{{ member.name }}</h3>
            <p class="position">{{ member.position }}</p>
            <p class="department">{{ member.department }}</p>
            {% if member.email %}
                <a href="mailto:{{ member.email }}">{{ member.email }}</a>
            {% endif %}
        </div>
    {% endfor %}
</div>
```

### View Usage
```python
from cms.models import StaffMember

def about_view(request):
    staff_members = StaffMember.objects.filter(
        is_active=True
    ).order_by('order', 'name')
    
    context = {
        'staff_members': staff_members,
    }
    return render(request, 'about.html', context)
```

## Related Commands

- `python manage.py seed_seo_data` - Seed SEO metadata
- `python manage.py seed_cms_data` - Seed general CMS content
- `python manage.py populate_officials_data` - Seed university officials

## Support

For issues or questions:
- Check Django admin for data verification
- Review audit logs for operation history
- Run verification script for data validation

---

**Last Updated:** March 2, 2026  
**Command Location:** `cms/management/commands/seed_staff_data.py`  
**Model:** `cms.models.StaffMember`
