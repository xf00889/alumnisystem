# Page Sections

## Overview

Page Sections Management allows you to create, edit, and organize different content sections that appear on your website pages. Sections include hero banners, features, testimonials, calls-to-action, announcements, and statistics displays.

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
2. Click on "Page Sections" or "Manage Sections"
3. You will see the list of all page sections

### Method 2: Direct URL
- Navigate to `/cms/page-sections/`

## Section Types

The system supports the following section types:

1. **Hero Section**: Main banner/header section with large text and imagery
2. **Features Section**: Showcase of key features or benefits
3. **Testimonials Section**: Display of user testimonials and reviews
4. **Call to Action Section**: Promotional sections encouraging user action
5. **Announcements Section**: Important announcements and news
6. **Statistics Section**: Display of numerical data and metrics

## Key Features

### 1. View All Sections
- List view of all page sections
- Filter by section type
- Sort by order or creation date
- Pagination for large lists

### 2. Create New Sections
- Add new content sections
- Choose section type
- Set display order
- Add images and content

### 3. Edit Existing Sections
- Update section content
- Change images
- Modify display order
- Toggle active status

### 4. Delete Sections
- Remove unwanted sections
- Confirmation required before deletion
- Permanent action

### 5. Section Ordering
- Control display order with numeric values
- Lower numbers appear first
- Reorder sections easily

## Step-by-Step Guide

### Task 1: View Page Sections List

1. Access Page Sections from CMS Dashboard
2. View the list of all sections
3. Observe the following information:
   - Section title
   - Section type
   - Display order
   - Active status
   - Creation date
4. Use pagination to navigate through multiple pages
5. Click on section titles to view details

**Expected Result**: Complete list of all page sections with their details.

### Task 2: Create a New Page Section

1. From the Page Sections list, click "Create New Section" or "Add Page Section"
2. Fill in the section details:

   **Section Type**:
   - Select from dropdown menu
   - Choose the appropriate type for your content
   
   **Title**:
   - Enter a descriptive title
   - Maximum 200 characters
   - This appears as the section heading
   
   **Subtitle** (optional):
   - Enter additional descriptive text
   - Provides context for the section
   - Can be longer than title
   
   **Content** (optional):
   - Enter main section content
   - HTML is allowed for formatting
   - Use rich text editor if available
   
   **Image** (optional):
   - Click "Choose File" to upload
   - Recommended size varies by section type
   - Supported formats: JPG, PNG, GIF
   
   **Order**:
   - Enter a number for display order
   - Lower numbers appear first
   - Default: 0
   - View existing sections to avoid conflicts
   
   **Is Active**:
   - Check to make section visible
   - Uncheck to hide without deleting

3. Review all entered information
4. Click "Save" or "Create Section"

**Expected Result**: New section is created and appears in the list. Success message confirms creation.

### Task 3: Edit an Existing Page Section

1. From the Page Sections list, find the section to edit
2. Click the "Edit" button or section title
3. Update any of the following fields:
   - Section type (if allowed)
   - Title
   - Subtitle
   - Content
   - Image (upload new or clear existing)
   - Order
   - Active status
4. To change the image:
   - Upload a new image to replace current one
   - Check "Clear" to remove image without replacement
5. Click "Save" or "Update Section"

**Expected Result**: Section is updated with new information. Success message confirms update.

### Task 4: Reorder Page Sections

1. View the Page Sections list
2. Note the current order values
3. Identify sections you want to reorder
4. Edit each section and update the "Order" field:
   - Lower numbers = higher priority (appear first)
   - Use increments of 10 for easy reordering (10, 20, 30...)
   - This allows inserting sections between existing ones
5. Save each section after updating order
6. Return to list view to verify new order

**Alternative Method** (if available):
- Some interfaces allow drag-and-drop reordering
- Click and hold section
- Drag to new position
- Release to save new order

**Expected Result**: Sections appear in the new order on both admin list and public website.

### Task 5: Deactivate a Page Section

1. From the Page Sections list, find the section
2. Click "Edit" on the section
3. Uncheck the "Is Active" checkbox
4. Click "Save"

**Alternative Method** (if available):
- Some list views allow toggling active status directly
- Click the active/inactive toggle in the list
- Change is saved automatically

**Expected Result**: Section no longer appears on the public website but remains in admin list for future reactivation.

### Task 6: Delete a Page Section

1. From the Page Sections list, find the section to delete
2. Click the "Delete" button
3. Review the confirmation page:
   - Section details are displayed
   - Warning about permanent deletion
4. Confirm you want to delete
5. Click "Yes, delete" or "Confirm deletion"

**Expected Result**: Section is permanently removed from the system. Success message confirms deletion.

## Section-Specific Guidelines

