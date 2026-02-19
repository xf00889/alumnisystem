# How to Set SECRET_KEY on Render.com

## Quick Steps (5 minutes)

### Step 1: Generate a Strong Secret Key

Run this command on your local machine:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Example output** (yours will be different):
```
7k#9m@x$2p!q8w&e5r^t6y*u1i(o0p-a_s+d=f[g]h{j}k|l:z;x<c>v,b.n/m
```

**Copy this entire string!** You'll need it in the next step.

### Step 2: Add to Render Environment Variables

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Log in to your account

2. **Select Your Service**
   - Click on your "alumnisystem" service
   - (The one deployed from your Git repository)

3. **Go to Environment Tab**
   - Click "Environment" in the left sidebar
   - You'll see your existing environment variables

4. **Add SECRET_KEY**
   - Click "Add Environment Variable" button
   - **Key**: `SECRET_KEY`
   - **Value**: Paste the generated key from Step 1
   - Click "Save Changes"

5. **Wait for Auto-Deploy**
   - Render will automatically redeploy (5-10 minutes)
   - Watch the "Events" tab for progress

### Step 3: Verify

After deployment completes:

1. **Check Logs**
   - Go to "Logs" tab in Render
   - Look for: "System check identified no issues"
   - Should see no SECRET_KEY warnings

2. **Test Your Site**
   - Visit: https://alumnisystem-6c7s.onrender.com
   - Everything should work normally
   - Site is now fully secure! ✅

## Visual Guide

```
Render Dashboard
    ↓
Select "alumnisystem" service
    ↓
Click "Environment" tab
    ↓
Click "Add Environment Variable"
    ↓
Key: SECRET_KEY
Value: <paste your generated key>
    ↓
Click "Save Changes"
    ↓
Wait for auto-deploy (5-10 min)
    ↓
Done! ✅
```

## Important Notes

### ⚠️ Keep Your SECRET_KEY Secret!
- **Never** commit it to Git
- **Never** share it publicly
- **Never** post it in forums/chat
- Store it only in Render environment variables

### ✅ What Happens After Setting It
- All security warnings disappear
- Django security features fully activated
- Sessions become more secure
- CSRF protection strengthened

### 🔄 If You Need to Change It
1. Generate a new key (same command)
2. Update in Render environment variables
3. Render auto-deploys
4. **Note**: All users will be logged out (sessions invalidated)

## Troubleshooting

### Problem: Can't find Environment tab
**Solution**: Make sure you're viewing your web service, not a database or other resource.

### Problem: Changes not taking effect
**Solution**: 
1. Check "Events" tab - deployment should be in progress
2. Wait for "Live" status
3. Clear browser cache and reload

### Problem: Site breaks after setting SECRET_KEY
**Solution**: 
1. Check the key was copied correctly (no extra spaces)
2. Check Render logs for errors
3. If needed, revert by removing the variable

## Other Environment Variables to Check

While you're in the Environment tab, verify these are set:

| Variable | Should Be | Purpose |
|----------|-----------|---------|
| `DEBUG` | `False` | Production mode |
| `SECRET_KEY` | `<your-key>` | Security |
| `DATABASE_URL` | `<auto-set>` | Database connection |
| `REDIS_URL` | `<auto-set>` | Cache/sessions |
| `ALLOWED_HOSTS` | `alumnisystem-6c7s.onrender.com` | Allowed domains |

## After Setting SECRET_KEY

Your security checklist:

- [x] XSS protection (from messaging fixes)
- [x] File upload validation (from messaging fixes)
- [x] Rate limiting (from messaging fixes)
- [x] HTTPS enforced (DEBUG=False)
- [x] Secure cookies (DEBUG=False)
- [x] HSTS enabled (DEBUG=False)
- [x] Strong SECRET_KEY (just set!)
- [x] Content-Type protection (DEBUG=False)
- [x] Clickjacking protection (DEBUG=False)

**Result**: 🔒 Fully Secure Production Site!

## Quick Reference

### Generate Key
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Render Dashboard
https://dashboard.render.com

### Your Service
alumnisystem-6c7s.onrender.com

### Time Required
- Generate key: 30 seconds
- Add to Render: 2 minutes
- Auto-deploy: 5-10 minutes
- **Total**: ~15 minutes

## Need Help?

If you run into issues:
1. Check Render logs for error messages
2. Verify the SECRET_KEY was copied correctly
3. Ensure no extra spaces or characters
4. Try generating a new key and setting it again

---

**Status**: One final step to complete security setup!
**Time**: 5 minutes
**Difficulty**: Easy
**Impact**: High security improvement
