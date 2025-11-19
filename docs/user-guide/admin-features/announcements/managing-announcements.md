# Managing Announcements

## Overview

The announcement management feature allows administrators to view, edit, delete, and filter existing announcements. This comprehensive management interface provides tools to maintain and organize all announcements in the system.

## Who Can Use This Feature

- **Admin Users**: Staff members with administrative privileges
- **Required Permission**: `is_staff` flag must be enabled for editing and deleting

## Prerequisites

- Admin account with staff privileges
- Existing announcements in the system
- Understanding of announcement structure and fields

## How to Access

1. Log in to your admin account
2. Navigate to the main navigation menu
3. Click on **"Announcements"**
4. The announcements list page will display

**Alternative Access:**
- From the Django admin panel: Navigate to **Announcements** → **Announcements**

## Key Features

- **View All Announcements**: Browse complete list of announcements
- **Search Functionality**: Find announcements by title or content
- **Category Filtering**: Filter announcements by category
- **Edit Announcements**: Update existing announcement details
- **Delete Announcements**: Remove outdated or incorrect announcements
- **Toggle Visibility**: Activate or deactivate announcements
- **View Modes**: Switch between card view and table view
- **Pagination**: Navigate through large lists of announcements
- **Quick Actions**: Perform actions directly from the list view

## Step-by-Step Guide

### Task 1: Viewing Announcements List

1. Navigate to the **Announcements** page from the main menu
2. The announcements list displays all announcements in the system
3. By default, announcements are sorted by date (newest first)

**List Display Information:**
- **Title**: Announcement headline
- **Priority Badge**: Visual indicator of priority level (Urgent, High, Medium, Low)
- **Category**: Announcement category
- **Date Posted**: When the announcement was created
- **Target Audience**: Who can view the announcement
- **Views Count**: Number of times the announcement has been viewed
- **Status**: Active or inactive

**View Modes:**

**Card View** (Default):
- Displays announcements as individual cards
- Shows preview of content
- Includes all metadata and action buttons
- Best for visual browsing

**Table View**:
- Displays announcements in a compact table format
- Shows key information in columns
- Better for managing large numbers of announcements
- Easier to compare multiple announcements

**To Switch Views:**
1. Locate the view toggle buttons at the top of the page
2. Click **"Card View"** icon (grid icon) for card layout
3. Click **"Table View"** icon (list icon) for table layout

**Expected Result:** The announcements list displays with all relevant information in your chosen view mode.

### Task 2: Searching for Announcements

The search feature helps you quickly find specific announcements by title or content.

1. Locate the **search bar** at the top of the announcements page
2. Click inside the search input field
3. Type your search query:
   - Search by announcement title
   - Search by content keywords
   - Search by category name
4. Press **Enter** or click the search icon
5. The list updates to show only matching announcements

**Search Tips:**
- Search is case-insensitive
- Partial matches are included in results
- Search looks in both title and content fields
- Use specific keywords for better results

**To Clear Search:**
1. Clear the search input field
2. Press **Enter** or click search again
3. All announcements will be displayed

**Expected Result:** Only announcements matching your search query are displayed.

### Task 3: Filtering Announcements by Category

Category filters help you view announcements from specific categories.

1. Locate the **"Filter by Category"** section below the search bar
2. View the available category filter buttons
3. Click on a category button to filter by that category
4. The button becomes highlighted when active
5. Click multiple categories to filter by multiple categories at once
6. Click an active category button again to remove that filter

**Filter Behavior:**
- Multiple categories can be selected simultaneously
- Results show announcements matching ANY selected category
- Filters work in combination with search
- Active filters are visually highlighted

**To Clear All Filters:**
1. Click all active category buttons to deselect them
2. Or refresh the page to reset all filters

**Expected Result:** Only announcements from the selected categories are displayed.

### Task 4: Editing an Announcement

Editing allows you to update any aspect of an existing announcement.

#### From Card View:

1. Locate the announcement you want to edit
2. Find the action buttons at the bottom of the announcement card
3. Click the **"Edit"** button (yellow/warning button with pencil icon)
4. The announcement edit form opens

#### From Table View:

1. Locate the announcement in the table
2. Find the **"Actions"** column on the right
3. Click the **"Edit"** button
4. The announcement edit form opens

#### Editing the Announcement:

1. The form opens with all current values pre-filled
2. Modify any fields you want to update:
   - **Title**: Update the announcement title
   - **Content**: Edit the announcement content
   - **Category**: Change the category
   - **Priority Level**: Adjust the priority
   - **Target Audience**: Change who can see it
   - **Is Active**: Toggle visibility (checkbox)

3. The **"Is Active"** checkbox controls visibility:
   - ☑ **Checked**: Announcement is visible to users
   - ☐ **Unchecked**: Announcement is hidden from users

4. Review your changes carefully

5. Click the **"Update Announcement"** button at the bottom

