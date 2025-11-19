# Managing Surveys

## Overview

The survey management feature allows administrators to view, edit, delete, and manage the status of surveys. You can monitor survey performance, update survey details, and control survey availability.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with survey management permissions

## Prerequisites

- Admin account with appropriate permissions
- Access to the admin panel
- At least one survey created in the system

## How to Access

1. Log in to your admin account
2. Navigate to the admin panel
3. Click on "Surveys" in the navigation menu
4. You'll see the survey list page

## Survey List Overview

The survey list page displays all surveys in the system with the following information:

- **Title**: Survey name
- **Status**: Current status (Draft, Active, Closed)
- **Start Date**: When survey becomes available
- **End Date**: When survey closes
- **Responses**: Number of responses received
- **Response Rate**: Percentage of alumni who responded
- **Actions**: Quick action buttons

### Dashboard Statistics

At the top of the survey list, you'll see:
- **Total Alumni**: Number of registered alumni
- **Alumni with Responses**: Alumni who have completed at least one survey
- **Participation Percentage**: Overall survey participation rate
- **Active Surveys**: Number of currently active surveys

### Filtering and Sorting

- Surveys are displayed in reverse chronological order (newest first)
- Use the search box to find specific surveys
- Filter by status using the status dropdown

## Step-by-Step Guide

### Viewing Survey Details

#### Step 1: Access Survey Details

1. From the survey list, click on a survey title or the "View" button
2. The survey detail page will open

**Expected Result:** You'll see complete survey information including all questions

#### Step 2: Review Survey Information

The survey detail page shows:
- Survey title and description
- Status and dates
- All questions with their settings
- Question options (for multiple choice questions)
- Response count
- Quick action buttons

**Expected Result:** You can review all survey configuration details

### Editing a Survey

#### Step 1: Access Edit Form

1. From the survey list, click the "Edit" button next to the survey
2. Or from the survey detail page, click "Edit Survey"

**Expected Result:** The survey edit form opens with current values

#### Step 2: Make Changes

You can update:
- **Title**: Change the survey name
- **Description**: Update the survey description
- **Start Date**: Modify when survey becomes available
- **End Date**: Extend or shorten survey duration
- **Status**: Change between Draft, Active, and Closed
- **External URL**: Update link (for external surveys)

**Important Notes:**
- Be cautious when editing active surveys with responses
- Changing question types may affect existing responses
- Consider creating a new survey for major changes

#### Step 3: Save Changes

1. Review your modifications
2. Click "Save Changes" or "Update Survey"

**Expected Result:** Survey is updated with new information

### Managing Survey Status

#### Activating a Draft Survey

1. Locate the draft survey in the list
2. Click "Edit" button
3. Change status from "Draft" to "Active"
4. Verify start and end dates are correct
5. Click "Save Changes"

**Expected Result:** Survey becomes visible to alumni and starts accepting responses

#### Closing an Active Survey

1. Locate the active survey in the list
2. Click "Edit" button
3. Change status from "Active" to "Closed"
4. Click "Save Changes"

**Expected Result:** Survey stops accepting new responses but remains visible

**Alternative Method:**
- Surveys automatically close when the end date is reached
- No manual action needed if end date is set correctly

#### Reopening a Closed Survey

**Note:** It's generally not recommended to reopen closed surveys as it can affect data integrity.

**If you must reopen:**
1. Edit the survey
2. Extend the end date to a future date
3. Change status to "Active"
4. Click "Save Changes"

**Better Alternative:**
- Create a new survey with similar questions
- Reference the previous survey in the description
- This maintains data integrity and clear versioning

### Editing Survey Questions

#### Adding New Questions to Existing Survey

1. Go to survey detail page
2. Click "Add Question" button
3. Fill in question details:
   - Question text
   - Question type
   - Required setting
   - Help text
   - Display order
4. Add options (if applicable)
5. Click "Save Question"

**Expected Result:** New question is added to the survey

**Warning:** Adding questions to active surveys may confuse respondents who already started

#### Editing Existing Questions

1. From survey detail page, click "Edit" next to a question
2. Modify question details
3. Update options if needed
4. Click "Save Changes"

**Expected Result:** Question is updated

**Important:** Editing questions with existing responses may affect data analysis

#### Deleting Questions

1. From survey detail page, click "Delete" next to a question
2. Confirm deletion in the popup

**Expected Result:** Question is removed from survey

**Warning:** Deleting questions will also delete all responses to that question

### Deleting a Survey

#### Step 1: Access Delete Function

1. From the survey list, click the "Delete" button next to the survey
2. Or from the survey detail page, click "Delete Survey"

**Expected Result:** A confirmation dialog appears

#### Step 2: Confirm Deletion

1. Review the warning message
2. Understand that deletion is permanent
3. Note the number of responses that will be deleted
4. Click "Confirm Delete" if you're sure

**Expected Result:** Survey and all associated responses are permanently deleted

**Warning:** This action cannot be undone. All survey data will be lost.

**Best Practice:** Instead of deleting, consider:
- Changing status to "Closed"
- Archiving survey data before deletion
- Exporting responses before deletion

### Monitoring Survey Performance

