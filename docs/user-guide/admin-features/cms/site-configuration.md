# Site Configuration

## Overview

Site Configuration allows you to manage global settings for the NORSU Alumni System website. This includes the site name, tagline, logo, contact information, social media links, and button texts that appear throughout the site.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system
- Access to CMS Dashboard

## How to Access

### Method 1: Through CMS Dashboard
1. Navigate to CMS Dashboard (`/cms/dashboard/`)
2. Click on "Site Configuration" or "Edit Site Config"
3. You will be directed to the site configuration form

### Method 2: Through Django Admin
1. Go to `/admin/`
2. Find "CMS" section
3. Click on "Site Configuration"
4. Click on the existing configuration entry

### Method 3: Direct URL
- Navigate directly to `/cms/site-config/`

## Configuration Sections

### Basic Information

**Site Name**
- The name of your website
- Default: "NORSU Alumni Network"
- Appears in page titles, headers, and branding
- Maximum 200 characters

**Site Tagline**
- The main tagline displayed on the homepage
- Default: "Connect. Grow. Succeed."
- Appears in hero sections and promotional materials
- Automatically syncs with hero section title

**Logo**
- Site logo image
- Supported formats: JPG, PNG, GIF
- Recommended size: 200x200 pixels or larger
- Appears in navigation bar and branding areas
- Optional field

### Contact Information

**Contact Email**
- Primary contact email address
- Default: "alumni@norsu.edu.ph"
- Used for general inquiries
- Displayed on contact pages

**Contact Phone**
- Primary contact phone number
- Default: "+63 35 422 6002"
- Include country code for international format
- Maximum 50 characters

**Contact Address**
- Primary physical address
- Default: Full NORSU address
- Supports multi-line text
- Displayed on contact and footer sections

### Social Media Links

Configure your social media presence:

**Facebook URL**
- Link to your Facebook page
- Example: `https://facebook.com/norsu.alumni`
- Optional field

**Twitter URL**
- Link to your Twitter profile
- Example: `https://twitter.com/norsu_alumni`
- Optional field

**LinkedIn URL**
- Link to your LinkedIn page
- Example: `https://linkedin.com/company/norsu-alumni`
- Optional field

**Instagram URL**
- Link to your Instagram profile
- Example: `https://instagram.com/norsu.alumni`
- Optional field

**YouTube URL**
- Link to your YouTube channel
- Example: `https://youtube.com/@norsu-alumni`
- Optional field

### Button Texts

**Signup Button Text**
- Text displayed on the signup/registration button
- Default: "Join the Network"
- Maximum 100 characters
- Appears on landing pages

**Login Button Text**
- Text displayed on the login button
- Default: "Member Login"
- Maximum 100 characters
- Appears on landing pages and navigation

## Step-by-Step Guide

### Task 1: Update Basic Site Information

1. Access the Site Configuration page
2. Locate the "Basic Information" section
3. Update the **Site Name** field:
   - Enter your desired site name
   - Keep it concise and memorable
4. Update the **Site Tagline** field:
   - Enter a compelling tagline
   - This will automatically update the hero section
5. Upload a **Logo** (optional):
   - Click "Choose File" or "Browse"
   - Select your logo image
   - Ensure image meets size recommendations
6. Click "Save" at the bottom of the form

**Expected Result**: Site name and tagline appear updated across the website, logo displays in navigation.

### Task 2: Update Contact Information

1. Scroll to the "Contact Information" section
2. Update **Contact Email**:
   - Enter a valid email address
   - This will be displayed publicly
3. Update **Contact Phone**:
   - Enter phone number with country code
   - Format: +XX XX XXX XXXX
4. Update **Contact Address**:
   - Enter complete physical address
   - Use line breaks for better formatting
   - Include postal code and country
5. Click "Save" at the bottom of the form

**Expected Result**: Updated contact information appears on contact pages and footer.

### Task 3: Configure Social Media Links

1. Scroll to the "Social Media" section
2. For each platform you use:
   - Enter the complete URL to your profile/page
   - Ensure URLs start with `https://`
   - Leave blank if you don't use that platform
