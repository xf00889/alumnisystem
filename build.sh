#!/bin/bash

# Build script for Django on Render
echo "🚀 Starting Django build process..."

# Set strict error handling
set -e

# Function to run command with error handling
run_command() {
    local description=$1
    local command=$2
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "$description"
    echo "═══════════════════════════════════════════════════════════"
    
    if eval "$command"; then
        echo "✅ SUCCESS: $description"
    else
        echo "❌ FAILED: $description"
        echo "Command: $command"
        exit 1
    fi
}

# Create logs directory if it doesn't exist
run_command "📂 Creating logs directory" "mkdir -p logs"

# Install dependencies
run_command "📦 Installing Python dependencies" "pip install -r requirements.txt"

# Collect static files
run_command "📁 Collecting static files" "python manage.py collectstatic --noinput"

# Run migrations
run_command "🗄️ Running database migrations" "python manage.py migrate --noinput"

# Populate CMS data
run_command "📝 Populating CMS data" "python manage.py seed_cms_data"

# Populate footer links
run_command "🔗 Populating footer links" "python manage.py populate_footer_links"

# Populate SEO configuration
run_command "🔍 Populating SEO configuration" "python manage.py seed_seo_data"

# Populate announcement categories
run_command "📢 Populating announcement categories" "python manage.py populate_categories"

# Populate donation campaign types
run_command "💰 Populating donation campaign types" "python manage.py populate_campaign_types"

# Clear reCAPTCHA cache to ensure fresh configuration
run_command "🧹 Clearing reCAPTCHA cache" "python manage.py clear_recaptcha_cache"

# Run system checks
run_command "🔍 Running system checks" "python manage.py check --deploy"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Build completed successfully!"
echo "═══════════════════════════════════════════════════════════"
