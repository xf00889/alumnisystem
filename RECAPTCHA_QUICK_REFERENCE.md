# reCAPTCHA v3 - Quick Reference Card

## ✅ Conversion Complete

Login and signup forms now use reCAPTCHA v3 (invisible verification).

## 🔑 Get v3 Keys

1. Visit: https://www.google.com/recaptcha/admin
2. Click "+" to register new site
3. Select "reCAPTCHA v3"
4. Add your domain(s)
5. Copy Site Key and Secret Key

## ⚙️ Configure in Database

**Admin Panel > Core > ReCaptcha Configs**

```
Site Key: [Your v3 site key]
Secret Key: [Your v3 secret key]
Version: v3
Threshold: 0.5
Enabled: ✅ True
```

## 🚀 Deploy

1. Push code to repository
2. Deploy to hosting
3. **Important:** Clear cache
   ```bash
   python manage.py clear_recaptcha_cache
   ```
4. Test login and signup

## 🧪 Quick Test

1. Go to `/accounts/login/`
2. Open browser console (F12)
3. Try to login
4. Check for errors
5. Verify form submits

## ❌ Troubleshooting

| Error | Solution |
|-------|----------|
| "Missing required parameters: sitekey" | Clear cache, restart server |
| "Invalid key type" | Generate new v3 keys |
| Forms don't submit | Check console for JS errors |
| Works locally, not on hosting | Clear cache on hosting |

## 📊 Monitoring

Check backend logs for:
```
INFO: reCAPTCHA validation successful, score: 0.9
WARNING: reCAPTCHA score below threshold: 0.3 < 0.5
```

## 🎯 Threshold Guide

- **0.0 - 0.3**: Likely bot
- **0.3 - 0.7**: Suspicious
- **0.7 - 1.0**: Likely human

**Recommended starting point**: 0.5

## 🔧 Emergency Disable

Add to `.env`:
```
DISABLE_RECAPTCHA=True
```

## 📝 Key Differences: v2 vs v3

| Feature | v2 | v3 |
|---------|----|----|
| User interaction | Checkbox | None (invisible) |
| Verification | Pass/Fail | Score (0.0-1.0) |
| User experience | Extra click | Seamless |
| Bot detection | Challenge-based | Behavior-based |

## ✨ Benefits of v3

- ✅ No user interaction required
- ✅ Better user experience
- ✅ More accurate bot detection
- ✅ Behavior-based scoring
- ✅ Works on mobile devices

## 📚 Documentation Files

1. `RECAPTCHA_V3_CONVERSION_COMPLETE.md` - Technical details
2. `RECAPTCHA_V3_TESTING_GUIDE.md` - Testing instructions
3. `RECAPTCHA_V3_DEPLOYMENT_READY.md` - Deployment guide
4. `RECAPTCHA_QUICK_REFERENCE.md` - This file

## 🆘 Need Help?

1. Check browser console for errors
2. Check backend logs
3. Verify database configuration
4. Clear cache and restart
5. Test with reCAPTCHA disabled

---

**Status**: ✅ Ready for deployment
**Last Updated**: February 17, 2026
