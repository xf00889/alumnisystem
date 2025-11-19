# Managing Applications

## Overview

The job application management feature allows administrators and HR staff to review, process, and manage all applications submitted for job postings. You can view applicant details, update application statuses, send emails to applicants, add notes, download documents, and export applicant data for further analysis.

## Who Can Use This Feature

- **User Role**: Admin users and HR staff only
- **Permissions Required**: Admin or HR group membership
- **Prerequisites**: 
  - Active admin or HR account
  - Access to job posting management area
  - At least one job posting with applications

## How to Access

1. Log in to your admin account
2. Navigate to the **Jobs** section from the admin menu
3. Click on **Manage Jobs**
4. On any job card, click the application count link (e.g., "5 applications")
   - Or click **View** on a job card, then navigate to the applications section

## Key Features

- View all applications for a specific job
- Monitor application statistics by status
- Update application status (Pending, Shortlisted, Interviewed, Accepted, Rejected)
- View detailed applicant information
- Download applicant resumes and documents
- Send emails directly to applicants
- Add internal notes to applications
- Filter applications by status
- Export applicant data to Excel
- Paginate through large numbers of applications

## Step-by-Step Guide

### Task 1: Viewing Applications Dashboard

This task covers accessing and understanding the applications management interface.

1. **Access the applications page**
   - From the jobs management dashboard, click on the application count for a job
   - Or navigate to a job detail page and click **Manage Applications**
   - **Expected Result**: Applications management page appears for that specific job

2. **Review the page header**
   - Page title shows: "Applications for [Job Title]"
   - Subtitle displays total application count
   - **Expected Result**: Job title and application count are visible

3. **Review application statistics**
   - Four colored stat cards display:
     - **Pending Review** (Orange): Applications awaiting initial review
     - **Shortlisted** (Blue): Applications selected for further consideration
     - **Interviewed** (Green): Applications that have been interviewed
     - **Accepted** (Purple): Applications that have been accepted
   - Each card shows the count for that status
   - **Expected Result**: Statistics provide overview of application pipeline

4. **View the applications table**
   - Table displays all applications with columns:
     - **Applicant**: Name, avatar, and email
     - **Status**: Current application status (dropdown)
     - **Applied Date**: When application was submitted
     - **Documents**: Links to resume and additional documents
     - **Actions**: View details, add note buttons
   - **Expected Result**: All applications are listed in the table

### Task 2: Filtering Applications by Status

This task covers filtering the applications list to focus on specific statuses.

1. **Access the filter dropdown**
   - Click the **Filter by Status** button in the top-right corner
   - **Expected Result**: Dropdown menu appears with status options

2. **Select a status filter**
   - Choose from:
     - **All**: Show all applications (default)
     - **Pending Review**: Show only pending applications
     - **Shortlisted**: Show only shortlisted applications
     - **Interviewed**: Show only interviewed applications
     - **Accepted**: Show only accepted applications
     - **Rejected**: Show only rejected applications
   - **Expected Result**: Selected filter is highlighted

3. **View filtered results**
   - Table updates to show only applications matching the selected status
   - URL updates with status parameter
   - **Expected Result**: Only applications with the selected status are displayed

4. **Clear filter**
   - Click **All** in the filter dropdown
   - **Expected Result**: All applications are displayed again

### Task 3: Updating Application Status

This task covers changing the status of applications.

1. **Locate the status dropdown**
   - In the applications table, find the **Status** column
   - Each row has a dropdown showing the current status
   - **Expected Result**: Status dropdowns are visible for all applications

2. **Change application status**
   - Click on the status dropdown for an application
   - Select a new status from the options:
     - **Pending Review**: Initial status for new applications
     - **Shortlisted**: Candidate selected for further review
     - **Interviewed**: Candidate has been interviewed
     - **Accepted**: Candidate has been offered the position
     - **Rejected**: Application has been declined
   - **Expected Result**: Dropdown shows all available statuses

3. **Confirm status change**
   - Status is automatically saved when you select a new option
   - **Expected Result**: Success message appears: "Status updated successfully"

4. **Verify status update**
   - The dropdown reflects the new status
   - Statistics cards update to reflect the change
   - **Expected Result**: Status change is saved and visible

**Status Workflow Best Practices:**
- **Pending Review** → **Shortlisted**: After initial resume review
- **Shortlisted** → **Interviewed**: After scheduling/conducting interview
- **Interviewed** → **Accepted**: After deciding to hire
- **Interviewed** → **Rejected**: After deciding not to proceed
- **Any Status** → **Rejected**: Can reject at any stage

