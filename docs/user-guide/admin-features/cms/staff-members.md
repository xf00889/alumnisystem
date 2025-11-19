# Staff Members

## Overview

Staff Members Management allows you to create and maintain profiles for staff members, administrators, and key personnel that are displayed on the About page. This feature helps showcase the team behind the NORSU Alumni Network.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions
- HR administrators

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system
- Access to CMS Dashboard
- Staff member photos (optional but recommended)

## How to Access

### Method 1: Through CMS Dashboard
1. Navigate to CMS Dashboard (`/cms/dashboard/`)
2. Click on "Staff Members" or "Manage Staff"
3. You will see the list of all staff members

### Method 2: Direct URL
- Navigate to `/cms/staff-members/`

## Key Features

### 1. View All Staff Members
- List view of all staff profiles
- Filter by department
- Sort by order or name
- Pagination for large lists
- Photo previews in list

### 2. Add New Staff Members
- Create new staff profiles
- Upload photos
- Set department and position
- Add biographical information
- Set display order

### 3. Edit Staff Profiles
- Update staff information
- Change photos
- Modify positions or departments
- Update contact information
- Adjust display order

### 4. Delete Staff Profiles
- Remove staff members who have left
- Confirmation required
- Permanent action

### 5. Staff Ordering
- Control display order on About page
- Lower numbers appear first
- Organize by hierarchy or importance

## Step-by-Step Guide

### Task 1: View Staff Members List

1. Access Staff Members from CMS Dashboard
2. View the list of all staff members
3. Observe the following information:
   - Staff member name
   - Position/title
   - Department
   - Display order
   - Active status
   - Photo preview
4. Use pagination to navigate through multiple pages
5. Click on names to view full details

**Expected Result**: Complete list of all staff members with their basic information and photos.

### Task 2: Add a New Staff Member

1. From the Staff Members list, click "Add Staff Member" or "Create New"
2. Fill in the staff member details:

   **Name** (required):
   - Enter full name
   - Maximum 200 characters
   - Example: "Dr. Maria Santos"
   
   **Position** (required):
   - Enter job title or role
   - Maximum 200 characters
   - Example: "Director of Alumni Relations"
   
   **Department** (optional):
   - Enter department or division
   - Maximum 200 characters
   - Example: "Alumni Affairs Office"
   
   **Bio** (optional):
   - Enter brief biography or description
   - Include education, experience, achievements
   - Keep it professional and concise
   - 2-3 paragraphs recommended
   
   **Image** (optional but recommended):
   - Click "Choose File" to upload photo
   - Recommended size: 400x400 pixels or larger
   - Use professional headshot
   - Supported formats: JPG, PNG
   - Square aspect ratio works best
   
   **Email** (optional):
   - Enter contact email address
   - Will be displayed publicly if provided
   - Use official work email
   
   **Order**:
   - Enter a number for display order
   - Lower numbers appear first
   - Default: 0
   - Use increments of 10 (10, 20, 30...)
   
   **Is Active**:
   - Check to make profile visible
   - Uncheck to hide without deleting

3. Review all entered information
4. Click "Save" or "Create Staff Member"

**Expected Result**: New staff member profile is created and appears in the list and on the About page.

### Task 3: Edit a Staff Member Profile

1. From the Staff Members list, find the profile to edit
2. Click the "Edit" button or staff member name
3. Update any of the following fields:
   - Name
   - Position
   - Department
   - Bio
   - Image (upload new or clear existing)
   - Email
   - Order
   - Active status
4. To change the photo:
   - Upload a new photo to replace current one
   - Check "Clear" to remove photo without replacement
5. Click "Save" or "Update Staff Member"

**Expected Result**: Staff member profile is updated with new information. Changes appear on the About page.

### Task 4: Reorder Staff Members

1. View the Staff Members list
2. Note the current order values
3. Decide on the desired display order:
   - By hierarchy (Director, Manager, Staff)
   - By department
   - By seniority
   - Alphabetically within groups
4. Edit each staff member and update the "Order" field:
   - Lower numbers = higher priority (appear first)
   - Use increments of 10 for easy reordering
   - Group by department using ranges (10-19, 20-29, etc.)
5. Save each profile after updating order
6. Return to list view to verify new order

**Expected Result**: Staff members appear in the desired order on the About page.

### Task 5: Deactivate a Staff Member

1. From the Staff Members list, find the profile
2. Click "Edit" on the staff member
3. Uncheck the "Is Active" checkbox
4. Click "Save"

**Use Cases**:
- Staff member on leave
- Temporary removal from public display
- Testing before making profile public

**Expected Result**: Staff member profile no longer appears on the About page but remains in admin list for future reactivation.

### Task 6: Delete a Staff Member Profile

