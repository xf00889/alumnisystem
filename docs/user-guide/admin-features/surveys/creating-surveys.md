# Creating Surveys

## Overview

The survey creation feature allows administrators to create custom surveys to gather feedback, conduct research, or collect data from alumni. You can create both internal surveys (hosted within the system) and external surveys (linking to platforms like Google Forms).

## Who Can Use This Feature

- Admin users with staff privileges
- Users with survey management permissions

## Prerequisites

- Admin account with appropriate permissions
- Access to the admin panel

## How to Access

1. Log in to your admin account
2. Navigate to the admin panel
3. Click on "Surveys" in the navigation menu
4. Click the "Create Survey" button

## Survey Types

### Internal Surveys

Internal surveys are created and hosted within the NORSU Alumni System. They offer:
- Full customization of questions and question types
- Built-in response collection and analysis
- Integrated reporting and data export
- Multiple question types (text, multiple choice, rating, etc.)

### External Surveys

External surveys link to third-party survey platforms like Google Forms, SurveyMonkey, or Typeform. They offer:
- Use of familiar external tools
- Advanced features from specialized survey platforms
- Simple integration via URL link
- Responses managed on the external platform

## Step-by-Step Guide

### Creating an Internal Survey

#### Step 1: Access Survey Creation Form

1. From the Surveys list page, click "Create Survey"
2. The survey creation form will open

**Expected Result:** You'll see a form with fields for survey details and question builder

#### Step 2: Enter Basic Survey Information

1. **Title**: Enter a clear, descriptive title for your survey
   - Example: "2024 Alumni Career Development Survey"
   
2. **Description**: Provide a detailed description of the survey's purpose
   - Explain what the survey is about
   - Mention how the data will be used
   - Include any incentives or benefits for participation

3. **Start Date**: Select when the survey should become available
   - Click the date/time picker
   - Choose the date and time
   
4. **End Date**: Select when the survey should close
   - Must be after the start date
   - Consider giving adequate time for responses (typically 2-4 weeks)

5. **Status**: Choose the initial status
   - **Draft**: Survey is not visible to users (recommended for new surveys)
   - **Active**: Survey is visible and accepting responses
   - **Closed**: Survey is visible but not accepting new responses

**Expected Result:** Basic survey information is filled in

#### Step 3: Add Survey Questions

1. Click "Add Question" button
2. For each question, provide:

   **Question Text**: Enter your question
   - Be clear and specific
   - Avoid leading or biased questions
   - Keep questions concise

   **Question Type**: Select from available types:
   - **Text Answer**: Open-ended text response
   - **Multiple Choice (Single Answer)**: Radio buttons for one selection
   - **Multiple Choice (Multiple Answers)**: Checkboxes for multiple selections
   - **Rating Scale**: Numeric rating (1-5 or 1-10)
   - **Likert Scale**: Agreement scale (Strongly Disagree to Strongly Agree)
   - **Date**: Date picker
   - **Time**: Time picker
   - **File Upload**: Allow file attachments
   - **Email**: Email address input with validation
   - **Number**: Numeric input
   - **Phone Number**: Phone number input
   - **Website URL**: URL input with validation

   **Required**: Check if the question must be answered
   - Use sparingly to avoid survey abandonment
   - Mark only essential questions as required

   **Help Text** (optional): Provide additional guidance
   - Clarify what you're asking for
   - Give examples if needed
   - Explain any specific format requirements

   **Display Order**: Set the question sequence
   - Questions are numbered automatically
   - You can reorder questions by changing this number

3. **For Multiple Choice Questions**: Add options
   - Click "Add Option" for each choice
   - Enter the option text
   - Set display order for options
   - You can add as many options as needed

4. **For Rating/Likert Questions**: Select scale type
   - **1-5**: Standard 5-point scale
   - **1-10**: Extended 10-point scale
   - **A-F**: Letter grade scale
   - **Frequency**: Never, Rarely, Sometimes, Often, Always
   - **Agreement**: Strongly Disagree to Strongly Agree
   - **Satisfaction**: Very Unsatisfied to Very Satisfied
   - **Custom Scale**: Define your own scale

5. Repeat for all questions you want to add

**Expected Result:** All survey questions are configured

#### Step 4: Review and Save

1. Review all survey details and questions
2. Check for:
   - Spelling and grammar errors
   - Clear and unbiased question wording
   - Logical question flow
   - Appropriate question types
   - Correct required field settings

3. Click "Save Survey" or "Create Survey"

**Expected Result:** Survey is created and appears in the survey list

### Creating an External Survey

#### Step 1: Create Your Survey on External Platform

1. Go to your preferred survey platform (e.g., Google Forms)
2. Create your survey with all questions
3. Configure survey settings on that platform
4. Get the shareable link to your survey

**Expected Result:** You have a working survey URL

#### Step 2: Add External Survey to System

1. From the Surveys list page, click "Create Survey"
2. Toggle "External Survey" option
3. Enter basic information:
   - **Title**: Name of your survey
   - **Description**: Brief description
   - **Start Date**: When survey becomes available
   - **End Date**: When survey closes
   - **Status**: Draft, Active, or Closed
   - **External URL**: Paste the survey link from your external platform

4. Click "Save Survey"

**Expected Result:** External survey is added to the system with a link to the external platform

## Survey Settings

### Status Management

- **Draft**: Use while building your survey
  - Not visible to alumni
  - Can be edited freely
  - Good for testing and review

