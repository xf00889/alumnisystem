#!/bin/bash

# Build script for Django on Render
echo "🚀 Starting Django build process..."

# Set strict error handling
set -e

# Create logs directory if it doesn't exist
echo "📂 Creating logs directory..."
mkdir -p logs

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
python manage.py seed_cms_data

# Populate footer links
echo "🔗 Populating footer links..."
python manage.py populate_footer_links

# Populate SEO configuration
echo "🔍 Populating SEO configuration..."
python manage.py seed_seo_data

# Populate announcement categories
echo "📢 Populating announcement categories..."
python manage.py populate_categories

# Populate donation campaign types
echo "💰 Populating donation campaign types..."
python manage.py populate_campaign_types

# Clear reCAPTCHA cache to ensure fresh configuration
echo "🧹 Clearing reCAPTCHA cache..."
python manage.py clear_recaptcha_cache

# Run system checks
echo "🔍 Running system checks..."
python manage.py check --deploy

echo "✅ Build completed successfully!"