### Task 4: Viewing Applicant Details

This task covers accessing detailed information about an applicant.

1. **Click the View Details button**
   - In the **Actions** column, click the eye icon button
   - **Expected Result**: Application details modal opens

2. **Review applicant header information**
   - View applicant's profile photo (if available)
   - See full name and email address
   - View phone number (if provided)
   - See application date ("Applied X days ago")
   - See last updated timestamp
   - **Expected Result**: Applicant contact information is displayed

3. **Review application status**
   - Status dropdown appears at the top of the modal
   - Can change status directly from the modal
   - **Expected Result**: Current status is visible and editable

4. **Read cover letter**
   - If applicant submitted a cover letter, it appears in a dedicated section
   - Full text is displayed with proper formatting
   - **Expected Result**: Cover letter content is readable

5. **View documents section**
   - **Resume**: Always present for all applications
     - Shows document icon and filename
     - **Download** button to view/download the file
   - **Additional Documents**: If applicant uploaded extra files
     - Shows document icon and filename
     - **Download** button to view/download the file
   - **Expected Result**: All submitted documents are accessible

6. **Review notes section**
   - View any internal notes added by HR/admin staff
   - Notes show timestamp and author
   - If no notes exist, message displays: "No notes added yet"
   - **Expected Result**: Internal notes are visible

7. **Close the modal**
   - Click the X button or click outside the modal
   - **Expected Result**: Modal closes and returns to applications list

### Task 5: Downloading Applicant Documents

This task covers accessing and downloading applicant-submitted files.

1. **Download from applications table**
   - In the **Documents** column, click the document icon button
   - **Resume icon**: Downloads the applicant's resume
   - **Archive icon**: Downloads additional documents (if available)
   - **Expected Result**: File opens in a new browser tab or downloads

2. **Download from details modal**
   - Open the application details modal
   - In the **Documents** section, click **Download** button on any document
   - **Expected Result**: File opens in a new browser tab or downloads

3. **View document in browser**
   - PDF files typically open in the browser
   - Other formats (DOC, DOCX) may download directly
   - **Expected Result**: Document is accessible for review

**Supported Document Formats:**
- PDF (.pdf) - Recommended format
- Microsoft Word (.doc, .docx)
- Other formats as configured in job posting requirements

### Task 6: Sending Emails to Applicants

This task covers communicating with applicants via email.

1. **Open the email modal**
   - Open the application details modal
   - Next to the applicant's email, click **Send Email**
   - **Expected Result**: Email composition modal opens

2. **Review pre-filled information**
   - **To**: Applicant's email address (read-only)
   - **Subject**: Pre-filled with "Re: Application for [Job Title]"
   - **Message**: Empty text area for your message
   - **Expected Result**: Email form is ready for composition

3. **Compose your email**
   - Edit the subject line if needed
   - Type your message in the message text area
   - Use professional, clear language
   - **Expected Result**: Email content is entered

4. **Send the email**
   - Click **Send Email** button
   - **Expected Result**: Loading indicator appears

5. **Confirm email sent**
   - Success message appears: "Email sent successfully!"
   - Modal closes automatically
   - **Expected Result**: Email is delivered to applicant

6. **Verify email in notes**
   - Email is automatically logged in the application notes
   - Note includes:
     - Timestamp
     - Sender name
     - Email subject
     - Email message content
   - **Expected Result**: Email record is saved in notes

**Email Use Cases:**
- Request additional information or documents
- Schedule interview appointments
- Send rejection notifications
- Provide application status updates
- Request clarification on qualifications
- Send job offer letters

### Task 7: Adding Notes to Applications

This task covers adding internal notes for tracking and collaboration.

1. **Open the add note interface**
   - From the applications table, click the comment icon in the **Actions** column
   - Or from the application details modal, click **Add Note**
   - **Expected Result**: Add note modal opens

2. **Enter your note**
   - Type your note in the text area
   - Notes can include:
     - Interview feedback
     - Screening results
     - Follow-up reminders
     - Internal recommendations
     - Any relevant observations
   - **Expected Result**: Note text is entered

3. **Save the note**
   - Click **Save Note** button
   - **Expected Result**: Note is saved

