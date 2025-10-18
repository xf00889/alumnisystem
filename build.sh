#!/bin/bash

# Build script for Django on Render
echo "🚀 Starting Django build process..."

# Set strict error handling
set -e

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Populate CMS data
echo "📝 Populating CMS data..."
python manage.py populate_cms_data

# Run system checks
echo "🔍 Running system checks..."
python manage.py check --deploy

echo "✅ Build completed successfully!"
