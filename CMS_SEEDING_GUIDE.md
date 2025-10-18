# CMS Content Seeding Guide

This guide explains how to add default content to your CMS models when you have an empty database, and how to handle this in different deployment scenarios including Render.

## Overview

The CMS seeding system provides multiple ways to populate your database with default content:

1. **Management Command Seeding** - Programmatic creation of default content
2. **Django Fixtures** - JSON-based data loading
3. **Render Integration** - Automatic seeding during deployment

## Available Commands

### 1. Seed CMS Content Command

The main command for seeding your CMS with default content:

```bash
python manage.py seed_cms_content
```

#### Options:
- `--force`: Force seeding even if content already exists (overwrites existing data)
- `--skip-existing`: Skip models that already have content (recommended for production)

#### Examples:
```bash
# Seed with default content, skip if already exists
python manage.py seed_cms_content --skip-existing

# Force seed (overwrites existing content)
python manage.py seed_cms_content --force

# Seed only if database is completely empty
python manage.py seed_cms_content
```

### 2. Create Fixtures Command

Export existing CMS content to fixture files:

```bash
python manage.py create_cms_fixtures
```

#### Options:
- `--output-dir`: Directory to save fixture files (default: `cms/fixtures/`)
- `--format`: Fixture format - json, xml, or yaml (default: json)

#### Examples:
```bash
# Create fixtures in default location
python manage.py create_cms_fixtures

# Create fixtures in custom directory
python manage.py create_cms_fixtures --output-dir my_fixtures/

# Create XML fixtures
python manage.py create_cms_fixtures --format xml
```

### 3. Load Fixtures Command

Load CMS content from fixture files:

```bash
python manage.py load_cms_fixtures
```

#### Options:
- `--fixtures-dir`: Directory containing fixture files (default: `cms/fixtures/`)
- `--fixture-files`: Specific fixture files to load
- `--clear`: Clear existing data before loading (not implemented for safety)

#### Examples:
```bash
# Load all fixtures from default directory
python manage.py load_cms_fixtures

# Load specific fixture files
python manage.py load_cms_fixtures --fixture-files site_config.json features.json

# Load from custom directory
python manage.py load_cms_fixtures --fixtures-dir my_fixtures/
```

## What Gets Seeded

The seeding command creates default content for all CMS models:

### Site Configuration
- Site name, tagline, and branding
- Contact information (email, phone, address)
- Social media links
- Button text customization

### Page Sections
- Hero section with welcome message
- Features section introduction
- Testimonials section header
- Call-to-action section

### Static Pages
- About Us page with mission, vision, values
- Contact Us page with office hours
- Privacy Policy template
- Terms of Service template

### Features
- Professional Networking
- Career Opportunities
- Alumni Events
- Knowledge Sharing
- Mentorship Program
- Alumni Directory

### Testimonials
- Sample testimonials from fictional alumni
- Professional success stories
- Network benefits examples

### Staff Members
- Alumni Relations Director
- Alumni Coordinator
- Contact information and bios

### Timeline Items
- University founding (2004)
- First alumni reunion (2010)
- Network launch (2015)
- Virtual events initiative (2020)

### Contact Information
- Primary email, phone, address
- Office hours
- Response time information

### FAQs
- Common questions about joining
- Membership fees
- Profile updates
- Finding alumni
- Job postings
- Mentorship programs

## Render Deployment Integration

### Automatic Seeding

The seeding command is automatically integrated into your Render deployment:

#### In `render.yaml`:
```yaml
buildCommand: |
  pip install -r requirements.txt
  python manage.py collectstatic --noinput
  python manage.py migrate --noinput
  python manage.py seed_cms_content --skip-existing
```

#### In `build.sh`:
```bash
# Seed CMS content (skip if already exists)
echo "🌱 Seeding CMS content..."
python manage.py seed_cms_content --skip-existing
```

### Environment Variables

You can control seeding behavior with environment variables:

```yaml
envVars:
  - key: SEED_CMS_CONTENT
    value: "true"  # Enable/disable seeding
  - key: FORCE_SEED_CMS
    value: "false" # Force overwrite existing content
```

### Custom Build Commands

For different deployment scenarios, you can customize the build command:

#### Development/Staging:
```yaml
buildCommand: |
  pip install -r requirements.txt
  python manage.py collectstatic --noinput
  python manage.py migrate --noinput
  python manage.py seed_cms_content --force
```

#### Production:
```yaml
buildCommand: |
  pip install -r requirements.txt
  python manage.py collectstatic --noinput
  python manage.py migrate --noinput
  python manage.py seed_cms_content --skip-existing
```

## Local Development

### First Time Setup

When setting up the project locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed with default content
python manage.py seed_cms_content

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Resetting Content

To reset CMS content to defaults:

```bash
# Clear and reseed
python manage.py seed_cms_content --force
```

### Creating Custom Fixtures

1. Set up your content through the admin interface
2. Export to fixtures:
   ```bash
   python manage.py create_cms_fixtures
   ```
3. Customize the generated JSON files
4. Load your custom fixtures:
   ```bash
   python manage.py load_cms_fixtures
   ```

## Best Practices

### For Development
- Use `--force` when you want to reset content
- Create custom fixtures for your specific content
- Test seeding commands before deploying

### For Production
- Always use `--skip-existing` to avoid overwriting user content
- Test seeding in staging environment first
- Monitor deployment logs for seeding errors

### For Staging
- Use `--force` to ensure consistent test data
- Create staging-specific fixtures
- Automate seeding in CI/CD pipeline

## Troubleshooting

### Common Issues

1. **Seeding fails during deployment**
   - Check that all CMS models are properly migrated
   - Verify database permissions
   - Review deployment logs for specific errors

2. **Content not appearing**
   - Ensure `is_active=True` for content that should be visible
   - Check template context variables
   - Verify model relationships

3. **Duplicate content**
   - Use `--skip-existing` to avoid duplicates
   - Check for existing data before seeding
   - Use `--force` to replace existing content

### Debug Commands

```bash
# Check if content exists
python manage.py shell -c "from cms.models import *; print('SiteConfig:', SiteConfig.objects.count())"

# Test seeding without saving
python manage.py seed_cms_content --dry-run  # (if implemented)

# Check fixture files
python manage.py load_cms_fixtures --fixture-files site_config.json --verbosity=2
```

## Customization

### Adding New Default Content

1. Edit `cms/management/commands/seed_cms_content.py`
2. Add new data to the appropriate `seed_*` method
3. Test locally before deploying

### Creating Custom Fixtures

1. Create JSON files in `cms/fixtures/`
2. Follow Django fixture format
3. Use `load_cms_fixtures` command to load them

### Environment-Specific Content

You can modify the seeding command to load different content based on environment:

```python
# In seed_cms_content.py
if settings.DEBUG:
    # Development content
    content = dev_content
else:
    # Production content
    content = prod_content
```

## Security Considerations

- Never include sensitive information in fixtures
- Use environment variables for production-specific data
- Validate all seeded content before deployment
- Consider data privacy when seeding user-related content

## Performance

- Seeding is typically fast for small datasets
- For large datasets, consider using fixtures instead
- Monitor deployment time impact
- Use `--skip-existing` to avoid unnecessary operations

This seeding system ensures your CMS always has meaningful default content, making it easier to deploy and maintain your alumni network application.