6. A confirmation dialog appears: "Are you sure you want to update this announcement?"

7. Click **"Yes, update it!"** to confirm

**Expected Result:**
- The announcement is updated with your changes
- Success message: "Announcement was updated successfully!"
- You are redirected to the announcements list
- The updated announcement reflects your changes

**Tips:**
- Use the "Is Active" checkbox to temporarily hide announcements without deleting them
- Deactivating an announcement removes it from user view but preserves the data
- You can reactivate announcements at any time by checking the box again

### Task 5: Deleting an Announcement

Deleting permanently removes an announcement from the system.

⚠️ **Warning:** Deletion is permanent and cannot be undone. Consider deactivating instead if you might need the announcement later.

#### From Card View:

1. Locate the announcement you want to delete
2. Find the action buttons at the bottom of the announcement card
3. Click the **"Delete"** button (red button with trash icon)
4. A confirmation dialog appears

#### From Table View:

1. Locate the announcement in the table
2. Find the **"Actions"** column on the right
3. Click the **"Delete"** button
4. A confirmation dialog appears

#### Confirming Deletion:

1. A SweetAlert confirmation dialog appears with the message:
   - "Are you sure you want to delete this announcement?"
   - "This action cannot be undone!"

2. Review the announcement details to ensure you're deleting the correct one

3. Click **"Yes, delete it!"** to confirm deletion
   - Or click **"Cancel"** to abort

4. If confirmed, a loading indicator appears: "Deleting announcement..."

**Expected Result:**
- The announcement is permanently deleted from the database
- Success message: "Announcement was deleted successfully!"
- The announcement is removed from the list
- The page updates to show remaining announcements

**Security Notes:**
- Only staff members and superusers can delete announcements
- Deletion requires POST request (cannot be done via direct URL access)
- AJAX-based deletion for smooth user experience
- Cache is automatically cleared when announcements are deleted

**Best Practices:**
- Always confirm you're deleting the correct announcement
- Consider deactivating instead of deleting for temporary removal
- Keep a backup or export of important announcements before deletion
- Document the reason for deletion if required by your organization

### Task 6: Viewing Announcement Details

You can view the full details of any announcement without editing it.

#### From Card View:

1. Locate the announcement you want to view
2. Click the **"View Details"** button (blue button)
3. Or click directly on the announcement title

#### From Table View:

1. Locate the announcement in the table
2. Click on the announcement title in the first column
3. Or click the **"View"** button in the actions column

**Detail View Shows:**
- Full announcement title
- Complete content (not truncated)
- Priority badge
- Category
- Date posted and last modified
- Target audience
- Views count
- Author information (if available)

**Expected Result:** A detailed view of the announcement opens, showing all information.

### Task 7: Using Pagination

When there are many announcements, pagination helps you navigate through pages.

1. Scroll to the bottom of the announcements list
2. Locate the pagination controls
3. View the pagination information:
   - "Showing X-Y of Z announcements"
   - Page numbers
   - Previous/Next buttons

**Navigation Options:**
- Click **"Previous"** to go to the previous page
- Click **"Next"** to go to the next page
- Click a specific page number to jump to that page
- The current page is highlighted

**Pagination Settings:**
- Default: 10 announcements per page
- Pagination works with search and filters
- Page state is maintained when using filters

**Expected Result:** You can navigate through all announcements efficiently.

### Task 8: Bulk Selection (If Available)

Some interfaces may support bulk operations on multiple announcements.

1. Look for checkboxes next to each announcement
2. Click the checkbox to select an announcement
3. Select multiple announcements as needed
4. A bulk actions bar appears showing the number selected
5. Choose a bulk action:
   - Bulk delete
   - Bulk activate/deactivate
   - Bulk category change

**Note:** Bulk operations may not be available in all views. Check your specific interface.

## Managing Announcements via Django Admin Panel

The Django admin panel provides additional management capabilities.

### Accessing Django Admin:

1. Navigate to `/admin/` in your browser
2. Log in with your admin credentials
3. Click on **"Announcements"** in the left sidebar
4. Click on **"Announcements"** to view the list

### Admin Panel Features:

**List View:**
- Displays: Title, Category, Priority, Target Audience, Date Posted, Active Status, Views Count
- **Filters** (right sidebar):
  - Filter by category
  - Filter by priority level
  - Filter by target audience
  - Filter by active status
  - Filter by date posted (date hierarchy)
- **Search**: Search by title or content
- **Actions**: Bulk delete selected announcements

**Edit View:**
- All fields are editable
- Additional fields:
  - Date posted (can be manually set)
  - Views count (read-only)
- Organized in fieldsets:
  - Basic information (title, content)
  - Classification (category, priority, target audience)
  - Status (is_active, views_count)
  - Dates (date_posted)

