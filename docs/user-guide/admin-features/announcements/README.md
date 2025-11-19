# Announcements

This section covers how administrators can create and manage announcements in the NORSU Alumni System.

## Overview

Announcements are an essential communication tool for keeping the alumni community informed about important updates, events, and news. As an administrator, you have full control over creating, editing, and managing announcements with various targeting and prioritization options.

## Available Features

### [Creating Announcements](creating-announcements.md)
Learn how to create new announcements with proper targeting, categorization, and priority settings. This comprehensive guide covers:
- Accessing the announcement creation form
- Setting titles and content
- Selecting categories and priority levels
- Choosing target audiences (All Alumni, Recent Graduates, Specific Department)
- Publishing and automatic email notifications
- Creating public announcements for non-registered visitors

### [Managing Announcements](managing-announcements.md)
Discover how to view, edit, delete, and organize existing announcements. This guide covers:
- Viewing announcements list in card or table view
- Searching and filtering announcements by category
- Editing announcement details and toggling visibility
- Deleting announcements with confirmation
- Using pagination for large lists
- Managing via Django admin panel for advanced features

## Key Features

- **Target Audience Selection**: Send announcements to all alumni, recent graduates, or specific departments
- **Priority Levels**: Set urgency levels (Low, Medium, High, Urgent) with color-coded visual badges
- **Categorization**: Organize announcements by category for easy filtering and discovery
- **Email Notifications**: Automatically notify users when announcements are published
- **Visibility Control**: Activate or deactivate announcements without permanent deletion
- **Search and Filter**: Quickly find announcements using search and category filters
- **Multiple View Modes**: Switch between card view and table view for different workflows
- **Public Announcements**: Create announcements visible to non-registered visitors
- **reCAPTCHA Protection**: Security verification to prevent spam (if enabled)

## Quick Start

### Create Your First Announcement

1. Navigate to **Announcements** → **Create New Announcement**
2. Fill in the required fields:
   - **Title**: Clear, descriptive headline
   - **Content**: Detailed announcement information
   - **Category**: Select appropriate category
   - **Priority**: Choose urgency level
   - **Target Audience**: Select who should see it
3. Click **"Publish Announcement"**
4. Confirm publication in the dialog
5. Email notifications are sent automatically

### Manage Existing Announcements

1. Navigate to **Announcements** list
2. Use search bar to find specific announcements
3. Apply category filters to narrow results
4. Click **"Edit"** to update announcement details
5. Click **"Delete"** to permanently remove (with confirmation)
6. Toggle **"Is Active"** checkbox to show/hide without deletion

## Best Practices

### Writing Effective Announcements

- **Use Action-Oriented Titles**: Start with verbs like "Join," "Register," "Attend"
- **Front-Load Important Information**: Put critical details first
- **Include Clear Calls-to-Action**: Tell users exactly what to do
- **Be Timely**: Publish with adequate lead time
- **Keep It Relevant**: Only announce information that matters to your audience

### Audience Targeting

- **Segment Wisely**: Use targeted audiences to reduce notification fatigue
- **Test First**: Review before publishing to large audiences
- **Consider Overlap**: Some users may belong to multiple target groups
- **Follow Up**: Monitor engagement and send follow-up announcements if needed

### Maintenance

- **Regular Review**: Periodically review and deactivate outdated announcements
- **Consistent Categorization**: Use categories consistently for better organization
- **Monitor Engagement**: Check views count to see which announcements are being read
- **Update Timely**: Edit announcements promptly if information changes

## Who Can Use These Features

- **Admin Users**: Staff members with administrative privileges
- **Required Permission**: `is_staff` flag must be enabled
- **Access Level**: Full create, read, update, and delete permissions

## Priority Levels Explained

- 🔴 **URGENT** (Red badge): Critical information requiring immediate action
  - Example: Emergency campus closure notification
  
- 🟠 **HIGH** (Orange badge): Important updates requiring attention
  - Example: Registration deadline approaching
  
- 🔵 **MEDIUM** (Blue badge): Standard announcements, moderate importance
  - Example: Monthly newsletter published
  
- 🟢 **LOW** (Green badge): General information, non-urgent updates
  - Example: New alumni directory feature available

## Target Audience Options

- **All Alumni**: Visible to all registered alumni users (maximum reach)
- **Recent Graduates**: Visible only to alumni who graduated within the last 5 years
- **Specific Department**: Visible only to alumni from a specific department/program (determined by category)

## Related Documentation

- [Public Announcements](../../public-features/announcements.md) - How visitors view public announcements
- [User Announcements](../../user-features/README.md) - How registered users view announcements
- [Email Configuration](../configuration/README.md) - Set up email notifications
- [User Management](../user-management/README.md) - Manage user permissions

## Additional Resources

- **Django Admin Panel**: Access advanced announcement management at `/admin/announcements/announcement/`
- **System Logs**: Review email notification status and errors
- **Email Analytics**: Track announcement engagement (if available)
- **User Feedback**: Monitor user responses and questions

---

[← Back to Admin Features](../README.md) | [← Back to Main Documentation](../../README.md)
