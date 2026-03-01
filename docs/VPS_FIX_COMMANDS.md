# VPS Fix Commands - Run These on Your Server

## Step 1: Pull Latest Code Changes

```bash
cd /var/www/norsualumni
source venv/bin/activate
git pull origin main
```

If you get conflicts, stash your local changes first:
```bash
git stash
git pull origin main
```

## Step 2: Enable Nginx Site Configuration

```bash
# Create symlink to enable the norsualumni site
ln -sf /etc/nginx/sites-available/norsualumni /etc/nginx/sites-enabled/

# Remove the default site
rm /etc/nginx/sites-enabled/default

# Verify Nginx configuration is valid
nginx -t
```

You should see:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

## Step 3: Restart Services

```bash
systemctl restart nginx
systemctl restart gunicorn
```

## Step 4: Test Locally on VPS

```bash
# Test Django directly (should show HTML, not "Bad Request")
curl http://127.0.0.1:8000

# Test through Nginx (should show your site)
curl http://localhost

# Check if services are running
systemctl status nginx
systemctl status gunicorn
```

## Step 5: Test from Your Computer

Open your browser and go to:
```
http://72.62.127.24
```

You should see your Django application!

## If It Still Doesn't Work

### Check Firewall Status

```bash
# Check UFW
ufw status

# Check if port 80 is listening
netstat -tlnp | grep :80

# Check iptables rules
iptables -L -n -v | grep 80
```

### Check Logs

```bash
# Nginx error log
tail -f /var/log/nginx/error.log

# Gunicorn error log
tail -f /var/www/norsualumni/logs/gunicorn_error.log

# System journal for gunicorn
journalctl -u gunicorn -n 50
```

### Verify Nginx Configuration

```bash
# View the enabled sites
ls -la /etc/nginx/sites-enabled/

# View the norsualumni config
cat /etc/nginx/sites-available/norsualumni
```

## Hostinger Firewall Issue

If the site works locally (`curl http://localhost`) but NOT from your browser (`http://72.62.127.24`), the Hostinger firewall is still blocking traffic.

### Contact Hostinger Support

Tell them:
> "I've configured firewall rules for ports 80 and 443 in the Hostinger panel and clicked Synchronize, but external traffic to my VPS (IP: 72.62.127.24) is still being blocked. The services are running correctly on the VPS (verified with curl localhost), but I cannot access the site from external networks. Can you please verify the firewall configuration is active?"

## Quick Status Check

Run this all-in-one command to check everything:

```bash
echo "=== Services Status ===" && \
systemctl is-active nginx gunicorn && \
echo -e "\n=== Port 80 Listening ===" && \
netstat -tlnp | grep :80 && \
echo -e "\n=== Enabled Nginx Sites ===" && \
ls -la /etc/nginx/sites-enabled/ && \
echo -e "\n=== UFW Status ===" && \
ufw status && \
echo -e "\n=== Test Local Access ===" && \
curl -I http://localhost 2>&1 | head -5
```

This will show you the status of all critical components at once.
