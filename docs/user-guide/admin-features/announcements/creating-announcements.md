# Creating Announcements

## Overview

The announcement creation feature allows administrators to publish important updates, news, and information to the alumni community. Announcements can be targeted to specific audiences, categorized, and prioritized based on importance.

## Who Can Use This Feature

- **Admin Users**: Staff members with administrative privileges
- **Required Permission**: `is_staff` flag must be enabled

## Prerequisites

- Admin account with staff privileges
- Access to the admin dashboard
- Understanding of target audience options

## How to Access

1. Log in to your admin account
2. Navigate to the main navigation menu
3. Click on **"Announcements"**
4. Click the **"Create New Announcement"** button (or **"+ New Announcement"** icon)

**Alternative Access:**
- From the Django admin panel: Navigate to **Announcements** → **Add Announcement**

## Key Features

- **Rich Text Content**: Write detailed announcement content with formatting
- **Target Audience Selection**: Choose who can see the announcement
- **Priority Levels**: Set urgency levels (Low, Medium, High, Urgent)
- **Categorization**: Organize announcements by category
- **Email Notifications**: Automatically notify users when announcements are published
- **Visibility Control**: Set announcements as active or inactive
- **reCAPTCHA Protection**: Security verification to prevent spam (if enabled)

## Step-by-Step Guide

### Task 1: Navigate to Announcement Creation

1. From the main dashboard, locate the **Announcements** section in the navigation menu
2. Click on **"Announcements"** to view the announcements list
3. Look for the **"Create New Announcement"** button (usually at the top right)
4. Click the button to open the announcement creation form

**Expected Result:** The announcement creation form opens with empty fields ready for input.

### Task 2: Enter Announcement Title

1. Locate the **"Title"** field at the top of the form
2. Enter a clear, descriptive title for your announcement
   - Keep it concise (maximum 200 characters)
   - Make it attention-grabbing and informative
   - Example: "Alumni Homecoming 2024 - Save the Date!"

**Tips:**
- Use action-oriented language
- Include key information in the title
- Avoid all caps unless necessary for emphasis

**Expected Result:** The title appears in the input field and will be displayed prominently in the announcement list.

### Task 3: Select Announcement Category

1. Locate the **"Category"** dropdown field
2. Click the dropdown to view available categories
3. Select the most appropriate category for your announcement

**Available Categories:**
- General announcements
- Events
- Academic updates
- Career opportunities
- Alumni news
- System updates
- Other predefined categories

**Tips:**
- Choose the category that best matches your announcement content
- Categories help users filter and find relevant announcements
- If no suitable category exists, contact a system administrator to add one

**Expected Result:** The selected category is displayed in the dropdown and will be used to organize the announcement.

### Task 4: Set Priority Level

1. Locate the **"Priority Level"** dropdown field
2. Click the dropdown to view priority options
3. Select the appropriate priority level

**Priority Levels:**

- **LOW** (Green badge): General information, non-urgent updates
  - Example: "New alumni directory feature available"
  
- **MEDIUM** (Blue badge): Standard announcements, moderate importance
  - Example: "Monthly newsletter published"
  
- **HIGH** (Orange badge): Important updates requiring attention
  - Example: "Registration deadline approaching"
  
- **URGENT** (Red badge): Critical information requiring immediate action
  - Example: "Emergency campus closure notification"

**Tips:**
- Use URGENT sparingly to maintain its impact
- Consider the time-sensitivity of your announcement
- Higher priority announcements appear more prominently

**Expected Result:** The priority level is set and will be displayed as a colored badge on the announcement.

### Task 5: Select Target Audience

1. Locate the **"Target Audience"** dropdown field
2. Click the dropdown to view audience options
3. Select who should see this announcement

**Target Audience Options:**

- **All Alumni**: Visible to all registered alumni users
  - Use for: General announcements, system-wide updates
  - Reach: Entire alumni community
  
- **Recent Graduates**: Visible only to alumni who graduated within the last 5 years
  - Use for: Early career opportunities, recent graduate events
  - Reach: Alumni with graduation year within 5 years of current year
  
- **Specific Department**: Visible only to alumni from a specific department/program
  - Use for: Department-specific events, program updates
  - Reach: Alumni whose primary education matches the announcement category
  - Note: The department is determined by the selected category

**Tips:**
- Choose the most specific audience that needs to see the announcement
- "All Alumni" ensures maximum visibility
- Targeted announcements reduce notification fatigue
- Consider creating multiple announcements for different audiences if needed

**Expected Result:** The target audience is set and determines who can view the announcement.

### Task 6: Write Announcement Content

1. Locate the **"Content"** text area field
2. Click inside the field to begin typing
3. Write your announcement content with clear, detailed information

**Content Guidelines:**

- **Be Clear and Concise**: Get to the point quickly
- **Include Key Information**:
  - What: What is being announced
  - When: Relevant dates and times
  - Where: Location or platform
  - Why: Purpose or importance
  - How: Action steps if needed
  
- **Use Proper Formatting**:
  - Break content into paragraphs for readability
  - Use line breaks to separate sections
  - Keep paragraphs short (3-5 sentences)
  
- **Include Contact Information**: Provide a way for users to ask questions or get more details

**Example Content:**
```
We are excited to announce the NORSU Alumni Homecoming 2024!

Date: December 15, 2024
Time: 9:00 AM - 5:00 PM
Location: NORSU Main Campus, Dumaguete City

Join us for a day of reconnection, celebration, and networking with fellow alumni. The event will feature:
- Welcome ceremony and campus tour
- Alumni recognition awards
- Networking lunch
- Career fair and mentorship sessions
- Evening gala dinner

Registration is required. Please RSVP by December 1, 2024.

For more information, contact the Alumni Relations Office at alumni@norsu.edu.ph or call (035) 123-4567.

We look forward to seeing you there!
```