1. From the Staff Members list, find the profile to delete
2. Click the "Delete" button
3. Review the confirmation page:
   - Staff member details are displayed
   - Warning about permanent deletion
4. Confirm you want to delete
5. Click "Yes, delete" or "Confirm deletion"

**Use Cases**:
- Staff member has left the organization
- Duplicate profile created by mistake
- Profile no longer needed

**Expected Result**: Staff member profile is permanently removed from the system.

## Staff Profile Best Practices

### Professional Photos
- Use high-quality, professional headshots
- Consistent background style across all photos
- Square aspect ratio (1:1) works best
- Good lighting and clear facial features
- Professional attire
- Neutral or branded background

### Position Titles
- Use official job titles
- Be consistent with title formatting
- Include credentials if relevant (Dr., PhD, etc.)
- Keep titles concise

### Department Names
- Use official department names
- Be consistent across all profiles
- Group related staff in same department
- Consider using abbreviations for long names

### Biographical Information
- Keep it professional and relevant
- Include:
  - Educational background
  - Years of experience
  - Key achievements
  - Areas of expertise
  - Professional interests
- Avoid:
  - Personal information
  - Controversial topics
  - Excessive length (keep to 2-3 paragraphs)

### Contact Information
- Only include if staff member wants to be contacted
- Use official work email
- Consider creating a general department email instead
- Update when staff members change roles

### Display Order
- Organize by organizational hierarchy
- Directors and heads first
- Group by department
- Alphabetical within same level
- Use consistent numbering scheme

## Tips and Best Practices

1. **Consistent Formatting**: Use the same photo style and bio format for all staff
2. **Regular Updates**: Review and update profiles quarterly
3. **Photo Quality**: Invest in professional photography for consistency
4. **Privacy**: Get permission before adding contact information
5. **Accuracy**: Verify all information with staff members before publishing
6. **Accessibility**: Include alt text for photos (if supported)
7. **Mobile View**: Check how profiles look on mobile devices
8. **Backup**: Keep copies of photos and bios before major updates
9. **Transitions**: Update promptly when staff members join or leave
10. **Permissions**: Ensure you have rights to use photos

## Important Notes

- **Photo Storage**: Images are stored in `media/cms/staff/` directory
- **Public Information**: All information entered is publicly visible on the About page
- **Deletion**: Deleting a profile is permanent and cannot be undone
- **Email Display**: Email addresses are displayed as clickable mailto links
- **Order Conflicts**: Multiple staff can have the same order value; they'll be sorted by name

## Troubleshooting

### Staff Member Not Appearing on About Page

**Issue**: Added or edited staff member doesn't show on the website

**Solutions**:
- Verify "Is Active" checkbox is checked
- Clear browser cache and refresh
- Check display order (might be below viewport)
- Verify About page template includes staff section
- Wait a few moments for cache to clear
- Check if there's a limit on displayed staff members

### Photo Not Displaying

**Issue**: Uploaded photo doesn't appear in profile

**Solutions**:
- Verify image file format (JPG or PNG)
- Check image file size (should be under 5MB)
- Ensure image uploaded successfully
- Verify media folder permissions
- Try uploading a different image
- Check if image is corrupted
- Use a square aspect ratio image

### Photo Quality Issues

**Issue**: Photo appears pixelated or distorted

**Solutions**:
- Upload higher resolution image (at least 400x400)
- Use square aspect ratio to avoid distortion
- Check original image quality
- Avoid excessive compression
- Use PNG for better quality
- Ensure proper image dimensions

### Cannot Reorder Staff Members

**Issue**: Changing order values doesn't affect display

**Solutions**:
- Ensure you saved changes after updating order
- Clear browser cache
- Check if multiple staff have same order value
- Verify template respects order field
- Try using larger gaps between order values

### Email Link Not Working

**Issue**: Email address doesn't create clickable link

**Solutions**:
- Verify email format is correct
- Check for extra spaces in email field
- Ensure template renders email as mailto link
- Test with different email address
- Check browser email client settings

### Permission Denied

**Issue**: Cannot create, edit, or delete staff profiles

**Solutions**:
- Verify you have admin/staff privileges
- Check with system administrator about permissions
- Ensure you're logged in with correct account
- Try logging out and back in

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [About Page Configuration](about-page.md) - Configure about page content
- [Timeline Management](timeline.md) - Manage university timeline
- [Site Configuration](site-configuration.md) - Manage global site settings

## Screenshots

> **Note**: Screenshots should be added showing:
> - Staff Members list view with photos and details
> - Create new staff member form
> - Photo upload interface
> - Edit staff member form with existing data
> - Order field and current staff list
> - Active/inactive toggle
> - Delete confirmation page
> - Staff member display on About page
> - Success messages after create/edit/delete
> - Mobile view of staff profiles