4. **Verify note added**
   - Success message may appear
   - If viewing application details, modal refreshes to show new note
   - Note includes timestamp and author name
   - **Expected Result**: Note appears in the notes section

5. **View note history**
   - All notes are displayed in chronological order (newest first)
   - Each note shows:
     - Date and time
     - Author name
     - Note content
   - **Expected Result**: Complete note history is visible

**Note Best Practices:**
- Be professional and objective
- Include specific details (dates, scores, observations)
- Use notes for internal communication only
- Document important decisions and rationale
- Add notes after interviews or phone screens
- Use consistent formatting for easy scanning

### Task 8: Exporting Applicant Data

This task covers exporting application data to Excel for analysis or record-keeping.

1. **Access the export function**
   - From the applications management page, look for an **Export** button
   - Or navigate to the job detail page and find export options
   - **Expected Result**: Export option is available

2. **Initiate export**
   - Click the **Export** or **Export to Excel** button
   - **Expected Result**: Export process begins

3. **Download the Excel file**
   - File downloads automatically
   - Filename format: `Applicants-[job-slug]-[date].xlsx`
   - Example: `Applicants-software-engineer-acme-corp-20251119.xlsx`
   - **Expected Result**: Excel file is downloaded to your computer

4. **Review exported data**
   - Open the Excel file
   - Spreadsheet includes columns:
     - **ID**: Application ID
     - **Name**: Applicant full name
     - **Email**: Applicant email address
     - **Application Date**: When they applied
     - **Status**: Current application status
     - **Phone**: Phone number (if available)
     - **Location**: Applicant location (if available)
     - **Skills**: Comma-separated list of skills
     - **Experience**: Years of experience (if available)
     - **Notes**: Internal notes
   - **Expected Result**: All applicant data is organized in spreadsheet format

5. **Use exported data**
   - Sort and filter applicants
   - Share with hiring managers
   - Create reports and analytics
   - Archive for record-keeping
   - Import into other systems
   - **Expected Result**: Data is usable for various purposes

**Export Use Cases:**
- Share applicant list with hiring committee
- Create hiring reports for management
- Archive applications for compliance
- Analyze applicant demographics
- Track hiring metrics over time

### Task 9: Managing Large Numbers of Applications

This task covers working efficiently with many applications.

1. **Use pagination**
   - If more than 20 applications exist, pagination controls appear
   - Click page numbers to navigate
   - Use **Previous** and **Next** buttons
   - **Expected Result**: Navigate through multiple pages of applications

2. **Filter by status**
   - Use status filter to focus on specific application stages
   - Example: Filter to "Pending Review" to process new applications
   - **Expected Result**: Reduced list makes review more manageable

3. **Bulk status updates (via Django Admin)**
   - For bulk operations, use Django admin interface
   - Navigate to `/admin/jobs/jobapplication/`
   - Select multiple applications
   - Use bulk actions to update statuses
   - **Expected Result**: Multiple applications updated at once

4. **Prioritize review**
   - Sort by application date (newest first by default)
   - Review pending applications first
   - Move through statuses systematically
   - **Expected Result**: Efficient application processing workflow

### Task 10: Application Review Workflow

This task covers a recommended workflow for processing applications.

1. **Initial screening (Pending → Shortlisted/Rejected)**
   - Filter to show **Pending Review** applications
   - For each application:
     - Click **View Details** to open modal
     - Review cover letter
     - Download and review resume
     - Check qualifications against job requirements
     - Add screening notes
     - Update status to **Shortlisted** or **Rejected**
   - **Expected Result**: All pending applications are screened

2. **Schedule interviews (Shortlisted → Interviewed)**
   - Filter to show **Shortlisted** applications
   - For each shortlisted candidate:
     - Click **Send Email** to schedule interview
     - Add note with interview date/time
     - After interview is conducted, update status to **Interviewed**
   - **Expected Result**: Interviews are scheduled and tracked

3. **Make hiring decisions (Interviewed → Accepted/Rejected)**
   - Filter to show **Interviewed** applications
   - For each interviewed candidate:
     - Review interview notes
     - Make hiring decision
     - Update status to **Accepted** or **Rejected**
     - Send email with decision
   - **Expected Result**: Hiring decisions are documented

4. **Follow up with accepted candidates**
   - Filter to show **Accepted** applications
   - Send offer letters via email
   - Add notes tracking offer acceptance
   - **Expected Result**: Offer process is managed

