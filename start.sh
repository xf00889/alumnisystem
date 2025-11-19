#!/bin/bash

# Startup script for Django on Render
# This script ensures the database is ready before starting the web server

echo "🚀 Starting Django application..."

# Set strict error handling
set -e

# Function to run migrations with retries
run_migrations() {
    echo "📊 Running database migrations..."
    
    # Try to run migrations with retries
    for i in {1..5}; do
        echo "Migration attempt $i/5..."
        if python manage.py migrate --noinput --verbosity=2; then
            echo "✅ Migrations completed successfully"
            return 0
        else
            echo "❌ Migration attempt $i failed"
            if [ $i -lt 5 ]; then
                echo "⏳ Waiting 15 seconds before retry..."
                sleep 15
            fi
        fi
    done
    
    echo "❌ All migration attempts failed"
    echo "🔍 Checking migration status..."
    python manage.py showmigrations --verbosity=2
    return 1
}

# Function to check database connectivity
check_database() {
    echo "🔍 Checking database connectivity..."
    if python manage.py check --database default; then
        echo "✅ Database connection successful"
        return 0
    else
        echo "❌ Database connection failed"
        return 1
    fi
}

# Function to verify critical tables exist
verify_tables() {
    echo "🔍 Verifying critical database tables..."
    
    # Check if django_session table exists
    if python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
if connection.vendor == 'postgresql':
    cursor.execute(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_session');\")
elif connection.vendor == 'mysql':
    cursor.execute(\"SHOW TABLES LIKE 'django_session'\")
else:
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='django_session'\")
result = cursor.fetchone()
if result and (result[0] if connection.vendor == 'postgresql' else result):
    print('django_session table exists')
    exit(0)
else:
    print('django_session table missing')
    exit(1)
"; then
        echo "✅ Critical tables verified"
        return 0
    else
        echo "❌ Critical tables missing"
        return 1
    fi
}

# Function to create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    mkdir -p sessions
    mkdir -p staticfiles
    echo "✅ Directories created"
}

# Main startup sequence
echo "🔄 Starting database initialization..."

# Step 0: Create necessary directories
create_directories

# Step 1: Check database connectivity
if ! check_database; then
    echo "❌ Database not available, exiting..."
    exit 1
fi

# Step 2: Run migrations
if ! run_migrations; then
    echo "❌ Failed to run migrations, exiting..."
    exit 1
fi

# Step 3: Verify tables
if ! verify_tables; then
    echo "❌ Database tables not ready, exiting..."
    exit 1
fi

# Step 4: Ensure CMS data exists
echo "📝 Checking CMS data..."
if python manage.py shell -c "
from cms.models import SiteConfig
if not SiteConfig.objects.exists():
    print('CMS data missing')
    exit(1)
else:
    print('CMS data exists')
    exit(0)
"; then
    echo "✅ CMS data verified"
else
    echo "⚠️ CMS data missing, populating..."
    python manage.py seed_cms_data
    echo "✅ CMS data populated"
fi

# Step 5: Run system checks
echo "🔍 Running system checks..."
if python manage.py check --deploy; then
    echo "✅ System checks passed"
else
    echo "❌ System checks failed"
    exit 1
fi

# Step 5: Start the web server
echo "🌐 Starting Gunicorn web server..."
exec gunicorn norsu_alumni.wsgi:application --bind 0.0.0.0:$PORT
