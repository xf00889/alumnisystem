#!/usr/bin/env python3
# Script to remove duration field from mentor_dashboard.html forms

with open('templates/mentorship/mentor_dashboard.html', 'r', encoding='utf-8') as file:
    content = file.read()

# Second, remove it from the scheduleMeetingModal
start_str = '<div class="mb-3">\n                        <label for="meetingDuration" class="form-label">Duration (minutes)</label>\n                        <input type="number" class="form-control" id="meetingDuration" name="duration" value="30" min="15" max="180" required>\n                    </div>'
if start_str in content:
    content = content.replace(start_str, '')
    print("Removed duration field from scheduleMeetingModal")
else:
    print("Couldn't find duration field with exact match")

with open('templates/mentorship/mentor_dashboard.html', 'w', encoding='utf-8') as file:
    file.write(content)
    print("File saved successfully") 