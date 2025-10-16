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
        if python manage.py migrate --noinput; then
            echo "✅ Migrations completed successfully"
            return 0
        else
            echo "❌ Migration attempt $i failed"
            if [ $i -lt 5 ]; then
                echo "⏳ Waiting 10 seconds before retry..."
                sleep 10
            fi
        fi
    done
    
    echo "❌ All migration attempts failed"
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

# Main startup sequence
echo "🔄 Starting database initialization..."

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

# Step 4: Run system checks
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