### Hero Section
- **Purpose**: Main banner at top of page
- **Best Practices**:
  - Use high-quality, large images (1920x1080 or larger)
  - Keep title short and impactful
  - Subtitle should explain value proposition
  - Typically only one active hero section per page

### Features Section
- **Purpose**: Highlight key features or benefits
- **Best Practices**:
  - Use icons or small images
  - Keep content concise
  - Focus on benefits, not just features
  - Typically 3-6 features work best

### Testimonials Section
- **Purpose**: Display social proof and reviews
- **Best Practices**:
  - Include photos when possible
  - Keep quotes authentic and specific
  - Attribute to real people with titles
  - Rotate testimonials regularly

### Call to Action Section
- **Purpose**: Encourage specific user actions
- **Best Practices**:
  - Clear, action-oriented title
  - Compelling reason to act
  - Prominent button or link
  - Create urgency when appropriate

### Announcements Section
- **Purpose**: Display important news and updates
- **Best Practices**:
  - Keep current and relevant
  - Remove outdated announcements
  - Use clear, concise language
  - Update regularly

### Statistics Section
- **Purpose**: Show impressive numbers and metrics
- **Best Practices**:
  - Use round, impressive numbers
  - Include context for statistics
  - Update periodically to reflect growth
  - Use icons to make visually appealing

## Tips and Best Practices

1. **Consistent Ordering**: Use increments of 10 (10, 20, 30) for order values to allow easy insertion
2. **Active Management**: Regularly review and deactivate outdated sections
3. **Image Quality**: Use high-resolution images appropriate for section type
4. **Content Length**: Keep content concise and scannable
5. **Mobile Preview**: Check how sections look on mobile devices
6. **HTML Formatting**: Use HTML carefully in content fields; test thoroughly
7. **Backup Content**: Copy important content before major edits
8. **Test Changes**: Preview changes before making sections active
9. **Seasonal Updates**: Update sections for holidays, events, or campaigns
10. **Performance**: Don't create too many active sections; it can slow page load

## Important Notes

- **Order Conflicts**: Multiple sections can have the same order value; they'll be sorted by creation date
- **HTML Content**: Be careful with HTML in content fields; invalid HTML can break page layout
- **Image Paths**: Images are stored in `media/cms/sections/` directory
- **Deletion**: Deleting a section is permanent and cannot be undone
- **Active Status**: Inactive sections don't appear on the website but remain in the database

## Troubleshooting

### Section Not Appearing on Website

**Issue**: Created or edited section doesn't show on the public site

**Solutions**:
- Verify "Is Active" checkbox is checked
- Clear browser cache and refresh
- Check section order (might be below viewport)
- Verify section type matches page template
- Check if template includes that section type
- Wait a few moments for cache to clear

### Images Not Displaying

**Issue**: Uploaded images don't appear in sections

**Solutions**:
- Verify image file format (JPG, PNG, GIF)
- Check image file size (should be under 10MB)
- Ensure image uploaded successfully
- Verify media folder permissions
- Check image path in database
- Try uploading a different image
- Clear browser cache

### Cannot Reorder Sections

**Issue**: Changing order values doesn't affect display order

**Solutions**:
- Ensure you saved changes after updating order
- Clear browser cache
- Check if multiple sections have same order value
- Verify template respects order field
- Try using larger gaps between order values (10, 20, 30)

### HTML Content Breaking Layout

**Issue**: Page layout breaks after adding HTML content

**Solutions**:
- Validate HTML syntax
- Remove or escape special characters
- Use simple HTML tags only
- Test HTML in a separate environment first
- Consider using plain text instead
- Contact developer for complex HTML needs

### Permission Denied

**Issue**: Cannot create, edit, or delete sections

**Solutions**:
- Verify you have admin/staff privileges
- Check with system administrator about permissions
- Ensure you're logged in with correct account
- Try logging out and back in

### Sections Appearing in Wrong Order

**Issue**: Sections don't display in the expected order

**Solutions**:
- Review order values for all sections
- Ensure no duplicate order values
- Use consistent increments (10, 20, 30)
- Check if template has custom ordering logic
- Verify section type matches page

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [Site Configuration](site-configuration.md) - Manage global site settings
- [Features Showcase Management](features.md) - Manage individual feature items
- [Testimonials Management](testimonials.md) - Manage testimonial entries

## Screenshots

> **Note**: Screenshots should be added showing:
> - Page Sections list view with multiple sections
> - Create new section form with all fields
> - Section type dropdown menu
> - Edit section form with existing content
> - Image upload interface
> - Order field and existing sections reference
> - Active/inactive toggle
> - Delete confirmation page
> - Success messages after create/edit/delete
> - Before/after of reordered sections on website
