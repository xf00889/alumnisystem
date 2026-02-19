# Bulk Export Fix (Mentorship, Donation, and Announcement)

## Issue
When exporting mentorship, donation, or announcement data via the bulk export feature, a 500 Internal Server Error occurred with the following error:

```
django.core.exceptions.FieldError: Invalid field name(s) given in select_related: 'user' or 'author'. 
```

## Root Cause
The issue was caused by incorrect field lookups in the export functionality for multiple models:

### Mentorship Export
1. **In `core/admin_views.py`**: The queryset was using `select_related('mentor__user', 'mentee__user')`, but `mentee` is a direct ForeignKey to `User`, not through another model.

2. **In `core/export_utils.py`**: The export configuration was using `'mentee__user__username'` as a field name, but since `mentee` is directly a ForeignKey to `User`, the correct field name should be `'mentee__username'`.

### Donation Export
1. **In `core/admin_views.py`**: The queryset was using `select_related('donor__user', 'campaign')`, but `donor` is a direct ForeignKey to `User`, not through another model.

2. **In `core/export_utils.py`**: The export configuration was using:
   - `'donor__user__username'` - should be `'donor__username'`
   - `'campaign__title'` - should be `'campaign__name'` (Campaign model has `name` field, not `title`)

### Announcement Export
1. **In `core/admin_views.py`**: The queryset was using `select_related('category', 'author')`, but the Announcement model doesn't have an `author` field.

2. **In `core/export_utils.py`**: The export configuration was using fields that don't exist in the Announcement model:
   - `'author__username'` - Announcement has no author field
   - `'is_published'` - should be `'is_active'`
   - `'created_at'` - should be `'date_posted'`
   - `'updated_at'` - should be `'last_modified'`

## Model Structures

### MentorshipRequest Model
- `mentor`: ForeignKey to `Mentor` model (which has a `user` field)
- `mentee`: ForeignKey to `User` model (direct relationship)

### Donation Model
- `donor`: ForeignKey to `User` model (direct relationship)
- `campaign`: ForeignKey to `Campaign` model

### Announcement Model
- `category`: ForeignKey to `Category` model
- No `author` field
- Has `is_active`, `date_posted`, `last_modified` fields

## Changes Made

### Mentorship Export Fixes

#### 1. Fixed `core/admin_views.py` (Line 391)
**Before:**
```python
queryset = MentorshipRequest.objects.select_related('mentor__user', 'mentee__user').all()
```

**After:**
```python
queryset = MentorshipRequest.objects.select_related('mentor__user', 'mentee').all()
```

#### 2. Fixed `core/admin_views.py` (Line 573)
**Before:**
```python
queryset = MentorshipRequest.objects.select_related('mentor__user', 'mentee__user').all()
```

**After:**
```python
queryset = MentorshipRequest.objects.select_related('mentor__user', 'mentee').all()
```

#### 3. Fixed `core/export_utils.py` (Line 1017)
**Before:**
```python
'field_names': [
    'id', 'mentor__user__username', 'mentee__user__username',
    'status', 'created_at', 'updated_at'
],
```

**After:**
```python
'field_names': [
    'id', 'mentor__user__username', 'mentee__username',
    'status', 'created_at', 'updated_at'
],
```

### Donation Export Fixes

#### 4. Fixed `core/admin_views.py` (Line 416)
**Before:**
```python
queryset = Donation.objects.select_related('donor__user', 'campaign').all()
```

**After:**
```python
queryset = Donation.objects.select_related('donor', 'campaign').all()
```

#### 5. Fixed `core/admin_views.py` (Line 579)
**Before:**
```python
queryset = Donation.objects.select_related('donor__user', 'campaign').all()
```

**After:**
```python
queryset = Donation.objects.select_related('donor', 'campaign').all()
```

#### 6. Fixed `core/export_utils.py` (Line 1046)
**Before:**
```python
'field_names': [
    'id', 'donor__user__username', 'campaign__title', 'amount',
    'status', 'donation_date', 'created_at'
],
```

**After:**
```python
'field_names': [
    'id', 'donor__username', 'campaign__name', 'amount',
    'status', 'donation_date', 'created_at'
],
```

### Announcement Export Fixes

#### 7. Fixed `core/admin_views.py` (Line 440)
**Before:**
```python
queryset = Announcement.objects.select_related('category', 'author').all()
```

**After:**
```python
queryset = Announcement.objects.select_related('category').all()
```

#### 8. Fixed `core/admin_views.py` (Line 582)
**Before:**
```python
queryset = Announcement.objects.select_related('category', 'author').all()
```

**After:**
```python
queryset = Announcement.objects.select_related('category').all()
```

#### 9. Fixed `core/export_utils.py` (Line 1074)
**Before:**
```python
'field_names': [
    'id', 'title', 'content', 'category__name', 'author__username',
    'is_published', 'created_at', 'updated_at'
],
'field_labels': [
    'ID', 'Title', 'Content', 'Category', 'Author',
    'Published', 'Created At', 'Updated At'
],
```

**After:**
```python
'field_names': [
    'id', 'title', 'content', 'category__name', 'priority_level',
    'is_active', 'date_posted', 'last_modified'
],
'field_labels': [
    'ID', 'Title', 'Content', 'Category', 'Priority',
    'Active', 'Date Posted', 'Last Modified'
],
```

## Testing
After the fixes:
- All querysets (mentorship, donation, announcement) execute without errors
- No syntax or diagnostic issues in the modified files
- The export functionality should now work correctly for all three data types

## Impact
This fix resolves the 500 error when exporting mentorship, donation, or announcement data through:
1. Bulk export interface (when selecting any of these models)
2. Direct export endpoints for each model

The fixes ensure proper field lookups based on the actual model relationships and field names.