**Tips:**
- Write in a friendly, professional tone
- Proofread for spelling and grammar errors
- Include links to relevant resources if applicable
- Keep the content focused on one main topic

**Expected Result:** The content is entered and will be displayed in the announcement detail view. Line breaks are automatically converted to HTML breaks for proper formatting.

### Task 7: Review and Submit

1. Review all entered information:
   - ✓ Title is clear and descriptive
   - ✓ Category is appropriate
   - ✓ Priority level matches importance
   - ✓ Target audience is correct
   - ✓ Content is complete and error-free

2. If reCAPTCHA is enabled, complete the security verification

3. Click the **"Publish Announcement"** button at the bottom of the form

4. A confirmation dialog will appear asking "Are you sure you want to publish this announcement?"

5. Click **"Yes, publish it!"** to confirm

**Expected Result:** 
- The announcement is created and saved to the database
- The system displays a success message: "Announcement was created successfully!"
- Email notifications are automatically sent to the target audience
- You are redirected to the announcements list
- The new announcement appears at the top of the list

### Task 8: Verify Email Notifications (Optional)

After publishing, the system automatically sends email notifications to users in the target audience.

**Notification Behavior:**
- Emails are sent asynchronously to avoid delays
- Users receive a notification with the announcement title and preview
- The email includes a link to view the full announcement
- Only active users in the target audience receive notifications

**Success Indicators:**
- Success message: "Email notifications have been sent successfully."
- Warning message: "The announcement was created but there was an error sending email notifications." (announcement is still published)

**Tips:**
- Check the system logs if email notifications fail
- Verify email configuration settings if issues persist
- Users can still view the announcement even if email fails

## Creating Public Announcements

Public announcements are visible to non-registered visitors on the public website.

### How to Create a Public Announcement:

1. Navigate to **Public Announcements** section (if available in your interface)
2. Click **"Create Public Announcement"**
3. Fill in the form fields:
   - Title
   - Content
   - Category
   - Priority Level
4. Note: Target audience is automatically set to "All Alumni" and cannot be changed
5. Click **"Publish Announcement"**

**Use Cases for Public Announcements:**
- Major university events open to the public
- Important system-wide updates
- Public relations announcements
- Community engagement initiatives

## Tips and Best Practices

### Writing Effective Announcements

1. **Use Action-Oriented Titles**: Start with verbs like "Join," "Register," "Attend," "Update"
2. **Front-Load Important Information**: Put the most critical details first
3. **Include Clear Calls-to-Action**: Tell users exactly what you want them to do
4. **Be Timely**: Publish announcements with adequate lead time
5. **Keep It Relevant**: Only announce information that matters to your audience

### Timing Considerations

- **Advance Notice**: Publish event announcements at least 2-4 weeks in advance
- **Urgent Updates**: Use URGENT priority only for time-sensitive, critical information
- **Regular Updates**: Maintain a consistent announcement schedule
- **Avoid Overload**: Don't publish too many announcements at once

### Audience Targeting

- **Segment Wisely**: Use targeted audiences to reduce notification fatigue
- **Consider Overlap**: Some users may belong to multiple target groups
- **Test First**: Create a draft and review before publishing to large audiences
- **Follow Up**: Monitor engagement and follow up with additional announcements if needed

### Content Quality

- **Proofread Carefully**: Check for typos, grammar, and factual accuracy
- **Use Consistent Formatting**: Maintain a professional appearance
- **Include Visuals**: While not directly supported in the form, reference images or documents
- **Provide Context**: Explain why the announcement matters to the audience

## Troubleshooting

### Common Issue 1: "You don't have permission to perform this action"

**Solution:**
- Verify you are logged in with an admin account
- Check that your account has the `is_staff` flag enabled
- Contact a system administrator to grant proper permissions

### Common Issue 2: Email notifications not sending

**Solution:**
- The announcement is still published successfully
- Check system email configuration settings
- Verify email service (SMTP, Brevo, SendGrid) is properly configured
- Review system logs for specific error messages
- Contact technical support if issue persists

### Common Issue 3: reCAPTCHA verification fails

**Solution:**
- Ensure you have a stable internet connection
- Try refreshing the page and submitting again
- Clear browser cache and cookies
- Try a different browser
- Contact administrator if reCAPTCHA is misconfigured

### Common Issue 4: Category dropdown is empty

**Solution:**
- Categories must be created first in the Django admin panel
- Navigate to **Admin Panel** → **Announcements** → **Categories**
- Add at least one category before creating announcements
- Contact a system administrator to add categories

### Common Issue 5: Cannot see the "Create Announcement" button

**Solution:**
- Verify you are logged in as an admin user
- Check that you have staff privileges
- Clear browser cache and reload the page
- Try accessing via the Django admin panel instead

## Related Features

- [Managing Announcements](managing-announcements.md) - Edit, delete, and filter announcements
- [Viewing Announcements (User)](../../user-features/README.md) - How regular users view announcements
- [Email Configuration](../configuration/email-configuration.md) - Set up email notifications
- [User Management](../user-management/README.md) - Manage user permissions

## Additional Resources

- **Django Admin Panel**: Access advanced announcement management features
- **System Logs**: Review email notification status and errors
- **Email Analytics**: Track announcement engagement (if available)
- **User Feedback**: Monitor user responses and questions

---

**Last Updated:** November 2024  
**Version:** 1.0