3. Supported platforms:
   - Facebook
   - Twitter
   - LinkedIn
   - Instagram
   - YouTube
4. Click "Save" at the bottom of the form

**Expected Result**: Social media icons appear in footer and link to your profiles.

### Task 4: Customize Button Texts

1. Scroll to the "Button Texts" section
2. Update **Signup Button Text**:
   - Enter text that encourages registration
   - Keep it action-oriented
   - Examples: "Join Now", "Get Started", "Sign Up Free"
3. Update **Login Button Text**:
   - Enter text for existing members
   - Keep it clear and simple
   - Examples: "Login", "Sign In", "Member Access"
4. Click "Save" at the bottom of the form

**Expected Result**: Buttons throughout the site display your custom text.

### Task 5: Upload or Change Logo

1. Locate the "Logo" field in Basic Information
2. To upload a new logo:
   - Click "Choose File" or "Browse"
   - Navigate to your logo file
   - Select the file
   - Preview will appear (if supported)
3. To change existing logo:
   - Check "Clear" checkbox to remove current logo
   - Upload new logo using steps above
4. Click "Save" at the bottom of the form

**Expected Result**: New logo appears in navigation bar and branding areas.

## Tips and Best Practices

1. **Consistent Branding**: Ensure site name and tagline align with your brand identity
2. **Professional Logo**: Use high-quality logo images with transparent backgrounds (PNG)
3. **Valid Contact Info**: Always provide accurate, monitored contact information
4. **Social Media**: Only add social media links for active, maintained accounts
5. **Test Links**: After saving, test all social media links to ensure they work
6. **Mobile Preview**: Check how changes look on mobile devices
7. **Backup Settings**: Keep a record of your configuration before major changes
8. **Clear Messaging**: Use button texts that clearly communicate their purpose

## Important Notes

- **Singleton Model**: Only one site configuration exists; you cannot create multiple configurations
- **Auto-Sync**: Changing the site tagline automatically updates the hero section title
- **Public Information**: All contact information entered here is publicly visible
- **URL Format**: Social media URLs must be complete (include https://)
- **Image Uploads**: Logo images are stored in `media/cms/logos/` directory

## Troubleshooting

### Changes Not Appearing

**Issue**: Updated configuration doesn't show on the website

**Solutions**:
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh the page (Ctrl+F5)
- Check if changes were actually saved (look for success message)
- Verify you're viewing the correct page
- Wait a few moments for cache to clear

### Logo Not Displaying

**Issue**: Uploaded logo doesn't appear on the site

**Solutions**:
- Verify image file format (use PNG, JPG, or GIF)
- Check image file size (should be under 5MB)
- Ensure image uploaded successfully (check for error messages)
- Verify image path in media folder
- Check file permissions on server
- Try uploading a different image

### Social Media Icons Not Showing

**Issue**: Social media links don't appear in footer

**Solutions**:
- Verify URLs are complete and start with `https://`
- Check that URLs are valid and accessible
- Ensure template includes social media section
- Clear browser cache
- Check if theme supports social media icons

### Cannot Save Configuration

**Issue**: Save button doesn't work or shows errors

**Solutions**:
- Check for validation errors (red text near fields)
- Ensure required fields are filled
- Verify email format is correct
- Check file size if uploading logo
- Try refreshing the page and re-entering data
- Contact system administrator if issue persists

### Permission Denied

**Issue**: Cannot access site configuration page

**Solutions**:
- Verify you have admin/staff privileges
- Check with system administrator about permissions
- Ensure you're logged in with correct account
- Try logging out and back in

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [Page Sections Management](page-sections.md) - Manage page content sections
- [About Page Configuration](about-page.md) - Configure about page content
- [Contact Information Management](contact-info.md) - Manage additional contact entries

## Screenshots

> **Note**: Screenshots should be added showing:
> - Site Configuration form with all sections
> - Basic Information section with site name and tagline
> - Contact Information section
> - Social Media section with URL fields
> - Button Texts section
> - Logo upload interface
> - Save button and success message
> - Before/after comparison of site with updated configuration
