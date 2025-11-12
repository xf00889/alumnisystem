# Mentorship Notifications Implementation

## Overview
Added automatic notifications for mentorship status changes to keep both mentors and mentees informed about their mentorship activities.

## Notifications Implemented

### 1. New Mentorship Request
**Trigger:** When a mentee submits a mentorship request  
**Recipient:** Mentor  
**Message:** "{Mentee Name} sent you a mentorship request"  
**Description:** "{Mentee Name} has requested you as their mentor. Review the request in your dashboard."  
**Level:** Info  

**Locations:**
- `mentorship/views.py` - `request_mentorship()` function (line ~230)
- `mentorship/views.py` - `MentorshipRequestViewSet.create()` method (line ~520)

### 2. Request Accepted
**Trigger:** When a mentor accepts a mentorship request  
**Recipient:** Mentee  
**Message:** "{Mentor Name} accepted your mentorship request"  
**Description:** "{Mentor Name} has accepted your mentorship request. You can now start your mentorship journey!"  
**Level:** Success  

**Locations:**
- `mentorship/views.py` - `update_request_status()` function (line ~80)
- `mentorship/views.py` - `MentorshipRequestViewSet.update_status()` method (line ~575)

### 3. Request Rejected
**Trigger:** When a mentor declines a mentorship request  
**Recipient:** Mentee  
**Message:** "{Mentor Name} declined your mentorship request"  
**Description:** "{Mentor Name} has declined your mentorship request. You can explore other mentors."  
**Level:** Warning  

**Locations:**
- `mentorship/views.py` - `update_request_status()` function (line ~85)
- `mentorship/views.py` - `MentorshipRequestViewSet.update_status()` method (line ~582)

### 4. Mentorship Completed
**Trigger:** When a mentor marks a mentorship as completed  
**Recipient:** Mentee  
**Message:** "{Mentor Name} marked your mentorship as completed"  
**Description:** "{Mentor Name} has marked your mentorship as completed. Congratulations on completing your mentorship!"  
**Level:** Success  

**Locations:**
- `mentorship/views.py` - `update_request_status()` function (line ~90)
- `mentorship/views.py` - `MentorshipRequestViewSet.update_status()` method (line ~589)

## Technical Details

### Package Used
- **django-notifications-hq** (version 1.8.3)
- Already installed in requirements.txt

### Import Added
```python
from notifications.signals import notify
```

### Notification Structure
```python
notify.send(
    sender=request.user,           # User who triggered the action
    recipient=target_user,          # User who receives the notification
    verb='action description',      # Short action description
    description='detailed message', # Full notification message
    action_object=mentorship_obj,   # Related object (MentorshipRequest)
    level='success/info/warning'    # Notification level
)
```

## User Experience

### For Mentees:
1. Get notified when mentor accepts their request
2. Get notified when mentor declines their request
3. Get notified when mentorship is marked as completed

### For Mentors:
1. Get notified when a new mentorship request is received

## Next Steps (Optional Enhancements)

1. **Email Notifications:** Configure email backend to send email notifications
2. **In-App Notification Center:** Create a notification dropdown in the navbar
3. **Notification Preferences:** Allow users to customize notification settings
4. **Additional Notifications:**
   - Meeting scheduled/cancelled
   - Progress updates
   - New messages
   - Timeline milestones completed

## Testing

To test the notifications:

1. **Test New Request:**
   - Login as a mentee
   - Submit a mentorship request
   - Login as the mentor
   - Check notifications (should see new request notification)

2. **Test Accept/Reject:**
   - Login as a mentor
   - Accept or reject a pending request
   - Login as the mentee
   - Check notifications (should see acceptance/rejection notification)

3. **Test Completion:**
   - Login as a mentor
   - Mark an active mentorship as completed
   - Login as the mentee
   - Check notifications (should see completion notification)

## Database
Notifications are stored in the database and can be accessed via:
```python
from notifications.models import Notification

# Get user's notifications
user_notifications = request.user.notifications.all()

# Get unread notifications
unread = request.user.notifications.unread()

# Mark as read
notification.mark_as_read()
```
