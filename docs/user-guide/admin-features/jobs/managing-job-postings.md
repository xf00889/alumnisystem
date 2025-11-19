# Managing Job Postings

## Overview

The job posting management feature allows administrators and HR staff to view, edit, delete, and manage the status of all job postings in the system. You can monitor application statistics, update job details, and control job visibility from a centralized dashboard.

## Who Can Use This Feature

- **User Role**: Admin users and HR staff only
- **Permissions Required**: Admin or HR group membership
- **Prerequisites**: 
  - Active admin or HR account
  - Access to job posting management area

## How to Access

1. Log in to your admin account
2. Navigate to the **Jobs** section from the admin menu
3. Click on **Manage Jobs** or access the jobs management dashboard

## Key Features

- View all job postings in a grid layout
- Monitor job statistics (active jobs, internal jobs, applications)
- Edit existing job postings
- Delete job postings
- Toggle job active/inactive status
- View application counts per job
- Quick access to job details and applications

## Step-by-Step Guide

### Task 1: Viewing the Jobs Management Dashboard

This task covers accessing and understanding the jobs management dashboard.

1. **Access the jobs management page**
   - From the admin menu, click **Jobs** → **Manage Jobs**
   - **Expected Result**: The jobs management dashboard appears

2. **Review the statistics section**
   - View **Active Jobs**: Number of currently visible job postings
   - View **Internal Jobs**: Number of NORSU internal positions
   - View **Total Applications**: All applications across all jobs
   - View **Pending Applications**: Applications awaiting review
   - **Expected Result**: Dashboard displays current job statistics

3. **Browse the jobs grid**
   - Each job card displays:
     - Job title and company name
     - Job type (Full Time, Part Time, etc.)
     - Posted date
     - Number of applications
     - Source type badge (Internal/External)
     - Active/Inactive status badge
   - **Expected Result**: All job postings are displayed in a grid layout

4. **Use pagination**
   - If more than 10 jobs exist, use pagination controls at the bottom
   - Click page numbers or use Previous/Next buttons
   - **Expected Result**: Navigate through multiple pages of job postings

### Task 2: Viewing Job Details

This task covers accessing detailed information about a specific job posting.

1. **Click on a job title**
   - From the jobs grid, click any job title
   - **Expected Result**: Job detail page opens

2. **Review job information**
   - View complete job description
   - See all requirements and qualifications
   - Check responsibilities
   - View skills required
   - See salary range and benefits
   - **Expected Result**: Full job details are displayed

3. **View application information**
   - Scroll to the applications section
   - See list of applicants (if any)
   - View application statuses
   - **Expected Result**: Application information is visible to admin/HR users

4. **Return to management dashboard**
   - Click the back button or navigate to **Manage Jobs**
   - **Expected Result**: Return to the jobs management dashboard

### Task 3: Editing Job Postings

This task covers modifying existing job postings.

1. **Access the edit form**
   - From the jobs grid, click the **Edit** button on a job card
   - **Expected Result**: Job editing form appears with current data pre-filled

2. **Update basic information**
   - Modify **Job Title** if needed
   - Update **Company Name**
   - Change **Location**
   - Adjust **Job Type** (Full Time, Part Time, etc.)
   - **Expected Result**: Basic fields are updated

3. **Edit job description and details**
   - Update the **Job Description** text
   - Modify **Requirements** section
   - Edit **Responsibilities**
   - Update **Skills Required** (comma-separated)
   - Change **Education Requirements**
   - **Expected Result**: Job content is updated

4. **Update compensation and benefits**
   - Modify **Salary Range**
   - Update **Benefits** information
   - **Expected Result**: Compensation details are updated

5. **Adjust job settings**
   - Change **Experience Level** (Entry, Mid, Senior, Executive)
   - Update **Category** (Technology, Finance, etc.)
   - Modify **Source Type** (Internal/External)
   - **Expected Result**: Job classification is updated

6. **Update visibility settings**
   - Check/uncheck **Is Featured** to control prominent display
   - Check/uncheck **Is Active** to show/hide the job
   - **Expected Result**: Job visibility settings are configured

7. **Modify document requirements (Internal jobs only)**
   - If source type is Internal, scroll to **Required Documents** section
   - Add new document requirements by clicking **Add Document Requirement**
   - Edit existing requirements:
     - Change document name
     - Update document type
     - Modify description
     - Toggle required/optional status
     - Adjust file type restrictions
     - Change max file size
   - Remove requirements by checking the **Delete** checkbox
   - **Expected Result**: Document requirements are updated

8. **Update external application link (External jobs)**
   - If source type is External, update the **Application Link** URL
   - Check/uncheck **Accepts Internal Applications** if needed
   - **Expected Result**: External application settings are updated

