#!/bin/bash

# Deploy Static File Changes Script
# Run this after pulling CSS/JS changes from Git

echo "=========================================="
echo "Deploying Static File Changes"
echo "=========================================="
echo ""

# Step 1: Collect static files
echo "[1/3] Collecting static files..."
python manage.py collectstatic --noinput --clear

if [ $? -eq 0 ]; then
    echo "✓ Static files collected successfully"
else
    echo "✗ Error collecting static files"
    exit 1
fi

echo ""

# Step 2: Clear Django cache (if using cache)
echo "[2/3] Clearing Django cache..."
python manage.py shell << EOF
from django.core.cache import cache
cache.clear()
print("✓ Cache cleared")
EOF

echo ""

# Step 3: Restart the application
echo "[3/3] Restarting application..."
echo "Please restart your application server manually:"
echo ""
echo "For Gunicorn:"
echo "  sudo systemctl restart gunicorn"
echo "  OR"
echo "  pkill -HUP gunicorn"
echo ""
echo "For Supervisor:"
echo "  sudo supervisorctl restart all"
echo ""
echo "For Hostinger (if using their panel):"
echo "  Restart from the hosting control panel"
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "If changes still don't appear:"
echo "1. Hard refresh browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)"
echo "2. Clear browser cache"
echo "3. Check browser console for errors (F12)"
echo "4. Verify file permissions: ls -la staticfiles/css/"
echo ""
