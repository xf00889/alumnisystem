# Features

## Overview

Features Showcase Management allows you to create and display key features, benefits, or services of the NORSU Alumni Network on the homepage. This feature helps highlight what makes your platform valuable and encourages user engagement.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions
- Marketing staff
- Content managers

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system
- Access to CMS Dashboard
- List of key features or benefits to showcase

## How to Access

### Method 1: Through CMS Dashboard
1. Navigate to CMS Dashboard (`/cms/dashboard/`)
2. Click on "Features" or "Features Showcase"
3. You will see the list of all feature items

### Method 2: Direct URL
- Navigate to `/cms/features/`

## Key Features

### 1. View All Features
- List view of all feature items
- Sort by order or title
- Filter by active status
- Pagination for large lists
- Icon preview in list

### 2. Add New Features
- Create new feature items
- Choose icons
- Add descriptions
- Set display order
- Add optional links

### 3. Edit Features
- Update feature information
- Change icons
- Modify descriptions
- Update links
- Adjust display order

### 4. Delete Features
- Remove outdated features
- Confirmation required
- Permanent action

### 5. Feature Ordering
- Control display sequence
- Lower numbers appear first
- Organize by importance

## Step-by-Step Guide

### Task 1: View Features List

1. Access Features from CMS Dashboard
2. View the list of all feature items
3. Observe the following information:
   - Feature title
   - Icon class
   - Display order
   - Active status
   - Creation date
4. Use pagination to navigate through multiple pages
5. Click on titles to view full details

**Expected Result**: Complete list of all feature showcase items with their icons and details.

### Task 2: Create a New Feature

1. From the Features list, click "Add Feature" or "Create New"
2. Fill in the feature details:

   **Title** (required):
   - Enter feature name or benefit
   - Maximum 200 characters
   - Be concise and impactful
   - Use action-oriented language
   - Examples:
     - "Connect with Alumni"
     - "Find Job Opportunities"
     - "Join Alumni Groups"
     - "Attend Exclusive Events"
   
   **Content** (required):
   - Enter feature description
   - Explain the benefit or value
   - Keep it concise (2-3 sentences)
   - Focus on user benefits, not just features
   - Use persuasive language
   - Example: "Build meaningful connections with fellow alumni from your college, campus, or industry. Expand your professional network and discover collaboration opportunities."
   
   **Icon** (optional):
   - Enter Font Awesome icon class
   - Default: "fas fa-lightbulb"
   - Choose icons that represent the feature
   - Common icons:
     - "fas fa-users" (networking, community)
     - "fas fa-briefcase" (jobs, career)
     - "fas fa-calendar" (events)
     - "fas fa-graduation-cap" (education, alumni)
     - "fas fa-comments" (messaging, communication)
     - "fas fa-heart" (donations, support)
     - "fas fa-search" (directory, search)
     - "fas fa-trophy" (achievements, success)
   - See Font Awesome documentation for more options
   
   **Icon Class** (optional):
   - Enter CSS class for icon styling
   - Default: "info"
   - Common options:
     - "primary" (blue)
     - "success" (green)
     - "info" (light blue)
     - "warning" (yellow/orange)
     - "danger" (red)
     - "secondary" (gray)
   - Affects icon color/background
   
   **Link URL** (optional):
   - Enter URL to feature page or section
   - Can be internal (/alumni-directory/) or external
   - Leave blank if no link needed
   - Example: "/jobs/" or "/events/"
   
   **Link Text** (optional):
   - Enter text for the link button
   - Default: "Learn More"
   - Keep it action-oriented
   - Examples:
     - "Get Started"
     - "Explore Now"
     - "View Jobs"
     - "Join Now"
   
   **Order**:
   - Enter a number for display order
   - Lower numbers appear first
   - Default: 0
   - Use increments of 10 (10, 20, 30...)
   - Typically display 3-6 features on homepage
   
   **Is Active**:
   - Check to make feature visible
   - Uncheck to hide without deleting

3. Review all entered information
4. Click "Save" or "Create Feature"

**Expected Result**: New feature is created and appears on the homepage features section.

### Task 3: Edit an Existing Feature