9. **Save changes**
   - Click **Save** or **Update Job Posting**
   - **Expected Result**: Job is updated and you're redirected to the job detail page
   - Success message appears: "Job posting updated successfully!"

10. **Verify changes**
    - Review the updated job details
    - Check that all modifications are reflected
    - **Expected Result**: All changes are saved and visible

### Task 4: Deleting Job Postings

This task covers removing job postings from the system.

1. **Locate the job to delete**
   - From the jobs management dashboard, find the job card
   - **Expected Result**: Job card is visible in the grid

2. **Click the Delete button**
   - On the job card, click the red **Delete** button
   - **Expected Result**: Confirmation dialog appears

3. **Review the confirmation dialog**
   - Dialog displays: "Delete Job Posting"
   - Shows the job title being deleted
   - Warning: "This action cannot be undone"
   - **Expected Result**: Confirmation dialog with job details

4. **Confirm deletion**
   - Click **Yes, delete it!** to proceed
   - Or click **Cancel** to abort
   - **Expected Result**: Loading indicator appears

5. **Wait for deletion to complete**
   - System processes the deletion request
   - **Expected Result**: Success message appears: "Deleted! The job posting has been deleted."

6. **Verify deletion**
   - Page automatically reloads
   - Deleted job no longer appears in the grid
   - Statistics are updated to reflect the deletion
   - **Expected Result**: Job is removed from the system

**Important Notes:**
- Deleting a job also deletes all associated applications
- This action cannot be undone
- Consider deactivating jobs instead of deleting them to preserve application history

### Task 5: Managing Job Status

This task covers activating and deactivating job postings.

1. **Identify job status**
   - Look at the status badge on each job card
   - Green badge with checkmark = Active
   - Gray badge with X = Inactive
   - **Expected Result**: Current status is visible

2. **Deactivate an active job**
   - Click **Edit** on an active job
   - Scroll to the **Is Active** checkbox
   - Uncheck the box
   - Click **Save**
   - **Expected Result**: Job is hidden from public job board but remains in admin view

3. **Activate an inactive job**
   - Click **Edit** on an inactive job
   - Scroll to the **Is Active** checkbox
   - Check the box
   - Click **Save**
   - **Expected Result**: Job becomes visible on public job board

4. **Verify status change**
   - Return to jobs management dashboard
   - Check the status badge on the job card
   - **Expected Result**: Badge reflects the new status

**Use Cases for Deactivating Jobs:**
- Position has been filled
- Temporarily pause applications
- Job posting needs major revisions
- Seasonal positions that are not currently open

### Task 6: Managing Featured Jobs

This task covers promoting jobs to featured status.

1. **Access job edit form**
   - Click **Edit** on the job you want to feature
   - **Expected Result**: Edit form opens

2. **Toggle featured status**
   - Scroll to the **Is Featured** checkbox
   - Check the box to make the job featured
   - Uncheck to remove featured status
   - **Expected Result**: Featured setting is changed

3. **Save changes**
   - Click **Save**
   - **Expected Result**: Job is updated

4. **Verify featured status**
   - Featured jobs appear at the top of the job board
   - Featured jobs are displayed prominently to users
   - **Expected Result**: Job appears in featured section if enabled

**Best Practices for Featured Jobs:**
- Limit to 3-5 most important positions
- Use for urgent or high-priority roles
- Rotate featured jobs regularly
- Feature jobs with competitive benefits

### Task 7: Viewing Application Statistics

This task covers monitoring applications for each job.

1. **View application count on job card**
   - Each job card shows: "X application(s)"
   - Number is clickable
   - **Expected Result**: Application count is visible

2. **Access applications list**
   - Click on the application count link
   - Or click **View** then navigate to applications
   - **Expected Result**: Applications management page opens for that job

3. **Review application statistics**
   - View breakdown by status:
     - Pending Review
     - Shortlisted
     - Interviewed
     - Accepted
   - **Expected Result**: Detailed application statistics are displayed

4. **Return to jobs management**
   - Use browser back button or navigate to **Manage Jobs**
   - **Expected Result**: Return to jobs dashboard

### Task 8: Bulk Job Management (Using Admin Interface)

For advanced bulk operations, use the Django admin interface.

1. **Access Django admin**
   - Navigate to `/admin/` in your browser
   - Log in with admin credentials
   - **Expected Result**: Django admin dashboard appears

2. **Navigate to Job Postings**
   - Click **Jobs** → **Job postings**
   - **Expected Result**: List of all job postings appears

3. **Select multiple jobs**
   - Check the boxes next to jobs you want to manage
   - **Expected Result**: Jobs are selected

4. **Apply bulk actions**
   - From the **Action** dropdown, select:
     - "Mark selected jobs as featured"
     - "Remove featured status from selected jobs"
     - "Activate selected jobs"
     - "Deactivate selected jobs"
   - Click **Go**
   - **Expected Result**: Action is applied to all selected jobs

