# Managing Events

## Overview

The event management feature allows administrators to view, edit, delete, and monitor all events in the system. This includes managing RSVPs, viewing attendee lists, and updating event details as needed.

## Who Can Use This Feature

- **Admin Users**: Full access to manage all events
- **Staff Members**: Can manage events they created or have been assigned to

## Prerequisites

- Admin or staff account with appropriate permissions
- Existing events in the system

## How to Access

1. Log in to your admin account
2. Navigate to the **Events** section from the main menu
3. The events list displays all events in the system

## Key Features

- View all events in card or table format
- Search and filter events by status
- Edit event details
- Delete events
- View RSVP statistics
- Monitor attendee lists
- Export event data
- Switch between different view modes

## Step-by-Step Guide

### Task 1: Viewing Events List

1. Navigate to the Events page
2. **View Options**:
   - **Card View**: Visual grid layout with event cards (default)
   - **Table View**: Compact tabular format with more details
3. Toggle between views using the **View Mode** buttons at the top
   
   **Expected Result**: Events display in your selected view format

### Task 2: Searching for Events

1. Locate the **Search Events** field in the search section
2. Enter keywords to search:
   - Event title
   - Description text
   - Location name
3. Results filter automatically as you type
   
   **Expected Result**: Only matching events are displayed

### Task 3: Filtering Events by Status

1. In the search section, locate the **Filter by Status** buttons
2. Click on a status filter:
   - **All**: Shows all events (default)
   - **Published**: Only published events
   - **Draft**: Only draft events
   - **Cancelled**: Only cancelled events
   - **Completed**: Only completed events
3. The active filter is highlighted in blue
   
   **Expected Result**: Events list updates to show only events with the selected status

### Task 4: Viewing Event Details

**In Card View:**
1. Locate the event card you want to view
2. Click the **"View Details"** button (blue button with eye icon)
3. A modal window opens with full event details

**In Table View:**
1. Find the event in the table
2. Click the eye icon in the Actions column
3. A modal window opens with full event details

**Event Details Include:**
- Full description
- Date and time information
- Location or virtual link
- RSVP counts (Attending, Not Attending, Maybe)
- Event status and visibility
- Event image (if uploaded)
- Created by information

**Expected Result**: Modal displays complete event information

### Task 5: Editing Events

**Method 1: From Card View**
1. Locate the event card
2. Click the **Edit** button (yellow button with pencil icon)
3. You're redirected to the event edit form

**Method 2: From Table View**
1. Find the event in the table
2. Click the pencil icon in the Actions column
3. You're redirected to the event edit form

**Method 3: From Event Details**
1. Open the event details modal
2. Click the **"Edit Event"** button in the modal footer
3. You're redirected to the event edit form

**On the Edit Form:**
1. Modify any event details as needed
2. All fields work the same as in event creation
3. Click **"Save Changes"** to update the event
4. Click **"Cancel"** to discard changes

**Expected Result**: 
- Success: Green notification appears, changes are saved
- You're redirected back to the events list

### Task 6: Deleting Events

**Method 1: From Card View**
1. Locate the event card
2. Click the **Delete** button (red button with trash icon)
3. A confirmation dialog appears

**Method 2: From Table View**
1. Find the event in the table
2. Click the trash icon in the Actions column
3. A confirmation dialog appears

**Confirmation Process:**
1. Review the event title in the confirmation message
2. Read the warning about what will be deleted:
   - All RSVPs associated with the event
   - All notifications sent for the event
   - Any uploaded images or files
3. Choose your action:
   - Click **"Delete Event"** to permanently remove the event
   - Click **"Cancel"** to keep the event

**Expected Result**: 
- If confirmed: Event is deleted, success message appears
- If cancelled: Event remains unchanged

**Important**: Deletion is permanent and cannot be undone!

### Task 7: Managing RSVPs

**Viewing RSVP Statistics:**
1. In Card View, each event card shows the total RSVP count
2. In the event details modal, view detailed RSVP breakdown:
   - **Attending**: Number of confirmed attendees
   - **Not Attending**: Number of declined RSVPs
   - **Maybe**: Number of tentative responses

**Viewing Attendee List:**
1. Open the event details modal
2. Scroll to the RSVP section
3. View the list of users who have RSVP'd
4. See each user's RSVP status and any notes they provided

**Expected Result**: Complete visibility into event attendance

### Task 8: Viewing Event Metadata

Each event displays important metadata:

**In Card View:**
- Event status badge (Draft, Published, Cancelled, Completed)
- Start date and time
- Location type (Virtual or Physical)
- RSVP count

**In Table View:**
- All card view information plus:
- Event description preview
- Created by information
- More compact layout for scanning multiple events

**In Detail Modal:**
- All information from card/table view plus:
- Full description
- End date and time
- Maximum participants (if set)
- Notified groups
- Event image
- Virtual link (for virtual events)

**Expected Result**: Easy access to all event information at different detail levels

### Task 9: Exporting Event Data

1. On the Events page, click the **"Export"** button in the search section
2. Select the events you want to export (optional):
   - Check individual event checkboxes
   - Or use filters to narrow down events first
