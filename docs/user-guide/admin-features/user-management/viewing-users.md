# Viewing Users

## Overview

The user list view provides administrators with a comprehensive overview of all registered users in the system. You can browse, search, and filter users to quickly find specific accounts or groups of users.

## Accessing the User List

### Step 1: Log in to Admin Panel

1. Navigate to your site's admin URL (typically `/admin/`)
2. Enter your admin credentials
3. Click "Log in"

**Expected Result**: You are logged into the Django admin dashboard

### Step 2: Navigate to Users

1. From the admin dashboard, locate the "AUTHENTICATION AND AUTHORIZATION" section
2. Click on "Users"

**Expected Result**: You see the user list page with all registered users

![User List View](../../screenshots/admin-user-list.png)

## Understanding the User List

### List Display Columns

The user list displays the following information for each user:

- **Username**: The user's unique username
- **Email**: The user's email address
- **First Name**: User's first name
- **Last Name**: User's last name
- **Staff Status**: Indicates if the user has staff privileges (checkmark icon)
- **Active Status**: Indicates if the account is active (checkmark icon)

### User Count

At the top of the list, you'll see the total number of users in the system.

## Searching for Users

### Using the Search Bar

1. Locate the search bar at the top right of the user list
2. Enter your search term (username, email, first name, or last name)
3. Press Enter or click the search icon

**Search Capabilities**:
- Search by username
- Search by email address
- Search by first name
- Search by last name
- Partial matches are supported

**Expected Result**: The list filters to show only users matching your search term

**Example**: Searching for "john" will show all users with "john" in their username, email, first name, or last name.

### Clearing Search

1. Click the "X" button next to the search bar
2. Or delete the search term and press Enter

**Expected Result**: The full user list is displayed again

## Filtering Users

### Available Filters

The right sidebar contains filter options:

#### 1. Staff Status Filter
- **All**: Show all users
- **Yes**: Show only staff users
- **No**: Show only non-staff users

#### 2. Active Status Filter
- **All**: Show all users
- **Yes**: Show only active users
- **No**: Show only inactive/deactivated users

#### 3. Groups Filter
- **All**: Show all users
- **[Group Name]**: Show only users in a specific group

### Applying Filters

1. Click on the desired filter option in the right sidebar
2. The list automatically updates to show filtered results
3. You can combine multiple filters

**Expected Result**: The user list shows only users matching the selected filter criteria

**Example**: Select "Staff status: Yes" and "Active: Yes" to see all active staff members.

### Clearing Filters

1. Click "All" in each filter category
2. Or click the "Clear all filters" link at the top of the filter sidebar

**Expected Result**: All filters are removed and the full user list is displayed

## Sorting Users

### Default Sorting

By default, users are sorted alphabetically by username.

### Changing Sort Order

1. Click on any column header to sort by that column
2. Click again to reverse the sort order (ascending/descending)

**Sortable Columns**:
- Username
- Email
- First Name
- Last Name

**Expected Result**: The list reorders based on the selected column and sort direction

## Pagination

### Navigating Pages

If there are many users, the list is divided into pages:

1. Use the pagination controls at the bottom of the list
2. Click page numbers to jump to a specific page
3. Use "Previous" and "Next" buttons to navigate sequentially

**Default**: 100 users per page

## Viewing User Details

### Quick View

1. Hover over a username to see a preview tooltip (if available)

### Full Details View

1. Click on a username in the list
2. You are taken to the user detail/edit page

**Expected Result**: You see the complete user information including:
- Basic account information
- Personal information
- Permissions and groups
- Important dates (last login, date joined)
- Associated profile data

See [Managing Users](./managing-users.md) for details on editing user information.

## Bulk Actions

### Selecting Multiple Users

1. Check the checkbox next to each user you want to select
2. Or check the checkbox in the header row to select all users on the current page

### Available Bulk Actions

Currently, bulk actions are limited. Individual user management is recommended for most operations.

## Tips and Best Practices

### Efficient Searching
- Use specific search terms to narrow results quickly
- Combine search with filters for precise results
- Remember that search looks across multiple fields (username, email, name)

### Finding Inactive Accounts
1. Use the "Active: No" filter
2. Review these accounts periodically
3. Consider if they should be reactivated or permanently removed

### Identifying Staff Members
1. Use the "Staff status: Yes" filter
2. Review staff permissions regularly
3. Ensure only authorized users have staff access

### Regular Audits
- Periodically review the user list
- Check for duplicate accounts
- Verify staff and superuser assignments
- Monitor new registrations

### Performance Considerations
- Use filters to reduce the number of displayed users
- Search for specific users rather than scrolling through pages
- Export user data for offline analysis if needed

## Troubleshooting

### Issue: Cannot see the Users section

**Solution**: 
- Verify you are logged in as a staff or admin user
- Check that you have the "Can view user" permission
- Contact a superuser if you need access

### Issue: Search returns no results

**Solution**:
- Check your spelling
- Try a partial search term
- Clear any active filters that might be limiting results
- Verify the user exists in the system

### Issue: Filters not working

**Solution**:
- Clear your browser cache
- Try refreshing the page
- Check if you have JavaScript enabled
- Try a different browser

### Issue: User list loads slowly

**Solution**:
- Use filters to reduce the number of displayed users
- Check your internet connection
- Contact system administrator if performance issues persist

## Related Documentation

- [Managing Users](./managing-users.md) - Edit user information and permissions
- [Profile Management](../../user-features/profile-management/README.md) - User profile features
- [Alumni Directory](../../user-features/alumni-directory/README.md) - Public-facing directory
