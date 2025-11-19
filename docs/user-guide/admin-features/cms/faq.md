# Faq

## Overview

FAQ (Frequently Asked Questions) Management allows you to create, organize, and maintain a collection of common questions and answers that are displayed on the Contact or Help pages. This feature helps reduce support inquiries by providing self-service information to users.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions
- Support staff
- Content managers

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system
- Access to CMS Dashboard
- List of common questions from users

## How to Access

### Method 1: Through CMS Dashboard
1. Navigate to CMS Dashboard (`/cms/dashboard/`)
2. Click on "FAQs" or "Manage FAQs"
3. You will see the list of all FAQ entries

### Method 2: Direct URL
- Navigate to `/cms/faqs/`

## Key Features

### 1. View All FAQs
- List view of all FAQ entries
- Sort by order or question
- Filter by active status
- Pagination for large lists
- Quick preview of questions

### 2. Add New FAQs
- Create new question-answer pairs
- Set display order
- Organize by topic
- Activate or deactivate

### 3. Edit FAQs
- Update questions
- Revise answers
- Adjust display order
- Toggle active status

### 4. Delete FAQs
- Remove outdated FAQs
- Confirmation required
- Permanent action

### 5. FAQ Ordering
- Control display sequence
- Group related questions
- Prioritize important questions

## Step-by-Step Guide

### Task 1: View FAQs List

1. Access FAQs from CMS Dashboard
2. View the list of all FAQ entries
3. Observe the following information:
   - Question (truncated if long)
   - Display order
   - Active status
   - Creation date
4. Use pagination to navigate through multiple pages
5. Click on questions to view full details and answers

**Expected Result**: Complete list of all FAQ entries with preview of questions.

### Task 2: Create a New FAQ

1. From the FAQs list, click "Add FAQ" or "Create New"
2. Fill in the FAQ details:

   **Question** (required):
   - Enter the question exactly as users would ask it
   - Maximum 500 characters
   - Use clear, simple language
   - Start with question words (How, What, When, Where, Why, Can, etc.)
   - Examples:
     - "How do I register for an alumni account?"
     - "What are the membership benefits?"
     - "Can I update my profile information?"
   
   **Answer** (required):
   - Provide a clear, comprehensive answer
   - Use simple language
   - Break into paragraphs for readability
   - Include step-by-step instructions if applicable
   - Add links to relevant pages if needed
   - Be specific and actionable
   - Anticipate follow-up questions
   
   **Order**:
   - Enter a number for display order
   - Lower numbers appear first
   - Default: 0
   - Group related questions with similar order numbers
   - Use increments of 10 (10, 20, 30...)
   
   **Is Active**:
   - Check to make FAQ visible
   - Uncheck to hide without deleting

3. Review question and answer for clarity
4. Click "Save" or "Create FAQ"

**Expected Result**: New FAQ is created and appears on the FAQ page.

### Task 3: Edit an Existing FAQ

1. From the FAQs list, find the FAQ to edit
2. Click the "Edit" button or question text
3. Update any of the following fields:
   - Question (improve clarity or wording)
   - Answer (add details, update information)
   - Order (reorganize FAQs)
   - Active status
4. Make necessary changes
5. Click "Save" or "Update FAQ"

**Expected Result**: FAQ is updated with new information. Changes appear on the FAQ page.

### Task 4: Organize FAQs by Topic

**Example Organization Structure**:

**Account & Registration (Order 10-29)**
- 10: How do I register?
- 11: What information do I need to register?
- 12: How do I verify my email?
- 13: I didn't receive the verification email. What should I do?
- 20: How do I reset my password?
- 21: Can I change my email address?

**Profile Management (Order 30-49)**
- 30: How do I update my profile?
- 31: How do I add my work experience?
- 32: Can I upload documents?
- 33: How do I change my profile photo?

**Features & Usage (Order 50-69)**
- 50: How do I connect with other alumni?
- 51: How do I send messages?
- 52: How do I join alumni groups?
- 53: How do I apply for jobs?

**Technical Issues (Order 70-89)**
- 70: I can't log in. What should I do?
- 71: The website is not loading properly
- 72: How do I report a bug?

**Steps to Organize**:
1. List all your FAQs
2. Group them by topic or category
3. Assign order ranges to each category
4. Edit each FAQ and update the order field
5. Save all changes
6. Review FAQ page to verify organization

**Expected Result**: FAQs are organized by topic, making it easier for users to find answers.

### Task 5: Update FAQ Based on User Feedback

1. Monitor user inquiries and support tickets
2. Identify questions that are frequently asked
3. Check if FAQ already exists:
   - If yes, edit to improve clarity
   - If no, create new FAQ
4. For existing FAQ:
   - Click "Edit"
   - Revise answer to address common confusion
   - Add examples or clarifications
   - Save changes
5. For new FAQ:
   - Click "Create New"
   - Enter question as users ask it
   - Provide comprehensive answer
   - Set appropriate order
   - Save

**Expected Result**: FAQ section stays current and addresses actual user needs.

### Task 6: Deactivate an FAQ

1. From the FAQs list, find the FAQ
2. Click "Edit" on the FAQ
3. Uncheck the "Is Active" checkbox
4. Click "Save"

**Use Cases**:
- Temporarily outdated information
- Seasonal questions (only relevant at certain times)
- Testing new FAQ before making public
- Feature temporarily unavailable

**Expected Result**: FAQ no longer appears on the FAQ page but remains in admin list for future reactivation.

### Task 7: Delete an FAQ

1. From the FAQs list, find the FAQ to delete
2. Click the "Delete" button
3. Review the confirmation page:
   - Question and answer are displayed
   - Warning about permanent deletion
