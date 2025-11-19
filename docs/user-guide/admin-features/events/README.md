# Events

## Overview

The Event Management system allows administrators to create, manage, and monitor events for the alumni community. Events can be in-person or virtual, with comprehensive features for RSVP tracking, group notifications, and attendance management.

## Who Can Use This Feature

- **Admin Users**: Full access to all event management features
- **Staff Members**: Can create and manage events

## Key Capabilities

### Event Creation
- Create in-person and virtual events
- Set event status and visibility
- Upload event images
- Configure participant limits
- Notify specific alumni groups

### Event Management
- View all events in card or table format
- Search and filter events
- Edit event details
- Delete events
- Monitor RSVPs and attendance

### RSVP Tracking
- View RSVP statistics (Attending, Not Attending, Maybe)
- Monitor participant counts
- Track attendance against limits
- Export attendee lists

## Quick Links

### Documentation
- [Creating Events](creating-events.md) - Step-by-step guide to creating new events
- [Managing Events](managing-events.md) - How to view, edit, delete, and monitor events

### Related Features
- [Event Participation (User View)](../../user-features/events/README.md) - How users interact with events
- [Announcements](../announcements/README.md) - Alternative communication method
- [Alumni Groups](../../user-features/groups/README.md) - Managing groups for notifications

## Common Tasks

### Creating a New Event
1. Navigate to Events page
2. Click "New Event" button
3. Fill in event details
4. Set status and visibility
5. Select groups to notify
6. Click "Create Event"

[Detailed Guide →](creating-events.md)

### Editing an Existing Event
1. Find the event in the list
2. Click the Edit button (pencil icon)
3. Update event details
4. Click "Save Changes"

[Detailed Guide →](managing-events.md#task-5-editing-events)

### Viewing Event RSVPs
1. Open event details modal
2. View RSVP breakdown
3. Check attendee list
4. Export data if needed

[Detailed Guide →](managing-events.md#task-7-managing-rsvps)

### Cancelling an Event
1. Edit the event
2. Change status to "Cancelled"
3. Save changes
4. System notifies all RSVP'd users

[Detailed Guide →](managing-events.md#event-status-management)

## Event Types

### In-Person Events
Events held at physical locations with venue details and directions.

**Best For:**
- Campus gatherings
- Alumni reunions
- Ceremonies and celebrations
- Networking events

### Virtual Events
Online events with meeting links for remote participation.

**Best For:**
- Webinars and workshops
- Online meetings
- Remote presentations
- Global alumni engagement

### Hybrid Events
Events offering both in-person and virtual attendance options.

**Implementation:**
- Create as in-person event
- Include virtual link in description
- Specify both options in event details

## Event Status Workflow

```
Draft → Published → Completed
   ↓
Cancelled
```

### Status Descriptions

**Draft**
- Initial planning state
- Not visible to users
- Use for preparation and coordination

**Published**
- Event is live and visible
- Accepting RSVPs
- Notifications sent to selected groups

**Cancelled**
- Event won't happen
- Notifies all RSVP'd users
- Remains visible but marked as cancelled

**Completed**
- Event has concluded
- Archived for records
- No longer accepting RSVPs

## Visibility Options

### Public Events
- Visible to all website visitors
- No login required to view
- Suitable for community events and fundraisers

### Private Events
- Only visible to logged-in alumni
- Requires authentication to view and RSVP
- Suitable for exclusive alumni gatherings

## Best Practices

### Planning Events
- Create events in Draft status while planning
- Publish well in advance to allow RSVP time
- Set realistic participant limits
- Choose appropriate visibility settings

### Event Details
- Write clear, comprehensive descriptions
- Include all relevant information (agenda, requirements, contact)
- Upload high-quality event images
- Provide accurate location or virtual link

### Group Notifications
- Select relevant groups based on target audience
- Avoid over-notifying to prevent fatigue
- Use targeted notifications for better engagement

### RSVP Management
- Monitor RSVPs regularly
- Follow up with tentative responses
- Use data for logistics planning
- Export attendee lists for check-in

### Post-Event
- Mark events as Completed after they end
- Keep cancelled events for records
- Review RSVP data for future planning
- Archive or delete old draft events

## Tips for Success

### Maximize Attendance
- Publish events early
- Use compelling titles and descriptions
- Include attractive event images
- Notify relevant alumni groups
- Send reminder announcements

### Effective Communication
- Provide complete event information
- Include contact details for questions
- Update event details if changes occur
- Follow up with attendees before event

### Data Management
- Export event data regularly
- Keep records of past events
- Use Completed status for archiving
- Delete only spam or duplicate events

### User Experience
- Use Public visibility for open events
- Set Private for exclusive gatherings
- Provide clear RSVP instructions
- Include accessibility information

## Troubleshooting

### Common Issues

**Cannot Create Event**
- Verify you have admin/staff permissions
- Check all required fields are filled
- Ensure dates are valid (future dates, end after start)

**Event Not Visible to Users**
- Check event status (must be Published)
- Verify visibility settings
- Ensure start date hasn't passed

**RSVPs Not Working**
- Check if participant limit is reached
- Verify event is Published
- Ensure users are logged in (for Private events)

**Notifications Not Sent**
- Verify groups are selected
- Check event status is Published
- Confirm group members have valid emails

For more detailed troubleshooting, see:
- [Creating Events Troubleshooting](creating-events.md#troubleshooting)
- [Managing Events Troubleshooting](managing-events.md#troubleshooting)

## Getting Help

If you encounter issues not covered in this documentation:

1. Check the specific feature documentation for detailed troubleshooting
2. Contact your system administrator
3. Review the [FAQ](../../faq.md) for common questions
4. Submit feedback through the [Feedback System](../../user-features/feedback/README.md)

## Feature Roadmap

Upcoming enhancements may include:
- Bulk event operations
- Event templates
- Recurring events
- Advanced RSVP management
- Event check-in system
- Integration with calendar applications

---

**Last Updated**: November 2024  
**Version**: 1.0
