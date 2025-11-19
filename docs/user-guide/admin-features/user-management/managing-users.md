# Managing Users

## Overview

User management allows administrators to edit user information, manage roles and permissions, and activate or deactivate user accounts. This comprehensive guide covers all aspects of managing individual user accounts.

## Prerequisites

- Admin or staff account with appropriate permissions
- Access to the Django admin panel
- Understanding of user roles and permissions

## Accessing User Management

### Step 1: Navigate to User Detail Page

1. Log in to the admin panel
2. Go to "Users" under "AUTHENTICATION AND AUTHORIZATION"
3. Click on the username of the user you want to manage

**Expected Result**: You see the user edit form with all user information

![User Edit Form](../../screenshots/admin-user-edit.png)

## Editing User Information

### Basic Account Information

#### Editing Username

1. Locate the "Username" field at the top of the form
2. Modify the username as needed
3. Scroll to the bottom and click "Save"

**Important Notes**:
- Usernames must be unique
- Usernames can contain letters, numbers, and @/./+/-/_ characters
- Changing username may affect user login

**Expected Result**: Username is updated and user can log in with the new username

#### Editing Password

1. Locate the "Password" field
2. Click on the "this form" link next to the password hash
3. Enter the new password twice
4. Click "Change password"

**Alternative Method**:
1. Click "Change password" button at the top right of the user form
2. Enter new password twice
3. Click "Change password"

**Password Requirements**:
- Minimum 8 characters
- Cannot be too similar to other personal information
- Cannot be entirely numeric
- Cannot be a commonly used password

**Expected Result**: User password is updated and they can log in with the new password

**Security Note**: Users will need to use the new password for their next login. Consider notifying them of the password change.

### Personal Information

#### Editing Name

1. Locate the "Personal info" section
2. Update the "First name" field
3. Update the "Last name" field
4. Click "Save" at the bottom

**Expected Result**: User's name is updated throughout the system

#### Editing Email

1. Locate the "Email" field in the "Personal info" section
2. Update the email address
3. Click "Save"

**Important Notes**:
- Email addresses should be unique
- User will receive system notifications at this email
- Consider verifying the new email address

**Expected Result**: User's email is updated and they receive notifications at the new address

### Profile Information

The user edit form includes an inline profile section where you can edit:

#### Basic Profile Fields

1. Scroll to the "Profile" section
2. Edit any of the following fields:
   - Avatar (upload new profile photo)
   - Bio
   - Birth date
   - Gender
   - Phone number
   - Address

3. Click "Save" at the bottom

**Expected Result**: User's profile information is updated

#### Professional Information

1. In the "Profile" section, locate professional fields:
   - Current position
   - Current employer
   - Industry
   - Employment status
   - Salary range

2. Update as needed
3. Click "Save"

**Expected Result**: User's professional information is updated in their profile

## Managing User Roles and Permissions

### Understanding User Roles

#### Regular User
- Default role for all registered alumni
- Can access standard features (profile, directory, events, etc.)
- Cannot access admin panel

#### Staff User
- Can access the admin panel
- Permissions are controlled by groups and individual permissions
- Cannot access all admin features by default

#### Superuser
- Full access to all admin features
- Can create and modify other admin accounts
- Should be limited to trusted administrators

### Making a User Staff

1. Locate the "Permissions" section
2. Check the "Staff status" checkbox
3. Click "Save"

**Expected Result**: User can now log in to the admin panel (with limited permissions based on their groups)

**Important**: Staff status alone doesn't grant specific permissions. You must also assign groups or individual permissions.

### Making a User Superuser

1. Locate the "Permissions" section
2. Check the "Superuser status" checkbox
3. Click "Save"

**Expected Result**: User has full admin access to all features

**Security Warning**: Only grant superuser status to fully trusted administrators. Superusers can:
- Access all data
- Modify any user account
- Change system settings
- Delete critical data

### Assigning Groups

Groups are collections of permissions that can be assigned to users for easier permission management.

#### Adding User to Groups

1. Locate the "Groups" field in the "Permissions" section
2. Select groups from the "Available groups" list
3. Click the right arrow (→) to move them to "Chosen groups"
4. Click "Save"

**Common Groups**:
- **Content Managers**: Can manage CMS content, announcements, events
- **HR Staff**: Can manage job postings and applications
- **Finance Staff**: Can manage donations and campaigns
- **Survey Managers**: Can create and manage surveys

**Expected Result**: User gains all permissions associated with the selected groups

#### Removing User from Groups

1. In the "Groups" field, select groups from "Chosen groups"
2. Click the left arrow (←) to move them back to "Available groups"
3. Click "Save"

**Expected Result**: User loses permissions associated with the removed groups

### Assigning Individual Permissions

For fine-grained control, you can assign specific permissions to users.

#### Adding Permissions

1. Locate the "User permissions" field in the "Permissions" section
2. Select permissions from the "Available user permissions" list
3. Use the filter box to search for specific permissions
4. Click the right arrow (→) to move them to "Chosen user permissions"
5. Click "Save"

**Permission Format**: `app_label | model_name | Can [action] model_name`

**Example Permissions**:
- `accounts | profile | Can view profile`
- `events | event | Can add event`
- `announcements | announcement | Can change announcement`

**Expected Result**: User gains the selected permissions

#### Removing Permissions

1. Select permissions from "Chosen user permissions"
2. Click the left arrow (←) to move them back
3. Click "Save"

**Expected Result**: User loses the selected permissions

### Best Practices for Permissions

1. **Use Groups**: Assign users to groups rather than individual permissions when possible
2. **Principle of Least Privilege**: Only grant permissions necessary for the user's role
3. **Regular Audits**: Periodically review user permissions
4. **Document Roles**: Maintain documentation of what each group can do
5. **Test Permissions**: Verify that users can access what they need and nothing more

