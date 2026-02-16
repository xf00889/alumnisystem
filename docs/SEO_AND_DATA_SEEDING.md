# SEO and Data Seeding Documentation

## Overview

The NORSU Alumni System includes automated data seeding commands that prepopulate essential configuration and content during deployment. These commands ensure that the system is production-ready immediately after deployment.

## Build Script Integration

The `build.sh` script automatically runs the following seeding commands during deployment on Render:

```bash
# Populate CMS data
python manage.py seed_cms_data

# Populate footer links
python manage.py populate_footer_links

# Populate SEO configuration
python manage.py seed_seo_data

# Populate announcement categories
python manage.py populate_categories

# Populate donation campaign types
python manage.py populate_campaign_types
```

## Available Seeding Commands

### 1. `seed_cms_data`

**Purpose:** Populates CMS models with default organizational data from NORSU Office of Alumni Affairs.

**Location:** `cms/management/commands/seed_cms_data.py`

**What it seeds:**
- Site Configuration (contact info, social media links, branding)
- About Page Configuration (university info, mission, vision)
- Page Sections (hero, features, stats, testimonials, CTA)
- Features (platform capabilities)
- Testimonials (alumni success stories)
- Staff Members (Office of Alumni Affairs team)
- Timeline Items (organizational milestones)
- Contact Information (office details)
- FAQs (frequently asked questions)
- Alumni Statistics (network metrics)

**Usage:**
```bash
python manage.py seed_cms_data
```

**Behavior:** Uses `update_or_create` logic - safe to run multiple times. Existing records will be updated with new data.

### 2. `seed_seo_data`

**Purpose:** Populates SEO configuration for all major pages with optimized meta tags and structured data.

**Location:** `core/management/commands/seed_seo_data.py`

**What it seeds:**
- PageSEO entries for 11 major pages:
  - Homepage (/)
  - About (/about/)
  - Contact (/contact/)
  - Alumni Directory (/alumni/)
  - Events (/events/)
  - Jobs (/jobs/)
  - Mentorship (/mentorship/)
  - Groups (/groups/)
  - Donations (/donations/)
  - Login (/accounts/login/)
  - Signup (/accounts/signup/)
- OrganizationSchema (structured data for Schema.org)

**SEO Fields Configured:**
- Meta title (50-60 characters)
- Meta description (150-160 characters)
- Meta keywords
- Sitemap priority (0.0-1.0)
- Sitemap change frequency
- Canonical URLs
- Open Graph images
- Twitter Card images

**Usage:**
```bash
python manage.py seed_seo_data
```

**Behavior:** Uses `update_or_create` logic - safe to run multiple times.

### 3. `populate_footer_links`

**Purpose:** Creates default footer navigation links organized by section.

**Location:** `cms/management/commands/populate_footer_links.py`

**What it seeds:**
- Quick Links (Home, Events, Announcements, Login, Sign Up)
- Information (About Us, Contact Us, FAQs)
- Legal (Privacy Policy, Terms of Service, Cookie Policy)

**Usage:**
```bash
python manage.py populate_footer_links
```

**Behavior:** Uses `get_or_create` with update logic - safe to run multiple times.

### 4. `populate_categories`

**Purpose:** Creates default announcement categories.

**Location:** `announcements/management/commands/populate_categories.py`

**What it seeds:**
- Campus News
- Events
- Career Opportunities
- Alumni Spotlight
- Fundraising
- Volunteer Opportunities
- Academic Updates
- Community Service

**Usage:**
```bash
python manage.py populate_categories
```

**Behavior:** Uses `get_or_create` - safe to run multiple times.

### 5. `populate_campaign_types`

**Purpose:** Creates default donation campaign types.

**Location:** `donations/management/commands/populate_campaign_types.py`

**What it seeds:**
- Scholarship Fund
- Infrastructure Development
- Research & Innovation
- Student Support
- Alumni Events
- Emergency Relief
- Technology Upgrade
- Community Outreach

