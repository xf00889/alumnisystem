# Donation Upload Debugging Guide

## Changes Made

### 1. Fixed PaymentProofForm (donations/forms.py)
- **Issue**: Duplicate `__init__` method
- **Fix**: Removed duplicate, kept single `__init__` method
- **Location**: Line 266-270

### 2. Added Debug Logging (donations/views.py)
- **Added comprehensive logging to `upload_payment_proof` view**:
  - Donation ID and status
  - POST data and FILES data
  - User authentication status
  - Form validation results
  - Form errors (if any)
  - Save confirmation

### 3. Template Debug Logging (upload_payment_proof_minimal.html)
- **Added console logging**:
  - Form submit event
  - Form validity
  - Form data

## How to Debug

### Step 1: Try Uploading Payment Proof
1. Go to: `http://127.0.0.1:8000/donations/upload-proof/<donation_id>/`
2. Select a payment screenshot file
3. Fill in optional transaction ID
4. Click "Upload Payment Proof"

### Step 2: Check Browser Console
Open Developer Tools (F12) and check Console tab for:
- "Form submit event triggered"
- "Form validity: true/false"
- Any JavaScript errors

### Step 3: Check Server Terminal Logs
Look for the debug output that starts with:
```
=== UPLOAD PAYMENT PROOF DEBUG ===
```

This will show you:
- Whether the POST request is reaching the server
- What data is being sent
- Whether the form is valid
- Any validation errors
- Whether the donation is being saved

### Step 4: Common Issues to Check

#### Issue 1: Form Not Submitting
**Symptoms**: No logs in terminal, no console logs
**Possible Causes**:
- JavaScript error preventing submission
- Missing form fields
- Browser blocking submission

**Solution**: Check browser console for errors

#### Issue 2: Form Invalid
**Symptoms**: "Form is valid: False" in logs
**Possible Causes**:
- Required field missing
- File validation error
- File size too large (>5MB)
- Wrong file type

**Solution**: Check "Form errors:" in the logs

#### Issue 3: File Not Saving
**Symptoms**: "Form is valid: True" but file not in database
**Possible Causes**:
- Media directory permissions
- File upload settings in settings.py
- Model save() error

**Solution**: Check "Donation after save:" in logs

#### Issue 4: Permission Error
**Symptoms**: Redirect to campaign list
**Possible Causes**:
- Session email not matching donation email
- Donation older than 1 hour

**Solution**: Check session email vs donation email in logs

## What to Look For

1. **In Browser Console**:
   ```
   Form submit event triggered
   Form validity: true
   Form data: FormData {}
   Form is valid, showing loading state
   ```

2. **In Server Logs**:
   ```
   === UPLOAD PAYMENT PROOF DEBUG ===
   Donation ID: XX
   Donation status: pending_payment
   POST data: {...}
   FILES data: {'payment_proof': [<UploadedFile>]}
   User authenticated: False
   Form is valid: True
   Form is valid, saving donation...
   Donation before save: status=pending_payment, payment_proof=payment_proofs/XXX.jpg
   Donation after save: status=pending_verification, payment_proof=payment_proofs/XXX.jpg
   Donation saved successfully with ID: XX
   ```

## Next Steps

If you see errors in the logs, please share them so I can help fix the specific issue.

Common error patterns:
- **"Form errors:"** - Shows which fields are invalid
- **"Session donor_email:"** - Shows if permission check is failing
- **"Exception:"** - Shows if there's a Python error

## Testing Checklist

- [ ] Browser console shows form submission
- [ ] Server logs show POST request received
- [ ] Form validation passes (Form is valid: True)
- [ ] Donation saves successfully
- [ ] Redirects to confirmation page
- [ ] Payment proof appears in admin/database