4. Confirm you want to delete
5. Click "Yes, delete" or "Confirm deletion"

**Use Cases**:
- Permanently outdated information
- Duplicate FAQs
- Incorrect information that's been replaced

**Expected Result**: FAQ is permanently removed from the system.

## Writing Effective FAQs

### Question Guidelines

**Do:**
- Use natural language as users would ask
- Start with question words (How, What, When, etc.)
- Be specific and focused
- Keep questions concise
- Use active voice

**Don't:**
- Use technical jargon
- Make questions too broad
- Combine multiple questions
- Use ambiguous language

**Examples:**

Good:
- "How do I reset my password?"
- "What documents can I upload to my profile?"
- "Can I delete my account?"

Poor:
- "Password issues" (not a question)
- "How do I do everything with my account?" (too broad)
- "What about passwords and security and stuff?" (unclear)

### Answer Guidelines

**Do:**
- Provide complete, actionable answers
- Use numbered steps for procedures
- Include specific examples
- Link to relevant pages or resources
- Anticipate follow-up questions
- Use simple, clear language
- Break into paragraphs for readability

**Don't:**
- Assume prior knowledge
- Use technical jargon without explanation
- Provide vague or incomplete answers
- Make answers too long (split into multiple FAQs if needed)
- Forget to update when features change

**Answer Structure:**

1. **Direct Answer**: Start with a direct answer to the question
2. **Details**: Provide additional context or explanation
3. **Steps**: If applicable, provide step-by-step instructions
4. **Examples**: Include examples when helpful
5. **Related Info**: Link to related FAQs or pages
6. **Contact**: Offer support contact if answer doesn't help

**Example:**

Question: "How do I reset my password?"

Answer:
```
You can reset your password from the login page.

To reset your password:
1. Go to the login page
2. Click "Forgot Password?" below the login form
3. Enter your registered email address
4. Click "Send Reset Link"
5. Check your email for the password reset link
6. Click the link and enter your new password
7. Confirm your new password and save

The reset link expires after 24 hours. If you don't receive the email within 5 minutes, check your spam folder or request a new link.

If you continue to have issues, contact support at alumni@norsu.edu.ph.
```

## Tips and Best Practices

1. **User-Centric**: Write from the user's perspective
2. **Regular Updates**: Review and update FAQs monthly
3. **Analytics**: Track which FAQs are most viewed
4. **Feedback Loop**: Use support tickets to identify new FAQs
5. **Clarity**: Test FAQs with actual users for clarity
6. **Completeness**: Ensure answers fully address the question
7. **Organization**: Group related questions together
8. **Prioritization**: Put most common questions first
9. **Maintenance**: Remove outdated FAQs promptly
10. **Links**: Keep links in answers up to date

## Common FAQ Categories

Consider organizing your FAQs into these categories:

1. **Account & Registration**
   - Creating accounts
   - Email verification
   - Login issues
   - Password management

2. **Profile Management**
   - Updating information
   - Adding education/experience
   - Uploading documents
   - Privacy settings

3. **Features & Usage**
   - Using specific features
   - Navigation help
   - Feature availability
   - Best practices

4. **Technical Support**
   - Login problems
   - Browser issues
   - Error messages
   - Performance issues

5. **Privacy & Security**
   - Data protection
   - Account security
   - Privacy settings
   - Data deletion

6. **Membership & Benefits**
   - Membership types
   - Benefits
   - Fees (if applicable)
   - Eligibility

## Important Notes

- **Order Conflicts**: Multiple FAQs can have the same order value
- **Character Limits**: Questions limited to 500 characters
- **HTML Support**: Answers may support HTML formatting (check with admin)
- **Deletion**: Deleting an FAQ is permanent and cannot be undone
- **Search**: Users may search FAQs, so use keywords they would use

## Troubleshooting

### FAQ Not Appearing

**Issue**: Created or edited FAQ doesn't show on FAQ page

**Solutions**:
- Verify "Is Active" checkbox is checked
- Clear browser cache and refresh
- Check display order
- Verify FAQ page template is working
- Wait a few moments for cache to clear

### FAQs Out of Order

**Issue**: FAQs don't display in expected sequence

**Solutions**:
- Review order values for all FAQs
- Ensure logical ordering
- Use consistent increments (10, 20, 30)
- Check if multiple FAQs have same order value
- Verify template respects order field

### Answer Formatting Issues

**Issue**: Answer text doesn't display correctly

**Solutions**:
- Check for special characters that need escaping
- Verify HTML tags are properly closed (if HTML allowed)
- Use plain text if formatting causes issues
- Break long paragraphs into shorter ones
- Test with simple text first

### Cannot Save FAQ

**Issue**: Save button doesn't work or shows errors

**Solutions**:
- Check for validation errors (red text near fields)
- Ensure required fields are filled (Question, Answer)
- Verify question doesn't exceed 500 characters
- Try refreshing the page and re-entering data
- Contact system administrator if issue persists

### Duplicate FAQs

**Issue**: Multiple FAQs with similar questions

**Solutions**:
- Review all FAQs for duplicates
- Merge similar questions into one comprehensive FAQ
- Delete duplicate entries
- Update remaining FAQ to cover all aspects
- Establish review process to prevent duplicates

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [Contact Information Management](contact-info.md) - Manage contact details
- [Site Configuration](site-configuration.md) - Manage global site settings

## Screenshots

> **Note**: Screenshots should be added showing:
> - FAQs list view with questions
> - Create new FAQ form
> - Question and answer fields
> - Edit FAQ form with existing content
> - Order field and organization
> - Active/inactive toggle
> - Delete confirmation page
> - FAQ display on website
> - Success messages after create/edit/delete
> - Organized FAQ categories on website
> - Mobile view of FAQs