**Usage:**
```bash
python manage.py populate_campaign_types
```

**Behavior:** Uses `get_or_create` - safe to run multiple times.

## SEO Configuration Details

### Page SEO Structure

Each PageSEO entry includes:

```python
{
    'page_path': '/',  # URL path
    'meta_title': 'NORSU Alumni Network - Connect, Network, and Grow',  # 50-60 chars
    'meta_description': 'Official alumni platform for Negros Oriental State University...',  # 150-160 chars
    'meta_keywords': 'NORSU alumni, alumni network, ...',
    'sitemap_priority': 1.0,  # 0.0 to 1.0
    'sitemap_changefreq': 'daily',  # always, hourly, daily, weekly, monthly, yearly, never
    'is_active': True,
}
```

### Organization Schema

Provides structured data for search engines:

```python
{
    'name': 'Negros Oriental State University Alumni Network',
    'logo': 'https://norsu-alumni.edu.ph/static/images/norsu-logo.png',
    'url': 'https://norsu-alumni.edu.ph',
    'telephone': '+63-35-422-6002',
    'email': 'alumni@norsu.edu.ph',
    'street_address': 'Kagawasan, Ave. Rizal',
    'address_locality': 'Dumaguete City',
    'address_region': 'Negros Oriental',
    'postal_code': '6200',
    'address_country': 'PH',
}
```

## Manual Execution

All seeding commands can be run manually at any time:

```bash
# Run all seeding commands
python manage.py seed_cms_data
python manage.py populate_footer_links
python manage.py seed_seo_data
python manage.py populate_categories
python manage.py populate_campaign_types

# Or run individually as needed
python manage.py seed_seo_data
```

## Updating Seeded Data

To update the default data:

1. Edit the respective command file in `*/management/commands/`
2. Modify the data dictionaries (e.g., `PAGE_SEO_DATA`, `SITE_CONFIG_DATA`)
3. Run the command manually or redeploy to Render

The commands use `update_or_create` logic, so existing records will be updated with new values.

## Admin Interface

After seeding, all data can be managed through the Django admin interface:

- **CMS Data:** `/admin/cms/`
- **SEO Configuration:** `/admin/core/pageseo/` and `/admin/core/organizationschema/`
- **Footer Links:** `/admin/cms/footerlink/`
- **Announcement Categories:** `/admin/announcements/category/`
- **Campaign Types:** `/admin/donations/campaigntype/`

## Best Practices

1. **Always run seeding commands after migrations** - The build script handles this automatically
2. **Review seeded data in admin** - Customize as needed for your organization
3. **Update SEO data regularly** - Keep meta descriptions and keywords current
4. **Monitor sitemap priorities** - Adjust based on page importance
5. **Test locally first** - Run commands locally before deploying changes

## Troubleshooting

### Command fails during build

Check the Render logs for specific error messages. Common issues:
- Missing migrations (run `python manage.py migrate` first)
- Database connection issues
- Invalid data format

### Data not appearing

1. Check if the command ran successfully in build logs
2. Verify data in Django admin
3. Check if `is_active` flags are set to `True`
4. Clear cache if using caching

### SEO not working

1. Verify PageSEO entries exist for the page path
2. Check that `is_active` is `True`
3. Ensure the SEO context processor is enabled in settings
4. Check template includes SEO meta tags

## Related Files

- `build.sh` - Build script with seeding commands
- `core/models/seo.py` - SEO models
- `cms/models.py` - CMS models
- `core/context_processors.py` - SEO context processor
- `templates/base.html` - Base template with SEO meta tags

## Future Enhancements

Potential improvements:
- Add command to export/import SEO configurations
- Create web UI for managing SEO without admin access
- Add SEO validation and recommendations
- Implement A/B testing for meta descriptions
- Add analytics integration for SEO performance tracking
