# Hostinger VPS Deployment Status

## ✅ Completed Steps

1. **System Setup**
   - ✅ Ubuntu 24.04 installed
   - ✅ Python 3.12 installed
   - ✅ PostgreSQL database created and configured
   - ✅ Redis installed and running
   - ✅ Nginx installed
   - ✅ UFW firewall configured (ports 22, 80, 443 open)

2. **Application Setup**
   - ✅ Project cloned from GitHub
   - ✅ Virtual environment created
   - ✅ Python dependencies installed (except mysqlclient - not needed for production)
   - ✅ Gunicorn and Daphne installed
   - ✅ Database migrations completed
   - ✅ Superuser created
   - ✅ Static files collected
   - ✅ .env file configured

3. **Services Configuration**
   - ✅ Gunicorn systemd service created and running
   - ✅ Daphne systemd service created and running
   - ✅ Nginx configuration created
   - ✅ Services set to auto-start on boot

4. **Code Updates**
   - ✅ Updated settings.py to make SECURE_SSL_REDIRECT configurable via environment variable

## ⚠️ Current Issue: Nginx Configuration Not Enabled

### Problem
The Nginx configuration for norsualumni is created but not enabled. The `sites-enabled` directory only has the `default` site.

### Evidence
```bash
# Only default site is enabled:
ls -la /etc/nginx/sites-enabled/
# Shows: default -> /etc/nginx/sites-available/default

# Django responds but returns 400 Bad Request (ALLOWED_HOSTS issue):
curl http://127.0.0.1:8000  # Returns "Bad Request (400)"

# Nginx shows default page:
curl http://localhost  # Returns Nginx default page or redirects to HTTPS
```

### Root Causes
1. **Nginx configuration not enabled** - The norsualumni site config exists but isn't symlinked to sites-enabled
2. **ALLOWED_HOSTS missing VPS IP and domains** - Django rejects requests from 127.0.0.1 and external IPs
3. **Hostinger firewall may still be blocking** - Even after synchronization, external access times out

### Fixes Applied (Local - Need to Push to GitHub)
1. ✅ Updated `ALLOWED_HOSTS` to include VPS IP and all domains
2. ✅ Updated `CSRF_TRUSTED_ORIGINS` to include all HTTP/HTTPS variants

### What's Needed on VPS
After pushing the code changes to GitHub, run these commands on the VPS:

```bash
# 1. Pull the latest code
cd /var/www/norsualumni
git pull origin main

# 2. Enable the norsualumni Nginx site
ln -sf /etc/nginx/sites-available/norsualumni /etc/nginx/sites-enabled/

# 3. Disable the default site
rm /etc/nginx/sites-enabled/default

# 4. Test Nginx configuration
nginx -t

# 5. Restart services
systemctl restart nginx
systemctl restart gunicorn

# 6. Test locally
curl http://127.0.0.1
curl http://localhost
```

### Hostinger Firewall
The firewall rules have been synchronized but may need additional time or support contact if external access still doesn't work after the above fixes.

---

## 🔧 Next Steps (Once Firewall is Fixed)

### 1. Verify Site Works on HTTP
Once the firewall allows traffic:
```bash
# Test from your browser
http://72.62.127.24
```

You should see your Django application!

### 2. Point Your Domains
Update DNS records at your domain registrar:

**For norsualumni.com:**
```
Type: A
Name: @
Value: 72.62.127.24
TTL: 3600
```

```
Type: A
Name: www
Value: 72.62.127.24
TTL: 3600
```

**For alumninorsu.com:**
```
Type: A
Name: @
Value: 72.62.127.24
TTL: 3600
```

```
Type: A
Name: www
Value: 72.62.127.24
TTL: 3600
```

Wait 5 minutes to 48 hours for DNS propagation.

### 3. Install SSL Certificates (Free from Let's Encrypt)

Once your domain is accessible via HTTP:

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get SSL certificates
certbot --nginx -d www.norsualumni.com -d norsualumni.com -d alumninorsu.com -d www.alumninorsu.com
```

Follow the prompts:
- Enter your email
- Agree to terms
- Choose option 2 (Redirect HTTP to HTTPS)

### 4. Enable SSL Redirect in Django

Update your .env file:
```env
SECURE_SSL_REDIRECT=True
```

Restart Gunicorn:
```bash
systemctl restart gunicorn
```

### 5. Update Google OAuth Redirect URIs

Go to [Google Cloud Console](https://console.cloud.google.com/):
1. Select your project
2. Go to "APIs & Services" > "Credentials"
3. Edit your OAuth 2.0 Client ID
4. Add Authorized redirect URIs:
   - `https://www.norsualumni.com/accounts/google/login/callback/`
   - `https://norsualumni.com/accounts/google/login/callback/`
   - `https://alumninorsu.com/accounts/google/login/callback/`
   - `https://www.alumninorsu.com/accounts/google/login/callback/`

---

## 📋 Configuration Files

### VPS IP Address
```
72.62.127.24
```

### Database Credentials
```
Database: alumni_norsu
User: alumni_user
Password: NorsuAlumni2024!Strong
Host: localhost
Port: 5432
```

### Service Status Commands
```bash
# Check services
systemctl status gunicorn
systemctl status daphne
systemctl status nginx
systemctl status postgresql
systemctl status redis-server

# Restart services
systemctl restart gunicorn
systemctl restart daphne
systemctl restart nginx

# View logs
tail -f /var/www/norsualumni/logs/gunicorn_error.log
tail -f /var/log/nginx/error.log
journalctl -u gunicorn -n 50
```

### Update Application
```bash
cd /var/www/norsualumni
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn daphne
```

---

## 🆘 Troubleshooting

### If site still doesn't work after firewall fix:

1. **Check if services are running:**
   ```bash
   systemctl status nginx gunicorn
   ```

2. **Check if port 80 is listening:**
   ```bash
   netstat -tlnp | grep :80
   ```

3. **Test locally on VPS:**
   ```bash
   curl http://127.0.0.1
   ```

4. **Check Nginx logs:**
   ```bash
   tail -f /var/log/nginx/error.log
   ```

5. **Check Gunicorn logs:**
   ```bash
   tail -f /var/www/norsualumni/logs/gunicorn_error.log
   ```

### Contact Hostinger Support

If the firewall rules don't work after 30 minutes, contact Hostinger support:
- Tell them: "I've added firewall rules for ports 80 and 443 but external traffic is still blocked"
- Provide your VPS IP: 72.62.127.24
- Ask them to verify the firewall configuration

---

## ✨ Final Result

Once everything is working, your site will be accessible at:
- https://www.norsualumni.com (primary)
- https://norsualumni.com
- https://alumninorsu.com
- https://www.alumninorsu.com

All with:
- ✅ Free SSL certificates (auto-renewing)
- ✅ HTTPS encryption
- ✅ Professional domain names
- ✅ Full Django application functionality
- ✅ 24/7 uptime

---

## 📞 Support

If you need help:
1. Check the logs (commands above)
2. Review this document
3. Contact Hostinger support for firewall issues
4. Check the deployment guides in `docs/` folder