**Creating via Admin:**
- Click **"Add Announcement"** button
- Fill in all required fields
- Email notifications are automatically sent when saved
- Success/warning messages indicate notification status

### Admin Panel Advantages:

- More powerful filtering options
- Bulk operations on multiple announcements
- Direct database access
- Advanced search capabilities
- Date hierarchy navigation
- Audit trail (if configured)

## Tips and Best Practices

### Organization and Maintenance

1. **Regular Review**: Periodically review announcements and deactivate outdated ones
2. **Consistent Categorization**: Use categories consistently for better organization
3. **Archive Old Announcements**: Deactivate or delete announcements that are no longer relevant
4. **Monitor Engagement**: Check views count to see which announcements are being read
5. **Update Timely**: Edit announcements promptly if information changes

### Search and Filter Strategies

1. **Use Specific Keywords**: Search with unique terms for faster results
2. **Combine Filters**: Use category filters with search for precise results
3. **Save Common Searches**: Bookmark filtered views for frequently accessed categories
4. **Clear Filters**: Remember to clear filters when switching tasks

### Editing Best Practices

1. **Preview Before Publishing**: Review changes carefully before saving
2. **Update Timestamps**: Consider if the date should reflect the edit
3. **Notify Users**: For major changes, consider creating a new announcement
4. **Track Changes**: Keep notes on why edits were made (external documentation)
5. **Test Links**: If content includes links, verify they still work

### Deletion Guidelines

1. **Confirm First**: Always double-check before deleting
2. **Consider Deactivation**: Use "Is Active" toggle instead of deletion when possible
3. **Export Important Data**: Save copies of important announcements before deletion
4. **Communicate Changes**: Inform relevant parties when deleting public announcements
5. **Follow Policy**: Adhere to your organization's data retention policies

## Troubleshooting

### Common Issue 1: Cannot edit or delete announcements

**Solution:**
- Verify you are logged in as an admin user
- Check that your account has `is_staff` permission
- Ensure you're not trying to edit via GET request (use the edit button)
- Contact system administrator for permission issues

### Common Issue 2: Search returns no results

**Solution:**
- Check spelling of search terms
- Try broader search terms
- Clear any active category filters
- Verify announcements exist in the system
- Try searching in the Django admin panel instead

### Common Issue 3: Filters not working

**Solution:**
- Clear browser cache and reload the page
- Try deselecting all filters and reapplying
- Check browser console for JavaScript errors
- Verify categories are properly assigned to announcements
- Try using the Django admin panel filters

### Common Issue 4: Deleted announcement still appears

**Solution:**
- Refresh the page (Ctrl+F5 or Cmd+Shift+R)
- Clear browser cache
- Check if deletion actually succeeded (look for success message)
- Verify you have permission to delete
- Check system logs for errors

### Common Issue 5: Cannot see edit/delete buttons

**Solution:**
- Verify you are logged in as an admin
- Check that you have staff privileges
- Try accessing via Django admin panel
- Clear browser cache
- Check if buttons are hidden by CSS (try different browser)

### Common Issue 6: Changes not saving

**Solution:**
- Check for validation errors in the form
- Ensure all required fields are filled
- Verify reCAPTCHA if enabled
- Check browser console for JavaScript errors
- Try editing via Django admin panel
- Check system logs for server errors

### Common Issue 7: Pagination not working

**Solution:**
- Check if JavaScript is enabled in your browser
- Clear browser cache
- Try clicking page numbers instead of next/previous
- Check browser console for errors
- Verify URL parameters are correct

## Related Features

- [Creating Announcements](creating-announcements.md) - How to create new announcements
- [Viewing Announcements (User)](../../user-features/README.md) - How regular users view announcements
- [Category Management](../configuration/category-management.md) - Managing announcement categories
- [Email Configuration](../configuration/email-configuration.md) - Set up email notifications

## Additional Resources

- **Django Admin Panel**: `/admin/announcements/announcement/`
- **System Logs**: Check for errors and notification status
- **User Feedback**: Monitor user engagement with announcements
- **Analytics**: Track announcement views and engagement (if available)

## Quick Reference

### Keyboard Shortcuts (if available)
- `Ctrl/Cmd + F`: Focus search bar
- `Esc`: Close modals or dialogs
- `Enter`: Submit search

### Status Indicators
- 🟢 **Active**: Announcement is visible to users
- 🔴 **Inactive**: Announcement is hidden from users
- 🔴 **Urgent**: Red priority badge
- 🟠 **High**: Orange priority badge
- 🔵 **Medium**: Blue priority badge
- 🟢 **Low**: Green priority badge

### Common Actions
- **Edit**: Update announcement details
- **Delete**: Permanently remove announcement
- **View**: See full announcement details
- **Toggle Active**: Show/hide announcement
- **Filter**: Narrow down announcement list
- **Search**: Find specific announcements

---

**Last Updated:** November 2024  
**Version:** 1.0
