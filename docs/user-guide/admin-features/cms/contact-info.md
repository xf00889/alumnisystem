# Contact Info

## Overview

Contact Information Management allows you to create and maintain multiple contact entries that are displayed on the Contact page. This feature enables you to provide various ways for visitors and alumni to reach different departments or offices.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions
- Office administrators

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system
- Access to CMS Dashboard
- Contact details for various departments or offices

## How to Access

### Method 1: Through CMS Dashboard
1. Navigate to CMS Dashboard (`/cms/dashboard/`)
2. Click on "Contact Information" or "Manage Contact Info"
3. You will see the list of all contact information entries

### Method 2: Direct URL
- Navigate to `/cms/contact-info/`

## Contact Types

The system supports the following contact information types:

1. **Phone Number**: Telephone and mobile numbers
2. **Email Address**: Email contacts for different purposes
3. **Physical Address**: Office locations and mailing addresses
4. **Office Hours**: Operating hours and availability
5. **Social Media**: Social media handles and links

## Key Features

### 1. View All Contact Information
- List view of all contact entries
- Filter by contact type
- Sort by type or order
- Pagination for large lists
- Primary contact indicators

### 2. Add New Contact Information
- Create new contact entries
- Choose contact type
- Set as primary contact
- Set display order
- Activate or deactivate

### 3. Edit Contact Information
- Update contact details
- Change contact type
- Update primary status
- Adjust display order
- Toggle active status

### 4. Delete Contact Information
- Remove outdated contact entries
- Confirmation required
- Permanent action

### 5. Primary Contact Designation
- Mark most important contact of each type
- Highlight primary contacts
- One primary per contact type

## Step-by-Step Guide

### Task 1: View Contact Information List

1. Access Contact Information from CMS Dashboard
2. View the list of all contact entries
3. Observe the following information:
   - Contact type
   - Contact value (truncated if long)
   - Primary status
   - Display order
   - Active status
4. Use pagination to navigate through multiple pages
5. Click on entries to view full details

**Expected Result**: Complete list of all contact information entries organized by type.

### Task 2: Add a New Contact Information Entry

1. From the Contact Information list, click "Add Contact Info" or "Create New"
2. Fill in the contact information details:

   **Contact Type** (required):
   - Select from dropdown menu:
     - Phone Number
     - Email Address
     - Physical Address
     - Office Hours
     - Social Media
   
   **Value** (required):
   - Enter the contact information
   - Format depends on type:
     - **Phone**: +63 35 422 6002
     - **Email**: alumni@norsu.edu.ph
     - **Address**: Full address with line breaks
     - **Hours**: Monday-Friday, 8:00 AM - 5:00 PM
     - **Social**: @norsu_alumni or full URL
   - Can be multi-line for addresses or hours
   
   **Is Primary**:
   - Check to mark as primary contact of this type
   - Only one primary per contact type recommended
   - Primary contacts may be highlighted on website
   
   **Order**:
   - Enter a number for display order
   - Lower numbers appear first
   - Default: 0
   - Use increments of 10 (10, 20, 30...)
   - Organize by importance or department
   
   **Is Active**:
   - Check to make entry visible
   - Uncheck to hide without deleting

3. Review all entered information
4. Click "Save" or "Create Contact Info"

**Expected Result**: New contact information entry is created and appears on the Contact page.

### Task 3: Edit Contact Information

1. From the Contact Information list, find the entry to edit
2. Click the "Edit" button or entry value
3. Update any of the following fields:
   - Contact type
   - Value
   - Is primary
   - Order
   - Active status
4. Make necessary changes
5. Click "Save" or "Update Contact Info"

**Expected Result**: Contact information is updated. Changes appear on the Contact page.

### Task 4: Set Primary Contacts

1. View the Contact Information list
2. For each contact type, identify the most important entry
3. Edit that entry
4. Check the "Is Primary" checkbox
5. Save the entry
6. If another entry of the same type was primary:
   - Edit that entry
   - Uncheck "Is Primary"
   - Save the entry

**Best Practice**: Have one primary contact for each type:
- One primary phone number
- One primary email address
- One primary physical address
- One primary office hours entry
- One primary social media link

**Expected Result**: Primary contacts are highlighted or displayed prominently on the Contact page.

### Task 5: Organize Contact Information by Department

1. Plan your organization structure:
   - Main office contacts: Order 10-19
   - Alumni affairs: Order 20-29
   - Admissions: Order 30-39
   - Student services: Order 40-49
   - And so on...

2. Edit each contact entry
3. Update the "Order" field according to your structure
4. Save each entry
5. Return to list view to verify organization

**Expected Result**: Contact information displays organized by department or function on the Contact page.

### Task 6: Add Multiple Contact Methods

**Example: Adding contacts for Alumni Affairs Office**

1. **Add Phone Number**:
   - Type: Phone Number
   - Value: +63 35 422 6002 ext. 123
   - Is Primary: Yes (if main number)
   - Order: 20

2. **Add Email Address**:
   - Type: Email Address
   - Value: alumni.affairs@norsu.edu.ph
   - Is Primary: Yes (if main email)
   - Order: 21

3. **Add Physical Address**:
   - Type: Physical Address
   - Value: 
     ```
     Alumni Affairs Office
     2nd Floor, Administration Building
     NORSU Main Campus
     Dumaguete City, 6200
     ```
   - Is Primary: Yes (if main office)
   - Order: 22

4. **Add Office Hours**:
   - Type: Office Hours
   - Value: Monday-Friday, 8:00 AM - 5:00 PM
   - Is Primary: Yes
   - Order: 23

