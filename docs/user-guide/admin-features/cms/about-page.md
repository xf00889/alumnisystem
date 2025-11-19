# About Page

## Overview

About Page Configuration allows you to manage the content displayed on the About page, including university information, mission and vision statements, descriptions, and page titles. This is a central place to maintain the institutional identity and messaging.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions
- University administrators
- Communications staff

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system
- Access to CMS Dashboard
- Official university information and statements

## How to Access

### Method 1: Through CMS Dashboard
1. Navigate to CMS Dashboard (`/cms/dashboard/`)
2. Click on "About Page Configuration" or "About Config"
3. You will be directed to the configuration form

### Method 2: Through Django Admin
1. Go to `/admin/`
2. Find "CMS" section
3. Click on "About Page Configuration"
4. Click on the existing configuration entry

### Method 3: Direct URL
- Navigate to `/cms/about-config/`

## Configuration Sections

### University Information

**University Name**
- Full official name of the university
- Default: "Negros Oriental State University"
- Maximum 200 characters
- Used throughout the About page

**University Short Name**
- Acronym or short name
- Default: "NORSU"
- Maximum 50 characters
- Used in headers and abbreviated references

**University Description**
- Main description of the university
- Default: Comprehensive description of NORSU
- Brief overview of the institution
- 2-3 sentences recommended
- Appears prominently on About page

**University Extended Description**
- Detailed description of the university
- Default: Extended information about NORSU
- Provides additional context and history
- 3-5 sentences recommended
- Appears below main description

**Establishment Year**
- Year the university was established
- Default: "2004"
- Maximum 10 characters
- Can be a year or year range
- Example: "2004" or "1927-2004"

### Mission and Vision

**Mission**
- University mission statement
- Default: NORSU's official mission
- Describes the university's purpose
- Should be official, approved statement
- Typically 2-4 sentences

**Vision**
- University vision statement
- Default: NORSU's official vision
- Describes aspirations and goals
- Should be official, approved statement
- Typically 1-3 sentences

### Page Configuration

**About Page Title**
- Title displayed on the About page
- Default: "About NORSU Alumni Network"
- Maximum 200 characters
- Appears as page heading

**About Page Subtitle**
- Subtitle or description for the About page
- Default: Descriptive subtitle
- Provides context for the page
- Appears below page title

## Step-by-Step Guide

### Task 1: Access About Page Configuration

1. Navigate to CMS Dashboard
2. Click on "About Page Configuration"
3. View the current configuration
4. Note: This is a singleton model (only one configuration exists)

**Expected Result**: About page configuration form is displayed with current values.

### Task 2: Update University Information

1. Access the About Page Configuration form
2. Locate the "University Information" section
3. Update the following fields as needed:

   **University Name**:
   - Enter the full official name
   - Verify spelling and capitalization
   - Example: "Negros Oriental State University"
   
   **University Short Name**:
   - Enter the acronym or short name
   - Use all caps for acronyms
   - Example: "NORSU"
   
   **Establishment Year**:
   - Enter the founding year
   - Can be single year or range
   - Example: "2004" or "1927-2004"

4. Click "Save" at the bottom of the form

**Expected Result**: University information is updated and appears on the About page.

### Task 3: Update University Descriptions

1. Scroll to the "University Description" section
2. Update the descriptions:

   **University Description** (Main):
   - Enter a concise overview
   - 2-3 sentences recommended
   - Focus on key characteristics
   - Example: "Negros Oriental State University (NORSU) is a premier state university in the Philippines, committed to providing quality education and fostering excellence in research, extension, and production services."
   
   **University Extended Description**:
   - Enter additional details
   - 3-5 sentences recommended
   - Include history, growth, achievements
   - Example: "Established in 2004 through the merger of several educational institutions, NORSU has grown to become a leading center of learning in the Visayas region. Our university is dedicated to developing competent professionals who contribute to national development and global competitiveness."

3. Review for accuracy and clarity
4. Click "Save"

**Expected Result**: Updated descriptions appear on the About page, providing comprehensive information about the university.

### Task 4: Update Mission and Vision Statements

1. Scroll to the "Mission & Vision" section
2. Update the statements:

   **Mission**:
   - Enter the official mission statement
   - Verify with official university documents
   - Typically 2-4 sentences
   - Describes purpose and objectives
   - Example: "To provide quality and relevant education through instruction, research, extension, and production services for the holistic development of individuals and communities towards a progressive society."
   
   **Vision**:
   - Enter the official vision statement
   - Verify with official university documents
   - Typically 1-3 sentences
   - Describes aspirations and future goals
   - Example: "A premier state university in the Asia-Pacific region recognized for excellence in instruction, research, extension, and production that produces globally competitive graduates and empowered communities."

3. Ensure statements are current and approved
4. Click "Save"

**Expected Result**: Mission and vision statements are updated and displayed prominently on the About page.

### Task 5: Update Page Titles