1. From the Features list, find the feature to edit
2. Click the "Edit" button or feature title
3. Update any of the following fields:
   - Title
   - Content/description
   - Icon
   - Icon class
   - Link URL
   - Link text
   - Order
   - Active status
4. Make necessary changes
5. Click "Save" or "Update Feature"

**Expected Result**: Feature is updated with new information. Changes appear on the homepage.

### Task 4: Choose Appropriate Icons

**Icon Selection Guide**:

1. **Networking Features**:
   - fas fa-users (community)
   - fas fa-user-friends (connections)
   - fas fa-handshake (partnerships)
   - fas fa-network-wired (network)

2. **Career Features**:
   - fas fa-briefcase (jobs)
   - fas fa-user-tie (professional)
   - fas fa-chart-line (growth)
   - fas fa-rocket (career launch)

3. **Communication Features**:
   - fas fa-comments (messaging)
   - fas fa-envelope (email)
   - fas fa-phone (contact)
   - fas fa-bullhorn (announcements)

4. **Events Features**:
   - fas fa-calendar (events)
   - fas fa-calendar-check (RSVP)
   - fas fa-ticket-alt (tickets)
   - fas fa-glass-cheers (celebration)

5. **Education Features**:
   - fas fa-graduation-cap (alumni)
   - fas fa-book (learning)
   - fas fa-certificate (credentials)
   - fas fa-chalkboard-teacher (mentorship)

6. **Support Features**:
   - fas fa-heart (donations)
   - fas fa-hands-helping (support)
   - fas fa-donate (giving)
   - fas fa-hand-holding-heart (charity)

**Steps to Update Icons**:
1. Identify the feature type
2. Choose appropriate icon from list above
3. Edit the feature
4. Update the "Icon" field
5. Save and preview on homepage

**Expected Result**: Features display with meaningful, recognizable icons.

### Task 5: Organize Features by Priority

**Recommended Organization**:

**Primary Features (Order 10-30)** - Most important, always visible:
- 10: Connect with Alumni
- 20: Find Job Opportunities
- 30: Join Alumni Groups

**Secondary Features (Order 40-60)** - Important but secondary:
- 40: Attend Events
- 50: Find Mentors
- 60: Support Campaigns

**Additional Features (Order 70+)** - Nice to have:
- 70: Update Your Profile
- 80: Share Your Success
- 90: Stay Informed

**Steps to Organize**:
1. List all features
2. Rank by importance to users
3. Assign order values based on priority
4. Edit each feature and update order
5. Save all changes
6. Review homepage to verify display

**Expected Result**: Most important features appear first and are most prominent.

### Task 6: Add Links to Features

1. Edit a feature
2. In the "Link URL" field, enter the destination:
   - Internal page: `/jobs/` or `/events/`
   - External page: `https://example.com`
   - Anchor link: `#section-name`
3. In the "Link Text" field, enter button text:
   - Make it action-oriented
   - Match the feature purpose
   - Examples: "Browse Jobs", "View Events", "Join Now"
4. Save the feature
5. Test the link on the homepage

**Expected Result**: Feature displays with a clickable button that navigates to the specified page.

### Task 7: Deactivate a Feature

1. From the Features list, find the feature
2. Click "Edit" on the feature
3. Uncheck the "Is Active" checkbox
4. Click "Save"

**Use Cases**:
- Seasonal features (only relevant at certain times)
- Testing new features before making public
- Feature temporarily unavailable
- Rotating feature displays

**Expected Result**: Feature no longer appears on the homepage but remains in admin list.

### Task 8: Delete a Feature

1. From the Features list, find the feature to delete
2. Click the "Delete" button
3. Review the confirmation page:
   - Feature details are displayed
   - Warning about permanent deletion
4. Confirm you want to delete
5. Click "Yes, delete" or "Confirm deletion"

**Use Cases**:
- Permanently removed features
- Duplicate entries
- Outdated information

**Expected Result**: Feature is permanently removed from the system.

## Feature Content Best Practices

### Titles
- Keep short and punchy (2-5 words)
- Use action verbs when possible
- Focus on user benefit
- Be specific, not generic
- Examples:
  - Good: "Find Your Dream Job"
  - Poor: "Job Board Feature"

