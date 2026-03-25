# Deployment Guide - College and Program Updates

## Changes Made
- Updated all college names to official NORSU naming
- Added 45+ programs from NORSU Main Campus
- All programs now available at all campuses
- Removed campus-specific restrictions

## Deployment Steps

### On Production Server (via SSH):

```bash
# 1. Navigate to project directory
cd /path/to/alumnisystem

# 2. Pull latest changes from git
git pull origin main

# 3. Activate virtual environment (if using one)
source venv/bin/activate  # or your venv path

# 4. Run migrations
python manage.py migrate

# 5. Collect static files (if needed)
python manage.py collectstatic --noinput

# 6. Restart the application
# For Gunicorn:
sudo systemctl restart gunicorn
# OR
sudo supervisorctl restart alumnisystem

# For Render.com (automatic):
# Just push to git, Render will auto-deploy
```

### Verify Deployment:

1. Go to https://norsualumni.com/alumni/management/
2. Click "Export" button
3. Check that:
   - Colleges show updated names (e.g., "College of Business" not "College of Business Administration")
   - Programs list shows 45+ programs sorted alphabetically
   - All new programs are visible (Chemistry, Geology, Mass Communication, etc.)

### Expected Results:

**Colleges (10 total):**
- College of Arts and Sciences
- College of Business
- College of Agriculture, Forestry and Fisheries
- College of Criminal Justice Education
- College of Engineering
- College of Industrial Technology
- College of Law
- College of Nursing, Pharmacy and Allied Health Sciences
- College of Education
- College of Tourism and Hospitality Management

**Programs (45+ total):**
All programs from NORSU Main Campus including:
- BS in Chemistry, Geology, Mass Communication (new)
- BS in Computer Engineering, ECE, Geodetic, Geothermal Engineering (new)
- BS in Aviation Maintenance, Civil Technology, Food Technology (new)
- BS in Agriculture with majors (Agronomy, Horticulture, Animal Science, Ag Extension)
- And many more...

### Troubleshooting:

If changes don't appear:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Check server logs: `tail -f /var/log/gunicorn/error.log`
3. Verify migrations ran: `python manage.py showmigrations alumni_directory`
4. Restart server again
5. Check if static files are served correctly

### Rollback (if needed):

```bash
# Revert to previous commit
git log  # Find previous commit hash
git revert <commit-hash>
python manage.py migrate alumni_directory <previous-migration-number>
sudo systemctl restart gunicorn
```

## Files Changed:
- `alumni_directory/models.py` - Updated COLLEGE_CHOICES
- `accounts/forms.py` - Updated COURSES_BY_COLLEGE and PROGRAMS_BY_CAMPUS
- `templates/accounts/post_registration.html` - Updated JavaScript mappings
- `alumni_directory/migrations/0005_update_colleges_and_programs.py` - New migration

## Database Changes:
- Alumni.college field choices updated
- No data loss - existing records remain unchanged
- New programs available for selection