5. **Confirm bulk action**
   - Review the confirmation message
   - **Expected Result**: Success message shows number of jobs updated

## Tips and Best Practices

- **Regular Maintenance**: Review and update job postings weekly to keep them current
- **Deactivate vs Delete**: Prefer deactivating filled positions to preserve application history
- **Featured Jobs**: Limit featured jobs to 3-5 high-priority positions for maximum impact
- **Application Monitoring**: Check pending applications daily to provide timely responses
- **Job Descriptions**: Keep descriptions concise and mobile-friendly
- **Status Updates**: Update job status promptly when positions are filled
- **Archive Strategy**: Deactivate old jobs rather than deleting them for record-keeping
- **Consistent Formatting**: Use consistent formatting across all job postings
- **Salary Transparency**: Include salary ranges when possible to attract more applicants
- **Skills Accuracy**: Keep skills lists accurate for better alumni matching

## Common Use Cases

### Use Case 1: Filled Position
When a position is filled, deactivate the job posting to hide it from the public board while preserving application records for future reference.

### Use Case 2: Seasonal Hiring
For seasonal positions, deactivate during off-season and reactivate when hiring resumes. Update dates and details before reactivating.

### Use Case 3: Job Corrections
If a job posting has errors, edit it immediately to correct information. Consider notifying applicants of significant changes.

### Use Case 4: Promoting Urgent Positions
Mark urgent or hard-to-fill positions as featured to increase visibility and attract more qualified candidates.

### Use Case 5: Bulk Status Updates
Use Django admin bulk actions to quickly activate multiple jobs at once (e.g., at the start of a hiring season).

## Troubleshooting

### Issue: Cannot Edit Job Posting
**Symptoms**: Edit button doesn't work or form doesn't load
**Solution**: 
- Verify you have admin or HR permissions
- Check that you're logged in
- Try refreshing the page
- Clear browser cache
- Contact system administrator if issue persists

### Issue: Changes Not Saving
**Symptoms**: Edit form submits but changes don't appear
**Solution**: 
- Ensure all required fields are filled
- Check for error messages at the top of the form
- For external jobs, provide either an application link or check "Accepts Internal Applications"
- Verify file size limits for document requirements are reasonable
- Try editing one section at a time

### Issue: Job Not Appearing After Activation
**Symptoms**: Job is marked active but doesn't show on job board
**Solution**: 
- Verify "Is Active" checkbox is checked
- Clear browser cache and refresh the job board
- Check that the job was saved successfully
- Ensure you're viewing the correct job type filter on the public board
- Wait a few minutes for cache to clear

### Issue: Cannot Delete Job
**Symptoms**: Delete button doesn't work or error occurs
**Solution**: 
- Ensure you have admin permissions
- Check your internet connection
- Try refreshing the page
- If job has many applications, deletion may take longer
- Contact system administrator if error persists

### Issue: Featured Jobs Not Displaying Prominently
**Symptoms**: Featured jobs don't appear at top of job board
**Solution**: 
- Verify "Is Featured" checkbox is checked
- Ensure job is also marked as active
- Clear browser cache
- Check that featured jobs section is enabled on the job board
- Limit featured jobs to 5 or fewer for best display

### Issue: Application Count Incorrect
**Symptoms**: Application count doesn't match actual applications
**Solution**: 
- Refresh the page
- Clear browser cache
- Check if applications were deleted
- Verify you're viewing the correct job
- Contact system administrator if discrepancy persists

### Issue: Bulk Actions Not Working (Admin Interface)
**Symptoms**: Bulk actions in Django admin don't apply
**Solution**: 
- Ensure jobs are selected (checkboxes checked)
- Verify action is selected from dropdown
- Click "Go" button after selecting action
- Check for error messages
- Refresh page and try again

## Related Features

- [Creating Job Postings](creating-job-postings.md) - How to create new job postings
- [Managing Applications](managing-applications.md) - Review and process job applications
- [Job Board (User View)](../../user-features/jobs/job-applications.md) - How alumni view and apply for jobs

## Additional Notes

- Job postings are displayed in reverse chronological order (newest first)
- The jobs grid uses responsive design and adapts to different screen sizes
- Statistics are calculated in real-time when the page loads
- Deleted jobs cannot be recovered - consider deactivating instead
- Job slugs are automatically generated from title and company name
- Editing a job preserves its original posted date
- Application counts include all statuses (pending, shortlisted, interviewed, accepted, rejected)
- Featured status can be toggled on/off without affecting other job settings
- The system prevents duplicate job slugs by adding numeric suffixes

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the main Jobs documentation.

*Last Updated: November 19, 2025*