### Descriptions
- Focus on benefits, not just features
- Use "you" language (user-focused)
- Keep to 2-3 sentences
- Be specific about value
- Include a call-to-action mindset
- Examples:
  - Good: "Discover job opportunities tailored to your skills and experience. Connect directly with employers and take the next step in your career."
  - Poor: "We have a job board where jobs are posted."

### Icons
- Choose icons that clearly represent the feature
- Be consistent with icon style (all solid or all regular)
- Use recognizable symbols
- Don't overuse the same icon
- Test icon visibility on different backgrounds

### Links
- Link to relevant pages or sections
- Ensure links work correctly
- Use descriptive link text
- Test links after saving
- Update links if page URLs change

## Tips and Best Practices

1. **User-Centric**: Focus on what users gain, not what the system does
2. **Consistency**: Use similar length and style for all features
3. **Visual Balance**: Display 3-6 features for best visual impact
4. **Icon Variety**: Use different icons for each feature
5. **Regular Review**: Update features quarterly to stay relevant
6. **A/B Testing**: Try different titles and descriptions to see what resonates
7. **Mobile View**: Check how features look on mobile devices
8. **Action-Oriented**: Use verbs and active language
9. **Specificity**: Be specific about benefits, avoid vague claims
10. **Prioritization**: Put most important features first

## Important Notes

- **Icon Library**: Icons use Font Awesome; ensure your theme includes Font Awesome
- **Order Conflicts**: Multiple features can have the same order value
- **Link Validation**: System doesn't validate URLs; test links manually
- **Deletion**: Deleting a feature is permanent and cannot be undone
- **Display Limit**: Homepage may limit number of displayed features

## Troubleshooting

### Feature Not Appearing on Homepage

**Issue**: Created or edited feature doesn't show on the website

**Solutions**:
- Verify "Is Active" checkbox is checked
- Clear browser cache and refresh
- Check display order
- Verify homepage template includes features section
- Check if there's a display limit (e.g., only first 6 shown)
- Wait a few moments for cache to clear

### Icon Not Displaying

**Issue**: Icon doesn't appear or shows as box

**Solutions**:
- Verify Font Awesome is loaded on the page
- Check icon class name is correct (include "fas" or "far")
- Ensure icon exists in Font Awesome library
- Try a different, common icon (like "fas fa-star")
- Check browser console for errors
- Verify Font Awesome version compatibility

### Icon Wrong Color

**Issue**: Icon displays in unexpected color

**Solutions**:
- Check "Icon Class" field value
- Verify CSS class exists in theme
- Try different icon class (primary, success, info, etc.)
- Check theme's color definitions
- Clear browser cache

### Link Not Working

**Issue**: Feature link doesn't navigate correctly

**Solutions**:
- Verify URL is correct and complete
- Check for typos in URL
- Test URL in browser address bar
- Ensure internal links start with /
- Ensure external links start with https://
- Check if page exists at that URL

### Features Out of Order

**Issue**: Features don't display in expected sequence

**Solutions**:
- Review order values for all features
- Ensure logical ordering
- Use consistent increments (10, 20, 30)
- Check if multiple features have same order value
- Verify template respects order field

### Cannot Save Feature

**Issue**: Save button doesn't work or shows errors

**Solutions**:
- Check for validation errors (red text near fields)
- Ensure required fields are filled (Title, Content)
- Verify title doesn't exceed 200 characters
- Check icon class format
- Try refreshing the page and re-entering data
- Contact system administrator if issue persists

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [Page Sections Management](page-sections.md) - Manage page content sections
- [Site Configuration](site-configuration.md) - Manage global site settings
- [Testimonials Management](testimonials.md) - Manage testimonial entries

## Screenshots

> **Note**: Screenshots should be added showing:
> - Features list view with icons and titles
> - Create new feature form
> - Icon field with Font Awesome examples
> - Icon class dropdown or field
> - Link URL and link text fields
> - Edit feature form with existing content
> - Order field and organization
> - Active/inactive toggle
> - Delete confirmation page
> - Features display on homepage
> - Success messages after create/edit/delete
> - Different icon styles and colors
> - Mobile view of features section