#### Viewing Response Statistics

From the survey list page, you can see:
- **Response Count**: Total number of responses
- **Response Rate**: Percentage of alumni who responded
- **Completion Rate**: Percentage who completed vs. started

#### Accessing Detailed Analytics

1. Click on a survey to view details
2. Click "View Responses" button
3. See detailed response analytics

**Expected Result:** You'll see response data and statistics (covered in detail in [Viewing Survey Responses](viewing-responses.md))

## Survey Status Workflow

### Recommended Status Flow

```
Draft → Active → Closed
```

1. **Draft**: Create and test survey
   - Build questions
   - Review and edit
   - Test with colleagues
   - Get approval

2. **Active**: Launch survey
   - Announce to alumni
   - Monitor responses
   - Provide support
   - Send reminders

3. **Closed**: End survey
   - Stop accepting responses
   - Analyze data
   - Generate reports
   - Share findings

### Status Transition Rules

- **Draft to Active**: Anytime before start date
- **Active to Closed**: Anytime, or automatically at end date
- **Closed to Active**: Not recommended (create new survey instead)
- **Active to Draft**: Not allowed if responses exist

## Tips and Best Practices

### Survey Management

1. **Use descriptive titles**: Include year or purpose
   - Good: "2024 Alumni Career Development Survey"
   - Bad: "Survey 1"

2. **Set realistic end dates**: Allow adequate time
   - Minimum 1-2 weeks for simple surveys
   - 3-4 weeks for comprehensive surveys
   - Consider holidays and busy periods

3. **Monitor response rates**: Check regularly
   - Send reminders if rates are low
   - Extend deadline if needed
   - Identify and address barriers

4. **Communicate clearly**: Keep alumni informed
   - Announce survey launch
   - Explain purpose and importance
   - Share how data will be used
   - Thank participants

### Editing Active Surveys

1. **Minimize changes**: Avoid editing active surveys
   - Plan thoroughly before activation
   - Test in draft mode
   - Get stakeholder approval

2. **If you must edit**:
   - Make changes early in survey period
   - Notify participants of changes
   - Document what changed and when
   - Consider data analysis implications

3. **Never change**:
   - Question types (affects data integrity)
   - Option values (affects existing responses)
   - Required settings (may invalidate responses)

### Data Preservation

1. **Export before major changes**: Save response data
   - Export to CSV or PDF
   - Store in secure location
   - Document export date and version

2. **Archive old surveys**: Don't delete unnecessarily
   - Close instead of delete
   - Keep for historical reference
   - Maintain data for trend analysis

3. **Version control**: For recurring surveys
   - Use year in title (e.g., "2024 Alumni Survey")
   - Keep previous versions closed
   - Compare results across years

## Common Tasks

### Extending Survey Deadline

1. Edit the survey
2. Change end date to new date
3. Ensure status is "Active"
4. Save changes
5. Notify alumni of extension

### Pausing a Survey Temporarily

1. Edit the survey
2. Change status to "Draft"
3. Save changes
4. Survey becomes invisible to alumni
5. To resume: Change status back to "Active"

### Duplicating a Survey

**Note:** System doesn't have built-in duplication feature

**Manual Process:**
1. Create new survey with similar title
2. Copy description and settings
3. Recreate questions manually
4. Review and test
5. Activate when ready

**Tip:** Keep a template document with standard questions for recurring surveys

### Bulk Operations

**Note:** System doesn't support bulk operations

**Workaround:**
- Manage surveys individually
- Use consistent naming for easy filtering
- Export data regularly for batch analysis

## Troubleshooting

### Issue: Cannot edit survey

**Possible Causes:**
- Insufficient permissions
- Survey is locked
- Browser cache issue

**Solution:**
- Verify you have admin privileges
- Try refreshing the page
- Clear browser cache
- Try different browser

### Issue: Changes not saving

**Possible Causes:**
- Network connection issue
- Validation errors
- Session timeout

**Solution:**
- Check internet connection
- Look for error messages
- Verify all required fields
- Log out and log back in

### Issue: Survey not appearing in list

**Possible Causes:**
- Filters are applied
- Search term doesn't match
- Survey was deleted

**Solution:**
- Clear all filters
- Clear search box
- Check with other admins
- Review audit logs if available

### Issue: Response count seems incorrect

**Possible Causes:**
- Incomplete responses not counted
- Cache not updated
- Duplicate submissions

**Solution:**
- Refresh the page
- View detailed responses
- Check for duplicate entries
- Verify response criteria

### Issue: Cannot delete survey

**Possible Causes:**
- Insufficient permissions
- Survey has dependencies
- System protection

**Solution:**
- Verify admin privileges
- Check for related data
- Close survey instead
- Contact system administrator

## Related Features

- [Creating Surveys](creating-surveys.md) - How to create new surveys
- [Viewing Survey Responses](viewing-responses.md) - Analyze survey data
- [Survey Analytics](../analytics/README.md) - View participation statistics
- [User Management](../users/README.md) - Manage admin permissions

## Need Help?

If you encounter issues not covered in this guide:
- Contact the system administrator
- Check the FAQ section
- Submit a support ticket through the feedback form
- Review system documentation
