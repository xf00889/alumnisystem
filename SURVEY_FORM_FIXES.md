# Survey Form Fixes

## Issues Fixed

### 1. Survey Edit Page Not Saving Questions
**Problem**: When editing a survey and adding questions, the questions were not being saved to the database.

**Root Cause**: The `SurveyUpdateView` was not processing the questions data that was being sent via JavaScript. Only the `SurveyCreateView` had the logic to handle questions.

**Solution**: 
- Added question processing logic to `SurveyUpdateView.form_valid()` method
- The view now:
  - Parses the JSON questions data from the POST request
  - Deletes existing questions if new ones are provided
  - Creates new `SurveyQuestion` objects with their options
  - Handles scale types for rating/likert questions
  - Logs the changes for audit purposes

**Files Modified**:
- `surveys/views.py` - Updated `SurveyUpdateView` class

### 2. No Success Alert After Saving
**Problem**: After creating or updating a survey, no success message was displayed to the user.

**Solution**:
- Added `messages.success()` calls in both `SurveyCreateView` and `SurveyUpdateView`
- Added `messages.error()` calls for error handling
- Removed JSON response from create view (was causing redirect issues)
- Now uses Django's standard form submission with messages framework

**Files Modified**:
- `surveys/views.py` - Added success/error messages to both views

### 3. Redundant "Add Question" Button in Detail View
**Problem**: The survey detail page showed an "Add Question" button that was redundant since questions should be added through the edit form.

**Solution**:
- Removed the "Add Question" button from the survey detail page footer
- Users now add questions directly in the edit form using the inline "Add Question" functionality

**Files Modified**:
- `templates/surveys/admin/survey_detail.html` - Removed redundant button

### 4. Redundant "Add Questions" Button in Edit Form Preview
**Problem**: The edit form's preview sidebar showed an "Add Questions" button that was confusing since questions are added inline in the form.

**Solution**:
- Removed the "Add Questions" button from the preview sidebar
- Added a comment explaining that questions are added inline

**Files Modified**:
- `templates/surveys/admin/survey_form.html` - Removed redundant button from preview section

## How It Works Now

### Creating a Survey with Questions:
1. User fills in survey title, description, dates, and status
2. User clicks "Add Question" button to add questions inline
3. For each question, user can:
   - Enter question text
   - Select question type (text, multiple choice, rating, etc.)
   - Mark as required/optional
   - Add help text
   - Add options for multiple choice questions
   - Set scale type for rating questions
4. User clicks "Create Survey"
5. JavaScript gathers all questions data and appends it to the form as JSON
6. Django view processes the form and creates the survey with all questions
7. Success message is displayed
8. User is redirected to survey list

### Editing a Survey:
1. User navigates to survey detail page
2. User clicks "Edit Survey" button
3. Edit form loads with existing survey data
4. User can modify survey details and add/edit questions inline
5. User clicks "Update Survey"
6. JavaScript gathers all questions data (including new ones)
7. Django view:
   - Updates survey details
   - Deletes old questions if new ones are provided
   - Creates new questions with their options
8. Success message is displayed
9. User is redirected to survey list

## Technical Details

### Question Data Format (JSON):
```json
[
  {
    "display_order": 0,
    "question_text": "What is your name?",
    "question_type": "text",
    "is_required": true,
    "help_text": "Please enter your full name",
    "options": []
  },
  {
    "display_order": 1,
    "question_text": "How satisfied are you?",
    "question_type": "rating",
    "is_required": true,
    "help_text": "",
    "scale_type": "1-5",
    "options": []
  },
  {
    "display_order": 2,
    "question_text": "What is your favorite color?",
    "question_type": "multiple_choice",
    "is_required": false,
    "help_text": "",
    "options": [
      {"option_text": "Red", "display_order": 0},
      {"option_text": "Blue", "display_order": 1},
      {"option_text": "Green", "display_order": 2}
    ]
  }
]
```

### View Processing Logic:
1. Parse JSON from `request.POST.get('questions', '[]')`
2. If questions exist and survey is not external:
   - Delete existing questions (for updates only)
   - Loop through questions data
   - Create `SurveyQuestion` objects
   - Add scale_type if applicable
   - Create `QuestionOption` objects for each option
3. Log the operation
4. Display success message
5. Redirect to success URL

## Testing Checklist

- [x] Create new survey with questions
- [x] Edit existing survey and add questions
- [x] Edit existing survey and modify questions
- [x] Success message appears after create
- [x] Success message appears after update
- [x] Questions are saved to database
- [x] Question options are saved correctly
- [x] Scale types are saved for rating questions
- [x] Required/optional flag is saved
- [x] Help text is saved
- [x] Display order is maintained
- [x] No redundant buttons in detail view
- [x] No redundant buttons in edit form preview

## Notes

- The JavaScript in `survey_form.html` handles gathering questions data on form submission
- The form submits normally (not via AJAX) to avoid redirect issues
- Questions are deleted and recreated on update to ensure consistency
- Error handling includes both logging and user-facing messages
- The solution maintains backward compatibility with external surveys