- **Active**: Survey is live
  - Visible to alumni
  - Accepting responses
  - Limited editing (to preserve data integrity)

- **Closed**: Survey has ended
  - Visible but not accepting responses
  - Responses can still be viewed and analyzed
  - Cannot be reopened (create a new survey instead)

### Date and Time Settings

- **Start Date**: Survey becomes available at this date/time
- **End Date**: Survey stops accepting responses at this date/time
- Alumni can only submit responses between these dates
- System automatically enforces these dates

## Question Types Explained

### Text Answer
- Open-ended responses
- Good for: Detailed feedback, suggestions, explanations
- Example: "What improvements would you like to see in the alumni network?"

### Multiple Choice (Single Answer)
- Select one option from a list
- Good for: Categorical data, preferences, yes/no questions
- Example: "What is your current employment status?"

### Multiple Choice (Multiple Answers)
- Select multiple options from a list
- Good for: Skills, interests, multiple applicable items
- Example: "Which services would you like the alumni association to offer? (Select all that apply)"

### Rating Scale
- Numeric rating (1-5 or 1-10)
- Good for: Satisfaction, quality, importance ratings
- Example: "Rate your satisfaction with the alumni portal (1-5)"

### Likert Scale
- Agreement scale with predefined labels
- Good for: Opinions, attitudes, perceptions
- Example: "The alumni association effectively supports career development"

### Date/Time
- Specific date or time input
- Good for: Event preferences, availability, historical dates
- Example: "When did you graduate?"

### File Upload
- Allow respondents to attach files
- Good for: Documents, images, portfolios
- Example: "Upload your current resume"

### Email/Phone/URL
- Validated input fields
- Good for: Contact information, references
- Example: "Provide your current email address"

## Tips and Best Practices

### Survey Design

1. **Keep it concise**: Aim for 10-15 questions maximum
   - Longer surveys have lower completion rates
   - Focus on essential information only

2. **Start with easy questions**: Build engagement
   - Begin with simple, non-sensitive questions
   - Save demographic questions for the end

3. **Use clear language**: Avoid jargon and technical terms
   - Write at a general reading level
   - Define any necessary technical terms

4. **One question at a time**: Don't combine multiple questions
   - Bad: "How satisfied are you with the website and mobile app?"
   - Good: Separate into two questions

5. **Provide context**: Explain why you're asking
   - Include a brief introduction
   - Explain how data will be used

### Question Writing

1. **Be specific**: Avoid vague questions
   - Bad: "How do you feel about the alumni network?"
   - Good: "How satisfied are you with networking opportunities provided by the alumni association?"

2. **Avoid leading questions**: Don't bias responses
   - Bad: "Don't you think the new portal is great?"
   - Good: "How would you rate the new alumni portal?"

3. **Use balanced scales**: Provide equal positive and negative options
   - Include a neutral option when appropriate
   - Use consistent scale directions

4. **Consider skip logic**: Plan question flow
   - Not all questions apply to all respondents
   - Note: Skip logic may require external survey tools

### Technical Considerations

1. **Test before launching**: Create a draft and test
   - Complete the survey yourself
   - Ask colleagues to test
   - Check on different devices

2. **Set realistic dates**: Allow adequate response time
   - Minimum 1-2 weeks for simple surveys
   - 3-4 weeks for comprehensive surveys
   - Consider holidays and busy periods

3. **Start as Draft**: Don't activate immediately
   - Review all questions
   - Check for errors
   - Get approval if needed

4. **Plan for analysis**: Consider how you'll use the data
   - Choose question types that facilitate analysis
   - Think about reporting needs

## Common Use Cases

### Career Development Survey
- Current employment status
- Job satisfaction
- Skills and training needs
- Career goals
- Mentorship interest

### Event Feedback Survey
- Event satisfaction ratings
- Session quality
- Venue and logistics
- Suggestions for improvement
- Future event preferences

### Alumni Engagement Survey
- Communication preferences
- Interest in services
- Volunteer opportunities
- Donation likelihood
- Program suggestions

### Tracer Study
- Employment history
- Educational attainment
- Skills utilization
- Career progression
- Employer feedback

## Troubleshooting

### Issue: Cannot save survey

**Possible Causes:**
- End date is before start date
- Required fields are missing
- External URL is invalid (for external surveys)

**Solution:**
- Check all required fields are filled
- Verify dates are in correct order
- Validate external URL format

### Issue: Questions not appearing in correct order

**Possible Cause:**
- Display order numbers are incorrect

**Solution:**
- Review display order values
- Ensure sequential numbering (1, 2, 3, etc.)
- Save and refresh to see changes

### Issue: Cannot add options to question

**Possible Cause:**
- Question type doesn't support options
- JavaScript error in browser

**Solution:**
- Verify question type is Multiple Choice or Checkbox
- Refresh the page
- Try a different browser
- Clear browser cache

### Issue: Survey not visible to alumni

**Possible Causes:**
- Status is set to "Draft"
- Start date is in the future
- End date has passed

**Solution:**
- Change status to "Active"
- Verify start and end dates
- Check current date/time

## Related Features

- [Managing Surveys](managing-surveys.md) - Edit, delete, and manage survey status
- [Viewing Survey Responses](viewing-responses.md) - Analyze and export survey data
- [Survey Analytics](../analytics/README.md) - View survey participation statistics

## Need Help?

If you encounter issues not covered in this guide:
- Contact the system administrator
- Check the FAQ section
- Submit a support ticket through the feedback form