**Expected Result**: Complete contact information for Alumni Affairs Office is displayed together on the Contact page.

### Task 7: Deactivate Contact Information

1. From the Contact Information list, find the entry
2. Click "Edit" on the contact info
3. Uncheck the "Is Active" checkbox
4. Click "Save"

**Use Cases**:
- Temporary phone number changes
- Office closed for renovation
- Seasonal hour changes
- Testing before making public

**Expected Result**: Contact information no longer appears on the Contact page but remains in admin list.

### Task 8: Delete Contact Information

1. From the Contact Information list, find the entry to delete
2. Click the "Delete" button
3. Review the confirmation page:
   - Contact details are displayed
   - Warning about permanent deletion
4. Confirm you want to delete
5. Click "Yes, delete" or "Confirm deletion"

**Use Cases**:
- Outdated contact information
- Duplicate entries
- Incorrect information

**Expected Result**: Contact information entry is permanently removed from the system.

## Contact Information Best Practices

### Phone Numbers
- Include country code for international format: +63
- Include area code
- Add extension if applicable: ext. 123
- Use consistent formatting across all numbers
- Specify if mobile or landline
- Examples:
  - +63 35 422 6002
  - +63 917 123 4567 (Mobile)
  - +63 35 422 6002 ext. 150

### Email Addresses
- Use official institutional email addresses
- Create department-specific emails when possible
- Avoid personal email addresses
- Ensure emails are monitored regularly
- Use descriptive email names
- Examples:
  - alumni@norsu.edu.ph
  - alumni.affairs@norsu.edu.ph
  - info@norsu.edu.ph

### Physical Addresses
- Include complete address information
- Use line breaks for readability
- Include building and room numbers
- Add postal code
- Include country for international visitors
- Example format:
  ```
  Office Name
  Building Name, Floor/Room
  Street Address
  City, Postal Code
  Province, Country
  ```

### Office Hours
- Specify days of operation
- Use 12-hour or 24-hour format consistently
- Include time zone if relevant
- Note holidays or special closures
- Specify if by appointment only
- Examples:
  - Monday-Friday, 8:00 AM - 5:00 PM
  - Monday-Friday, 08:00 - 17:00 (PHT)
  - By appointment only

### Social Media
- Include platform name
- Provide full URL or handle
- Verify links work correctly
- Keep accounts active
- Examples:
  - Facebook: facebook.com/norsu.alumni
  - Twitter: @norsu_alumni
  - Instagram: @norsu.alumni

## Tips and Best Practices

1. **Accuracy**: Verify all contact information before publishing
2. **Regular Updates**: Review and update contact info quarterly
3. **Accessibility**: Ensure contact methods are accessible to all users
4. **Response Time**: Only list contacts that are actively monitored
5. **Organization**: Group related contacts together using order field
6. **Clarity**: Be specific about which office or department each contact reaches
7. **Redundancy**: Provide multiple contact methods when possible
8. **Testing**: Test phone numbers and email addresses before publishing
9. **Privacy**: Don't publish personal contact information
10. **Backup**: Keep records of contact information changes

## Important Notes

- **Primary Contacts**: Only one primary contact per type is recommended
- **Public Display**: All active contact information is publicly visible
- **Deletion**: Deleting a contact entry is permanent and cannot be undone
- **Order Conflicts**: Multiple entries can have the same order value
- **Contact Types**: Choose the most appropriate type for each entry

## Troubleshooting

### Contact Information Not Appearing

**Issue**: Added or edited contact info doesn't show on Contact page

**Solutions**:
- Verify "Is Active" checkbox is checked
- Clear browser cache and refresh
- Check display order
- Verify Contact page template includes contact info section
- Wait a few moments for cache to clear

### Email Links Not Working

**Issue**: Email addresses don't create clickable mailto links

**Solutions**:
- Verify email format is correct (no spaces)
- Check template renders emails as mailto links
- Test with different email address
- Ensure contact type is set to "Email Address"
- Check browser email client settings

### Phone Numbers Not Formatted

**Issue**: Phone numbers display without proper formatting

**Solutions**:
- Enter phone numbers with desired formatting
- Use consistent format across all entries
- Consider using international format
- Check if template applies automatic formatting
- Manually format in the value field

### Primary Contact Not Highlighted

**Issue**: Primary contact doesn't appear different from others

**Solutions**:
- Verify "Is Primary" checkbox is checked
- Check if template supports primary contact styling
- Clear browser cache
- Verify only one primary per contact type
- Check CSS styling for primary contacts

### Multiple Primary Contacts

**Issue**: Multiple entries marked as primary for same type

**Solutions**:
- Review all entries of that contact type
- Uncheck "Is Primary" for all but one
- Choose the most important as primary
- Save all updated entries
- Refresh Contact page to verify

### Cannot Save Contact Information

**Issue**: Save button doesn't work or shows errors

**Solutions**:
- Check for validation errors (red text near fields)
- Ensure required fields are filled (Type, Value)
- Verify value format is appropriate for type
- Try refreshing the page and re-entering data
- Contact system administrator if issue persists

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [Site Configuration](site-configuration.md) - Manage global contact settings
- [FAQ Management](faq.md) - Manage frequently asked questions
- [Staff Members Management](staff-members.md) - Manage staff contact information

## Screenshots

> **Note**: Screenshots should be added showing:
> - Contact Information list view with different types
> - Create new contact info form
> - Contact type dropdown menu
> - Edit contact info form
> - Primary contact checkbox
> - Order field and organization
> - Active/inactive toggle
> - Delete confirmation page
> - Contact information display on Contact page
> - Success messages after create/edit/delete
> - Multiple contact methods for one department
