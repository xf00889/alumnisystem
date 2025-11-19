# Creating Events

## Overview

The event creation feature allows administrators to create and publish events for the alumni community. Events can be in-person or virtual, with customizable settings for visibility, notifications, and participant limits.

## Who Can Use This Feature

- **Admin Users**: Full access to create, edit, and manage all events
- **Staff Members**: Can create and manage events

## Prerequisites

- Admin or staff account with appropriate permissions
- Event details including title, description, date/time, and location

## How to Access

1. Log in to your admin account
2. Navigate to the **Events** section from the main menu
3. Click the **"New Event"** button in the search section

## Key Features

- Create in-person or virtual events
- Set event status (draft, published, cancelled, completed)
- Configure visibility (public or private)
- Set participant limits
- Upload event images
- Notify specific alumni groups
- Schedule events with start and end times

## Step-by-Step Guide

### Task 1: Navigate to Event Creation

1. From the Events page, locate the search section at the top
2. Click the **"New Event"** button (blue button with plus icon)
   - **Expected Result**: You'll be redirected to the event creation form

### Task 2: Enter Basic Information

1. In the **Basic Information** section, enter the following:
   - **Title** (required): Enter a clear, descriptive event title
     - Example: "Alumni Homecoming 2024"
   - **Description** (required): Provide detailed information about the event
     - Include purpose, agenda, and any special instructions
     - Use the text area to write multiple paragraphs if needed
   
   **Expected Result**: The form fields are populated with your event information

### Task 3: Set Date and Time

1. In the **Date and Time** section:
   - **Start Date & Time** (required): Click the field and select from the date/time picker
     - Note: Start date cannot be in the past
   - **End Date & Time** (required): Select the event end date and time
     - Note: End date must be after the start date
   
   **Expected Result**: Both date fields show your selected dates in the format "MM/DD/YYYY HH:MM AM/PM"

### Task 4: Configure Location Details

1. In the **Location Details** section, choose the event type:

   **For In-Person Events:**
   - Leave the "Virtual Event" toggle OFF
   - **Location** (required): Enter the physical address or venue name
     - Example: "NORSU Main Campus, Auditorium Building"
   - **Maximum Participants** (optional): Enter a number to limit attendees
   
   **For Virtual Events:**
   - Toggle **"Virtual Event"** ON
   - **Virtual Link** (required): Enter the meeting URL
     - Example: "https://zoom.us/j/123456789"
   - **Maximum Participants** (optional): Enter a number to limit attendees
   - Note: Location field will automatically be set to "Virtual Event"
   
   **Expected Result**: The form adapts based on your selection, showing/hiding relevant fields

### Task 5: Configure Event Settings

1. In the **Event Settings** section, configure:
   
   **Status** (required):
   - **Draft**: Event is not visible to users (use for work-in-progress)
   - **Published**: Event is live and visible based on visibility settings
   - **Cancelled**: Event is marked as cancelled
   - **Completed**: Event has ended
   
   **Visibility** (required):
   - **Public**: Visible to all visitors, including non-registered users
   - **Private**: Only visible to logged-in alumni members
   
   **Event Image** (optional):
   - Click **"Choose Event Image"** to upload a photo
   - Supported formats: JPG, PNG, GIF
   - Maximum file size: 5MB
   - **Preview**: Image preview appears after selection
   - **Remove**: Click the "Remove" button on the preview to delete the image
   
   **Expected Result**: Status and visibility are set, and image preview appears if uploaded

### Task 6: Notify Alumni Groups

1. In the **Notify Groups** section:
   - Review the list of available alumni groups
   - Check the boxes next to groups you want to notify about this event
   - Use **"Select All"** checkbox to quickly select all groups
   - Groups will receive notifications when the event is published
   
   **Expected Result**: Selected groups are highlighted with checkmarks

### Task 7: Review and Submit