5. **Communicate with rejected candidates**
   - Filter to show **Rejected** applications
   - Send professional rejection emails
   - Thank them for their interest
   - **Expected Result**: All candidates receive closure

## Tips and Best Practices

- **Timely Review**: Review applications within 24-48 hours of submission
- **Consistent Criteria**: Use the same evaluation criteria for all applicants
- **Detailed Notes**: Document your reasoning for status changes
- **Professional Communication**: Always be courteous and professional in emails
- **Privacy**: Treat applicant information confidentially
- **Status Updates**: Keep applicants informed of their status
- **Document Everything**: Add notes for all significant interactions
- **Regular Exports**: Export data regularly for backup and reporting
- **Team Collaboration**: Use notes to communicate with other reviewers
- **Fair Process**: Ensure all applicants receive equal consideration

## Common Use Cases

### Use Case 1: High-Volume Screening
For positions with many applications, use filters and notes to efficiently screen candidates. Export data to share with hiring team for collaborative review.

### Use Case 2: Interview Scheduling
Use the email feature to schedule interviews directly from the application. Add notes with interview details for easy reference.

### Use Case 3: Hiring Committee Review
Export applicant data to Excel and share with hiring committee. Use notes to document committee feedback and decisions.

### Use Case 4: Compliance Documentation
Maintain detailed notes throughout the hiring process for compliance and audit purposes. Export data for record-keeping.

### Use Case 5: Candidate Pipeline Management
Use status updates to track candidates through the hiring pipeline. Monitor statistics to identify bottlenecks in the process.

## Troubleshooting

### Issue: Cannot View Application Details
**Symptoms**: View details button doesn't work or modal doesn't open
**Solution**: 
- Verify you have admin or HR permissions
- Check that JavaScript is enabled in your browser
- Try refreshing the page
- Clear browser cache
- Check browser console for errors

### Issue: Status Update Not Saving
**Symptoms**: Status dropdown changes but doesn't save
**Solution**: 
- Check your internet connection
- Verify you're still logged in
- Try refreshing the page
- Check for error messages in browser console
- Contact system administrator if issue persists

### Issue: Cannot Download Documents
**Symptoms**: Document download links don't work
**Solution**: 
- Check that documents were actually uploaded by applicant
- Verify file still exists on server
- Try right-clicking and "Save link as"
- Check browser's download settings
- Contact system administrator if files are missing

### Issue: Email Not Sending
**Symptoms**: Email form submits but email doesn't send
**Solution**: 
- Verify email configuration is set up correctly
- Check that applicant email address is valid
- Review email logs for errors
- Ensure email service (SMTP/Brevo/SendGrid) is configured
- Contact system administrator to check email settings

### Issue: Export Not Working
**Symptoms**: Export button doesn't generate file
**Solution**: 
- Check that you have permission to export data
- Verify there are applications to export
- Try exporting a smaller dataset
- Check browser's download settings
- Clear browser cache and try again

### Issue: Notes Not Appearing
**Symptoms**: Added notes don't show up
**Solution**: 
- Refresh the application details modal
- Check that note was actually saved (look for success message)
- Verify you're viewing the correct application
- Try adding the note again
- Contact system administrator if notes are lost

### Issue: Pagination Not Working
**Symptoms**: Cannot navigate to other pages of applications
**Solution**: 
- Check that there are actually multiple pages of applications
- Try clicking different page numbers
- Clear browser cache
- Check for JavaScript errors in browser console
- Refresh the page

## Related Features

- [Creating Job Postings](creating-job-postings.md) - How to create new job postings
- [Managing Job Postings](managing-job-postings.md) - Edit and manage existing job postings
- [Job Board (User View)](../../user-features/jobs/job-applications.md) - How alumni view and apply for jobs

## Additional Notes

- Application data is stored securely and treated confidentially
- All status changes are logged with timestamps
- Email communications are logged in application notes
- Exported Excel files include all available applicant data
- Applications are displayed in reverse chronological order (newest first)
- The system supports pagination for jobs with many applications (20 per page)
- Status changes are saved immediately without requiring a form submission
- Notes are prepended (newest first) for easy access to recent information
- Document downloads open in new tabs to preserve your place in the application list
- Application details modal can be closed by clicking outside or pressing Escape key
- Statistics cards update in real-time when status changes are made
- Filter selections persist in the URL for easy bookmarking and sharing

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the main Jobs documentation.

*Last Updated: November 19, 2025*