1. Scroll to the "Page Configuration" section
2. Update the page titles:

   **About Page Title**:
   - Enter the main page heading
   - Keep it clear and descriptive
   - Maximum 200 characters
   - Example: "About NORSU Alumni Network"
   
   **About Page Subtitle**:
   - Enter supporting text
   - Provides context for the page
   - 1-2 sentences recommended
   - Example: "Learn more about our university, mission, and the people behind our alumni community"

3. Review for consistency with branding
4. Click "Save"

**Expected Result**: Page titles are updated and appear at the top of the About page.

### Task 6: Review and Verify All Changes

1. After saving, navigate to the About page
2. Verify all updated information appears correctly:
   - University name and short name
   - Establishment year
   - Descriptions (main and extended)
   - Mission statement
   - Vision statement
   - Page title and subtitle
3. Check formatting and layout
4. Test on mobile devices
5. Verify no typos or errors

**Expected Result**: All information displays correctly and professionally on the About page.

## Content Best Practices

### University Information
- Use official names and spellings
- Verify information with university records
- Keep short name consistent across all materials
- Update establishment year if institutional changes occur

### Descriptions
- **Main Description**:
  - Focus on core identity
  - Highlight key strengths
  - Keep concise and impactful
  - Use active voice
  
- **Extended Description**:
  - Provide historical context
  - Mention achievements and growth
  - Include regional or national significance
  - Maintain professional tone

### Mission and Vision
- Use official, approved statements
- Don't modify without proper authorization
- Verify statements are current
- Ensure alignment with university strategic plans
- Review periodically for updates

### Page Titles
- Keep clear and descriptive
- Align with site navigation
- Use consistent capitalization
- Avoid overly long titles
- Make subtitle informative but concise

## Tips and Best Practices

1. **Official Sources**: Always use official university documents as sources
2. **Approval Process**: Get approval for major changes from appropriate authorities
3. **Consistency**: Ensure information matches other official university materials
4. **Regular Review**: Review and update annually or when institutional changes occur
5. **Accuracy**: Verify all facts, dates, and statements
6. **Professional Tone**: Maintain formal, professional language
7. **Clarity**: Use clear, accessible language for diverse audiences
8. **Completeness**: Provide comprehensive information without being verbose
9. **Proofreading**: Carefully proofread all content before saving
10. **Backup**: Keep copies of previous versions for reference

## Important Notes

- **Singleton Model**: Only one About page configuration exists; you cannot create multiple configurations
- **Official Statements**: Mission and vision should be official, approved statements
- **Public Visibility**: All information entered is publicly visible on the About page
- **Cannot Delete**: The configuration cannot be deleted, only edited
- **Related Content**: This works in conjunction with Staff Members, Timeline, and Statistics

## Troubleshooting

### Changes Not Appearing

**Issue**: Updated configuration doesn't show on the About page

**Solutions**:
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh the page (Ctrl+F5)
- Check if changes were actually saved (look for success message)
- Verify you're viewing the correct page
- Wait a few moments for cache to clear
- Check if template is pulling from correct source

### Cannot Save Configuration

**Issue**: Save button doesn't work or shows errors

**Solutions**:
- Check for validation errors (red text near fields)
- Ensure required fields are filled
- Verify character limits on fields
- Try refreshing the page and re-entering data
- Check for special characters that might cause issues
- Contact system administrator if issue persists

### Text Formatting Issues

**Issue**: Text doesn't display with proper formatting

**Solutions**:
- Check for line breaks in text fields
- Verify no special characters causing issues
- Use plain text without formatting codes
- Check template rendering
- Test with simple text first

### Mission/Vision Too Long

**Issue**: Mission or vision statement is too long for layout

**Solutions**:
- Verify you're using official statements
- Check if statements can be abbreviated
- Consult with university administration
- Adjust page layout if necessary
- Consider using summary version

### Cannot Access Configuration

**Issue**: Cannot access About page configuration

**Solutions**:
- Verify you have admin/staff privileges
- Check with system administrator about permissions
- Ensure you're logged in with correct account
- Try accessing through Django admin
- Try logging out and back in

### Descriptions Not Distinct

**Issue**: Main and extended descriptions are too similar

**Solutions**:
- Rewrite main description to be more concise
- Expand extended description with additional details
- Focus main description on core identity
- Use extended description for history and achievements
- Ensure each serves a distinct purpose

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [Site Configuration](site-configuration.md) - Manage global site settings
- [Staff Members Management](staff-members.md) - Manage staff profiles displayed on About page
- [Timeline Management](timeline.md) - Manage university timeline on About page
- [Alumni Statistics Management](statistics.md) - Manage statistics displayed on About page

## Additional About Page Content

The About page also displays content from other CMS features:

- **Staff Members**: Profiles of key personnel
- **Timeline Items**: Historical milestones and events
- **Alumni Statistics**: Key metrics and numbers

To manage these, see their respective documentation pages.

## Screenshots

> **Note**: Screenshots should be added showing:
> - About Page Configuration form with all sections
> - University Information section
> - University Description fields
> - Mission and Vision fields
> - Page Configuration section
> - Save button and success message
> - About page displaying updated information
> - Before/after comparison of About page
> - Mobile view of About page
> - All sections of About page (staff, timeline, statistics)