1. Review all entered information for accuracy
2. Check for any validation errors (marked in red)
3. Choose your action:
   - Click **"Create Event"** to save the event
   - Click **"Cancel"** to discard changes and return to the events list
   
   **Expected Result**: 
   - Success: Green notification appears, and you're redirected to the events list
   - Error: Red notification appears with specific error messages to fix

## Event Types

### In-Person Events
- Require a physical location
- Can include venue details and directions
- Suitable for campus gatherings, reunions, ceremonies

### Virtual Events
- Require a meeting link (Zoom, Google Meet, etc.)
- Location automatically set to "Virtual Event"
- Suitable for webinars, online meetings, remote workshops

### Hybrid Events
- Create as in-person event
- Include virtual meeting link in the description
- Specify in description that both options are available

## Event Status Workflow

```
Draft → Published → Completed
   ↓
Cancelled
```

- **Draft**: Initial state for planning and preparation
- **Published**: Event is live and accepting RSVPs
- **Cancelled**: Event won't happen (notifies registered attendees)
- **Completed**: Event has concluded (for archival purposes)

## Validation Rules

The system enforces the following rules:

1. **Required Fields**: Title, description, start date, end date, location (or virtual link), status, and visibility must be filled
2. **Date Validation**: 
   - Start date cannot be in the past
   - End date must be after start date
3. **Virtual Events**: Must have a virtual link
4. **In-Person Events**: Must have a physical location
5. **Publishing**: Cannot publish without all required fields completed

## Tips and Best Practices

### Writing Effective Event Descriptions
- Start with a compelling summary
- Include the event agenda or schedule
- Mention any requirements (registration, fees, dress code)
- Add contact information for questions
- Include parking or transportation details for in-person events

### Choosing Event Status
- Use **Draft** while planning and coordinating
- Switch to **Published** when ready to accept RSVPs
- Use **Cancelled** if the event won't happen (system can notify attendees)
- Mark as **Completed** after the event for record-keeping

### Setting Visibility
- Use **Public** for events open to the community (fundraisers, open houses)
- Use **Private** for alumni-only events (exclusive gatherings, member meetings)

### Managing Participant Limits
- Set limits for venues with capacity restrictions
- Leave blank for unlimited attendance
- System will prevent RSVPs once limit is reached

### Using Event Images
- Use high-quality, relevant images
- Recommended size: 1200x630 pixels
- Images appear in event cards and detail pages
- Choose images that represent the event theme

### Notifying Groups
- Select relevant groups based on event target audience
- Example: Notify "Engineering Alumni" for engineering-specific events
- Notifications are sent when event status changes to "Published"
- Avoid over-notifying to prevent notification fatigue

## Troubleshooting

### "Start date cannot be in the past" Error
- **Cause**: Selected start date/time has already passed
- **Solution**: Choose a future date and time for the event

### "End date must be after start date" Error
- **Cause**: End date is the same as or before start date
- **Solution**: Ensure end date/time is later than start date/time

### "Virtual link is required for virtual events" Error
- **Cause**: Virtual Event toggle is ON but no link provided
- **Solution**: Enter a valid meeting URL or turn off Virtual Event toggle

### "Location is required for in-person events" Error
- **Cause**: Virtual Event toggle is OFF but no location provided
- **Solution**: Enter a physical location or enable Virtual Event toggle

### Image Upload Fails
- **Cause**: File size exceeds 5MB or unsupported format
- **Solution**: 
  - Compress the image to reduce file size
  - Convert to JPG, PNG, or GIF format
  - Use online tools to resize/compress images

### Cannot Publish Event
- **Cause**: Missing required fields
- **Solution**: Review the form for any red error messages and complete all required fields

## Related Features

- [Managing Events](managing-events.md) - Edit, delete, and manage existing events
- [Event Participation](../../user-features/events/README.md) - How users view and RSVP to events
- [Alumni Groups](../../user-features/groups/README.md) - Managing groups for event notifications
- [Announcements](../announcements/README.md) - Alternative way to communicate with alumni