## Activating and Deactivating Accounts

### Deactivating a User Account

Deactivating an account prevents the user from logging in without deleting their data.

#### Steps to Deactivate

1. Locate the "Permissions" section
2. Uncheck the "Active" checkbox
3. Click "Save"

**Expected Result**: 
- User cannot log in
- User's data remains in the system
- User's profile is hidden from the alumni directory
- User cannot receive connection requests or messages

**When to Deactivate**:
- User requests account suspension
- Suspicious account activity
- Policy violations
- Temporary access removal

### Reactivating a User Account

#### Steps to Reactivate

1. Navigate to the deactivated user's edit page
2. Locate the "Permissions" section
3. Check the "Active" checkbox
4. Click "Save"

**Expected Result**:
- User can log in again
- User's profile becomes visible in the directory
- User can use all features normally

### Permanent Account Deletion

**Warning**: Deleting a user permanently removes all their data. This action cannot be undone.

#### Steps to Delete

1. Navigate to the user's edit page
2. Click the "Delete" button at the bottom left
3. Review the list of related objects that will be deleted
4. Confirm by clicking "Yes, I'm sure"

**What Gets Deleted**:
- User account
- Profile information
- Education and experience records
- Skills and documents
- Connections
- Messages
- Event RSVPs
- Job applications
- All related data

**Expected Result**: User and all associated data are permanently removed from the system

**Best Practice**: Consider deactivating accounts instead of deleting them to preserve data integrity and audit trails.

## Viewing User Activity

### Important Dates

The "Important dates" section shows:

#### Last Login
- Shows when the user last logged in
- Helps identify inactive accounts
- Useful for security audits

#### Date Joined
- Shows when the user registered
- Helps track user tenure
- Useful for analytics

### Viewing Related Data

From the user edit page, you can access related information:

#### Profile Data
- Inline profile section shows basic profile information
- Click "View on site" to see the user's public profile

#### Education and Experience
- Visible in the inline profile section
- Shows user's academic and professional background

#### Skills and Documents
- Listed in the profile inline section
- Shows uploaded documents and listed skills

## Bulk User Management

### Exporting User Data

1. Go to the user list page
2. Select users using checkboxes
3. Choose "Export selected users" from the action dropdown (if available)
4. Click "Go"

**Expected Result**: User data is exported in the selected format (CSV, Excel, etc.)

### Bulk Status Changes

While individual user management is recommended, you can use Django admin actions for bulk operations:

1. Select multiple users using checkboxes
2. Choose an action from the dropdown
3. Click "Go"
4. Confirm the action

**Available Actions** (may vary based on configuration):
- Activate selected users
- Deactivate selected users

## Tips and Best Practices

### User Management Best Practices

1. **Regular Audits**: Review user accounts and permissions quarterly
2. **Document Changes**: Keep a log of significant permission changes
3. **Communicate Changes**: Notify users when their permissions change
4. **Test After Changes**: Verify that permission changes work as expected
5. **Backup Before Bulk Changes**: Always backup before making bulk modifications

### Security Best Practices

1. **Limit Superusers**: Keep the number of superuser accounts to a minimum
2. **Strong Passwords**: Enforce strong password policies
3. **Monitor Staff Accounts**: Regularly review staff and admin accounts
4. **Remove Unused Accounts**: Deactivate or delete accounts that are no longer needed
5. **Audit Logs**: Review user activity logs for suspicious behavior

### Permission Management

1. **Use Groups**: Create groups for common roles (Content Manager, HR Staff, etc.)
2. **Least Privilege**: Only grant necessary permissions
3. **Regular Reviews**: Audit permissions quarterly
4. **Document Roles**: Maintain clear documentation of what each role can do
5. **Test Permissions**: Verify permissions work correctly after changes

### Communication

1. **Notify Users**: Inform users when their account status changes
2. **Explain Changes**: Provide reasons for permission changes
3. **Provide Support**: Offer help if users have issues after changes
4. **Document Policies**: Maintain clear policies for account management

## Troubleshooting

### Issue: Cannot save user changes

**Possible Causes**:
- Duplicate username or email
- Invalid data in required fields
- Permission issues

**Solutions**:
- Check for validation errors at the top of the form
- Ensure username and email are unique
- Verify all required fields are filled
- Check that you have permission to edit users

### Issue: User cannot log in after changes

**Possible Causes**:
- Account is deactivated
- Password was changed
- Username was changed

**Solutions**:
- Verify "Active" checkbox is checked
- Confirm the user is using the correct username/password
- Check if email verification is required
- Review any error messages on the login page

### Issue: User doesn't have expected permissions

**Possible Causes**:
- Not assigned to correct groups
- Individual permissions not granted
- Staff status not enabled

**Solutions**:
- Verify user is in the correct groups
- Check individual permissions
- Ensure "Staff status" is checked if admin access is needed
- Clear cache and have user log out and back in

### Issue: Cannot make user a superuser

**Possible Causes**:
- You are not a superuser yourself
- Permission restrictions

**Solutions**:
- Only superusers can create other superusers
- Contact an existing superuser for assistance
- Verify you are logged in with the correct account

### Issue: Changes not reflecting immediately

**Solutions**:
- Have the user log out and log back in
- Clear browser cache
- Wait a few minutes for cache to expire
- Check if changes were actually saved

## Related Documentation

- [Viewing Users](./viewing-users.md) - Browse and search users
- [Profile Management](../../user-features/profile-management/README.md) - User profile features
- [Account Management](../../user-features/account-management/README.md) - User account features
- [Analytics](../analytics/README.md) - User activity analytics
