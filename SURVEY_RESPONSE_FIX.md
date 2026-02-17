# Survey Response Saving Fix

## Issue
Survey responses were being created but answers were not being saved correctly. The `text_answer` field was showing as `None` even when users submitted answers.

## Root Cause
The view code had a logic error where it was creating empty `ResponseAnswer` objects for required questions that appeared to have no answer. This happened because:

1. When retrieving text answers from POST data, empty strings (`""`) are falsy in Python
2. The code checked `if text_answer:` which failed for empty strings
3. Then it checked `elif question.is_required:` and created an empty answer with `text_answer=None`
4. This empty answer was saved to the database, overriding any actual answer

## Changes Made

### 1. Fixed Answer Creation Logic (`surveys/views.py`)
- **Removed** the code that created empty answers for required questions
- Now only creates answers when there's actual data to save
- Added `.strip()` to text answers to remove whitespace

### 2. Improved Logging
- Changed debug logs to info logs so they appear in production
- Added detailed logging of POST data and field values
- Added logging of answer creation with the actual data being saved

### 3. Fixed Syntax Error
- Removed duplicate `return HttpResponseRedirect(self.success_url)` statement in `SurveyDeleteView`

## Testing Instructions

1. **Create a new survey** with various question types (text, email, number, phone, url)
2. **Submit a response** with answers to all questions
3. **Check the logs** at `logs/alumni_system.log` to see the detailed processing:
   - Look for "Processing question" entries showing the POST data
   - Look for "Saving text answer" entries showing what's being saved
   - Look for "Created answer" entries showing the answer IDs
4. **View the responses** in the admin panel to verify answers are displayed correctly

## Expected Behavior

- All answered questions should have their answers saved in the `text_answer`, `rating_value`, or `selected_option` fields
- Unanswered questions should have NO `ResponseAnswer` record (not an empty one)
- The survey responses page should display all answers correctly
- No more "No answer provided" messages for questions that were actually answered

## Files Modified

1. `surveys/views.py` - Fixed answer creation logic and improved logging
2. `surveys/management/commands/check_survey_responses.py` - Removed reference to non-existent `file_answer` field

## Next Steps

1. Test by submitting a new survey response
2. Check the logs to verify POST data is being received
3. Verify answers are displayed correctly in the admin panel
4. If issues persist, check the logs for the detailed POST data and field processing