3. Choose export format (if prompted)
4. Download begins automatically

**Exported Data Includes:**
- Event title and description
- Date and time information
- Location details
- Status and visibility
- RSVP statistics
- Created by information

**Expected Result**: CSV or Excel file downloads with event data

### Task 10: Bulk Operations

**Selecting Multiple Events:**
1. In Card View or Table View, check the checkbox on each event card/row
2. Or use **"Select All"** checkbox in Table View header
3. Selected events are highlighted

**Available Bulk Actions:**
- Export selected events
- (Future: Bulk status updates, bulk delete)

**Expected Result**: Multiple events can be selected and processed together

## View Modes

### Card View
- **Best For**: Visual browsing, quick overview
- **Features**:
  - Large, easy-to-read cards
  - Event images prominently displayed
  - Quick action buttons
  - Grid layout adapts to screen size
- **Use When**: You want to browse events visually or need to see event images

### Table View
- **Best For**: Detailed comparison, data analysis
- **Features**:
  - Compact rows with more information
  - Sortable columns
  - Better for scanning many events
  - More data visible at once
- **Use When**: You need to compare multiple events or work with large event lists

## Event Status Management

### Status Transitions

**Draft → Published**
- Use when event is ready for public viewing
- Triggers notifications to selected groups
- Event becomes visible based on visibility settings

**Published → Cancelled**
- Use when event won't happen
- Notifies all users who RSVP'd
- Event remains visible but marked as cancelled

**Published → Completed**
- Use after event has concluded
- Marks event as historical
- Useful for record-keeping and reporting

**Any Status → Draft**
- Use to temporarily hide an event
- Useful for making major updates
- No notifications sent

### Best Practices for Status Management
- Keep events in Draft until all details are finalized
- Publish events well in advance to allow RSVP time
- Mark events as Completed after they end for clean event lists
- Use Cancelled status instead of deleting to maintain records

## RSVP Management

### Understanding RSVP Statuses

**Attending (Yes)**
- User confirmed they will attend
- Counts toward participant limit
- User receives event reminders

**Not Attending (No)**
- User declined the invitation
- Does not count toward participant limit
- User won't receive further reminders

**Maybe**
- User is tentatively interested
- Does not count toward participant limit
- User receives event reminders

### Monitoring Attendance

**Check Participant Limits:**
- View current RSVP count vs. maximum participants
- System prevents new RSVPs when limit is reached
- Consider increasing limit if demand is high

**Review RSVP Notes:**
- Users can add notes with their RSVP
- Check for special requests or questions
- Follow up with attendees as needed

**Track Trends:**
- Monitor RSVP rates over time
- Identify popular event types
- Adjust future event planning accordingly

## Tips and Best Practices

### Event List Organization
- Use status filters to focus on active events
- Regularly mark completed events to keep list clean
- Use search to quickly find specific events
- Switch to Table View when working with many events

### Editing Events
- Make minor updates directly without changing status
- Set to Draft for major changes to avoid confusion
- Update event details if location or time changes
- Notify attendees of significant changes separately

### Deleting Events
- Consider marking as Cancelled instead of deleting
- Deletion removes all historical data
- Export event data before deleting if needed for records
- Only delete spam or duplicate events

### RSVP Management
- Check RSVPs regularly as event date approaches
- Follow up with "Maybe" responses closer to event date
- Use RSVP data to plan logistics (seating, catering, etc.)
- Export attendee list for check-in purposes

### Communication
- Use event notifications to reach target groups
- Send follow-up announcements for important updates
- Consider creating an announcement for major event changes
- Provide contact information for questions

## Troubleshooting

### Cannot Edit Event
- **Cause**: Insufficient permissions
- **Solution**: Ensure you have admin or staff role, or contact a system administrator

### Cannot Delete Event
- **Cause**: Insufficient permissions or event has dependencies
- **Solution**: 
  - Verify you have admin/staff permissions
  - Consider marking as Cancelled instead
  - Contact system administrator if issue persists

### Event Not Appearing in List
- **Cause**: Status filter is active
- **Solution**: 
  - Click "All" in the status filter
  - Check if event status matches current filter
  - Use search to find the event by name

### RSVP Count Seems Wrong
- **Cause**: May include all RSVP types
- **Solution**: 
  - Open event details to see breakdown
  - Only "Attending" counts toward participant limit
  - "Maybe" and "Not Attending" are tracked separately

### Export Not Working
- **Cause**: No events selected or browser blocking download
- **Solution**:
  - Ensure at least one event is visible (check filters)
  - Check browser download settings
  - Try a different browser if issue persists

### Changes Not Saving
- **Cause**: Validation errors or network issues
- **Solution**:
  - Look for red error messages on the form
  - Check all required fields are filled
  - Verify internet connection
  - Try refreshing the page and editing again

## Related Features

- [Creating Events](creating-events.md) - How to create new events
- [Event Participation](../../user-features/events/README.md) - User perspective on events
- [Announcements](../announcements/README.md) - Communicating with alumni
- [Alumni Groups](../../user-features/groups/README.md) - Managing groups for event notifications
- [Analytics](../analytics/README.md) - Viewing event participation statistics
