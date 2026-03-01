# SSL Certificate Setup Guide

## Current Status

✅ DNS configured for norsualumni.com (www and @)
⏳ Waiting for DNS propagation (currently still pointing to old IP)
❓ alumninorsu.com - needs DNS configuration if you want to use it

## Step 1: Wait for DNS Propagation

Check if DNS is ready by running this from your computer:

```powershell
nslookup norsualumni.com
nslookup www.norsualumni.com
```

Both should return: `72.62.127.24`

Currently showing: `216.24.57.1` (old Render IP)

**Typical propagation time:** 5 minutes to 48 hours (usually within 1-2 hours)

## Step 2: Update Nginx Configuration

Once DNS is propagating, SSH into your VPS and update Nginx:

```bash
# Edit Nginx config
nano /etc/nginx/sites-available/norsualumni
```

Update the `server_name` line to include all your domains:

```nginx
server {
    listen 80;
    server_name norsualumni.com www.norsualumni.com 72.62.127.24;
    
    # If you configured alumninorsu.com DNS, add it too:
    # server_name norsualumni.com www.norsualumni.com alumninorsu.com www.alumninorsu.com 72.62.127.24;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /static/ {
        alias /var/www/norsualumni/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/norsualumni/media/;
        expires 30d;
        add_header Cache-Control "public";
    }
}
```

Test and reload Nginx:

```bash
nginx -t
systemctl reload nginx
```

## Step 3: Test Domain Access

Try accessing your domain via HTTP:

```bash
curl http://norsualumni.com
curl http://www.norsualumni.com
```

Both should return your Django site HTML.

From your browser, visit:
- http://norsualumni.com
- http://www.norsualumni.com

Both should show your site.

## Step 4: Install SSL Certificates

Once your domains are accessible via HTTP, install Let's Encrypt SSL:

```bash
# Install certbot (if not already installed)
apt install -y certbot python3-certbot-nginx

# Get SSL certificates
# For norsualumni.com only:
certbot --nginx -d norsualumni.com -d www.norsualumni.com

# OR if you configured alumninorsu.com DNS too:
# certbot --nginx -d norsualumni.com -d www.norsualumni.com -d alumninorsu.com -d www.alumninorsu.com
```

Follow the prompts:
1. Enter your email address (for renewal notifications)
2. Agree to Terms of Service (Y)
3. Share email with EFF (optional - Y or N)
4. Choose option 2: Redirect HTTP to HTTPS

Certbot will:
- ✅ Generate free SSL certificates
- ✅ Update Nginx configuration automatically
- ✅ Set up auto-renewal (certificates renew every 90 days)

## Step 5: Verify SSL is Working

After certbot completes, test your site:

```bash
# From VPS
curl https://norsualumni.com
curl https://www.norsualumni.com
```

From your browser:
- https://norsualumni.com
- https://www.norsualumni.com

You should see:
- ✅ Padlock icon in browser
- ✅ "Connection is secure"
- ✅ HTTP automatically redirects to HTTPS

## Step 6: Enable Django SSL Redirect

Update your `.env` file:

```bash
nano /var/www/norsualumni/.env
```

Change this line:
```
SECURE_SSL_REDIRECT=True
```

Restart Gunicorn:
```bash
systemctl restart gunicorn
```

## Step 7: Update Google OAuth

Go to [Google Cloud Console](https://console.cloud.google.com/):

1. Select your project
2. Go to "APIs & Services" > "Credentials"
3. Click on your OAuth 2.0 Client ID
4. Under "Authorized redirect URIs", add:
   - `https://norsualumni.com/accounts/google/login/callback/`
   - `https://www.norsualumni.com/accounts/google/login/callback/`
   
   (Add alumninorsu.com URIs too if you configured that domain)

5. Click "Save"

## Step 8: Test Everything

Test these features:
- ✅ Site loads on HTTPS
- ✅ HTTP redirects to HTTPS
- ✅ Google OAuth login works
- ✅ Static files load correctly
- ✅ Media files load correctly
- ✅ Admin panel accessible

## Troubleshooting

### DNS Not Propagating
If DNS still shows old IP after 2 hours:
- Clear your DNS cache: `ipconfig /flushdns` (Windows)
- Try a different DNS server: `nslookup norsualumni.com 8.8.8.8`
- Check DNS propagation: https://dnschecker.org

### Certbot Fails
If certbot can't verify domain:
- Make sure domain resolves to your VPS IP
- Check Nginx is serving on port 80
- Verify firewall allows port 80
- Try: `certbot certonly --webroot -w /var/www/norsualumni/staticfiles -d norsualumni.com -d www.norsualumni.com`

### SSL Certificate Renewal
Certificates auto-renew. To test renewal:
```bash
certbot renew --dry-run
```

To manually renew:
```bash
certbot renew
systemctl reload nginx
```

## Quick Status Check

Run this to verify everything:

```bash
echo "=== DNS Check ===" && \
nslookup norsualumni.com && \
echo -e "\n=== Nginx Config Test ===" && \
nginx -t && \
echo -e "\n=== Services Status ===" && \
systemctl is-active nginx gunicorn && \
echo -e "\n=== SSL Certificates ===" && \
certbot certificates && \
echo -e "\n=== Test HTTPS ===" && \
curl -I https://norsualumni.com 2>&1 | head -5
```

## Timeline

- **Now:** DNS configured, waiting for propagation
- **1-2 hours:** DNS should propagate
- **+10 minutes:** Install SSL certificates
- **+5 minutes:** Configure Django and Google OAuth
- **Total:** ~2-3 hours from now

## Next Steps

1. ⏳ Wait for DNS propagation (check every 30 minutes)
2. ✅ Once DNS shows 72.62.127.24, proceed with SSL installation
3. ✅ Update Google OAuth settings
4. ✅ Test everything works
5. 🎉 Your site is live with HTTPS!
