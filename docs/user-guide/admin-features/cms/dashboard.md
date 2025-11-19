# CMS Dashboard

## Overview

The CMS (Content Management System) Dashboard is the central hub for managing all website content in the NORSU Alumni System. It provides quick access to all CMS features and displays statistics about your content.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system

## How to Access

1. Log in to your admin account
2. Navigate to the main menu
3. Click on "CMS" or "Content Management"
4. You will be directed to the CMS Dashboard at `/cms/dashboard/`

Alternatively, you can access the CMS through the Django admin interface:
1. Go to `/admin/`
2. Look for the "CMS" section in the admin panel

## Dashboard Overview

The CMS Dashboard displays:

### Content Statistics

The dashboard shows counts for all content types:
- **Site Configuration**: Number of site config entries (typically 1)
- **Page Sections**: Active page sections on the website
- **Staff Members**: Active staff member profiles
- **Timeline Items**: Active timeline entries
- **Contact Information**: Active contact info entries
- **FAQs**: Active frequently asked questions
- **Features**: Active feature showcase items
- **Testimonials**: Active testimonial entries
- **About Page Configuration**: About page config entries (typically 1)
- **Alumni Statistics**: Active statistic displays

### Recent Content

Quick access to recently modified content:
- Recent page sections (last 5 modified)
- Recent FAQs (last 5 modified)

### Navigation Links

The dashboard provides quick links to manage:
- Site Configuration
- Page Sections
- Staff Members
- Timeline Items
- Contact Information
- FAQs
- Features Showcase
- Testimonials
- About Page Configuration
- Alumni Statistics

## Key Features

### 1. Content Overview
- View counts of all content types at a glance
- Identify areas that need attention
- Track content growth over time

### 2. Quick Access
- Direct links to all CMS management pages
- Recently modified content for quick editing
- Streamlined navigation

### 3. Content Management
From the dashboard, you can:
- Create new content entries
- Edit existing content
- View content lists
- Delete content (with confirmation)

## Navigation Guide

### From Dashboard to Content Management

**To manage Site Configuration:**
1. Click "Site Configuration" or "Edit Site Config"
2. Update site-wide settings
3. Save changes

**To manage Page Sections:**
1. Click "Page Sections" or "Manage Sections"
2. View list of all page sections
3. Create, edit, or delete sections

**To manage Staff Members:**
1. Click "Staff Members"
2. View list of all staff profiles
3. Add, edit, or remove staff members

**To manage Timeline Items:**
1. Click "Timeline Items"
2. View university history timeline
3. Add, edit, or remove timeline entries

**To manage Contact Information:**
1. Click "Contact Information"
2. View all contact entries
3. Add, edit, or remove contact info

**To manage FAQs:**
1. Click "FAQs"
2. View all frequently asked questions
3. Add, edit, or remove FAQ entries

**To manage Features:**
1. Click "Features" or "Features Showcase"
2. View all feature items
3. Add, edit, or remove features

**To manage Testimonials:**
1. Click "Testimonials"
2. View all testimonial entries
3. Add, edit, or remove testimonials

**To manage About Page:**
1. Click "About Page Configuration"
2. Update about page content
3. Save changes

**To manage Alumni Statistics:**
1. Click "Alumni Statistics"
2. View all statistic displays
3. Add, edit, or remove statistics

## Tips and Best Practices

1. **Regular Updates**: Check the dashboard regularly to keep content fresh
2. **Content Review**: Use the recent content section to review latest changes
3. **Organized Workflow**: Work through one content type at a time
4. **Preview Changes**: Always preview changes on the live site after updates
5. **Backup Important Content**: Keep backups of important text content before major edits

## Troubleshooting

### Cannot Access Dashboard

**Issue**: Dashboard page doesn't load or shows permission error

**Solutions**:
- Verify you're logged in with an admin account
- Check that your account has staff privileges
- Contact system administrator to verify permissions
- Clear browser cache and try again

### Statistics Not Updating

**Issue**: Content counts don't reflect recent changes

**Solutions**:
- Refresh the page (F5 or Ctrl+R)
- Clear browser cache
- Check if changes were actually saved
- Verify content is marked as "active"

### Links Not Working

**Issue**: Navigation links lead to error pages

**Solutions**:
- Verify URL configuration is correct
- Check that CMS URLs are properly configured in `urls.py`
- Contact system administrator if issue persists

### Missing Content Types

**Issue**: Some content management options are not visible

**Solutions**:
- Verify your permission level
- Check if features are enabled in system configuration
- Contact administrator to enable missing features

## Related Features

- [Site Configuration](site-configuration.md) - Manage global site settings
- [Page Sections Management](page-sections.md) - Manage page content sections
- [Staff Members Management](staff-members.md) - Manage staff profiles
- [Timeline Management](timeline.md) - Manage university timeline
- [Contact Information Management](contact-info.md) - Manage contact details
- [FAQ Management](faq.md) - Manage frequently asked questions
- [Features Showcase Management](features.md) - Manage feature displays
- [Testimonials Management](testimonials.md) - Manage testimonials
- [About Page Configuration](about-page.md) - Configure about page
- [Alumni Statistics Management](statistics.md) - Manage statistics display

## Screenshots

> **Note**: Screenshots should be added showing:
> - CMS Dashboard main view with statistics
> - Navigation menu highlighting CMS access
> - Content statistics section
> - Recent content section
> - Quick action buttons
