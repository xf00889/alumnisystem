# NORSU Alumni System - Render Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the NORSU Alumni System to Render, a modern cloud platform that offers free hosting for web applications.

## Prerequisites
- Git repository with your code
- GitHub, GitLab, or Bitbucket account
- Render account (free)

## Pre-Deployment Checklist

✅ **Files Created/Updated:**
- `Procfile` - Tells Render how to start your app
- `render.yaml` - Deployment configuration
- `requirements.txt` - Updated with production dependencies
- `settings.py` - Configured for production environment

✅ **Dependencies Added:**
- `gunicorn` - WSGI HTTP Server
- `psycopg2-binary` - PostgreSQL adapter
- `whitenoise` - Static file serving
- `dj-database-url` - Database URL parsing

## Step 1: Create a Render Account

1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up using your GitHub, GitLab, or email
4. Verify your email address

## Step 2: Connect Your Repository

1. Push your code to GitHub/GitLab/Bitbucket
2. In Render dashboard, click "New +"
3. Select "Web Service"
4. Connect your Git provider account
5. Select your repository
6. Choose the branch (usually `main` or `master`)

## Step 3: Configure Web Service

### Basic Settings:
- **Name:** `norsu-alumni-system` (or your preferred name)
- **Environment:** `Python 3`
- **Region:** Choose closest to your users
- **Branch:** `main` (or your default branch)
- **Build Command:** 
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  ```
- **Start Command:** 
  ```bash
  gunicorn norsu_alumni.wsgi:application
  ```

### Environment Variables:
Add these in the "Environment" section:

**Required:**
```
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/database
RENDER_EXTERNAL_HOSTNAME=your-app-name.onrender.com
SITE_URL=https://your-app-name.onrender.com
```

**Optional (for email functionality):**
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Optional (for AWS S3 static files):**
```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## Step 4: Create PostgreSQL Database

1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Configure:
   - **Name:** `norsu-alumni-db`
   - **Database:** `norsu_alumni`
   - **User:** `norsu_alumni_user`
   - **Region:** Same as your web service
   - **Plan:** Free
4. Click "Create Database"
5. Copy the "External Database URL" from the database info page
6. Add it as `DATABASE_URL` in your web service environment variables

## Step 5: Deploy Your Application

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Run database migrations
   - Collect static files
   - Start your application

3. Monitor the build logs for any errors
4. Once deployed, your app will be available at: `https://your-app-name.onrender.com`

## Step 6: Run Initial Setup

### Create Superuser (via Render Shell):
1. Go to your web service dashboard
2. Click "Shell" tab
3. Run:
   ```bash
   python manage.py createsuperuser
   ```

### Load Initial Data (if needed):
```bash
python manage.py loaddata your_fixture_file.json
```

## Step 7: Configure Custom Domain (Optional)

1. In your web service settings
2. Go to "Custom Domains"
3. Add your domain
4. Update DNS records as instructed
5. Update `RENDER_EXTERNAL_HOSTNAME` environment variable

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|----------|
| `DEBUG` | Debug mode | Yes | `False` |
| `SECRET_KEY` | Django secret key | Yes | `your-secret-key` |
| `DATABASE_URL` | PostgreSQL connection | Yes | `postgresql://user:pass@host/db` |
| `RENDER_EXTERNAL_HOSTNAME` | Your Render domain | Yes | `myapp.onrender.com` |
| `SITE_URL` | Full site URL | Yes | `https://myapp.onrender.com` |
| `REDIS_URL` | Redis connection (optional) | No | `redis://host:port` |
| `EMAIL_HOST` | SMTP server | No | `smtp.gmail.com` |
| `EMAIL_HOST_USER` | Email username | No | `user@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Email password | No | `app-password` |

## Post-Deployment Tasks

1. **Test all functionality:**
   - User registration/login
   - Admin panel access
   - Static files loading
   - Database operations

2. **Set up monitoring:**
   - Enable Render's built-in monitoring
   - Set up error tracking (Sentry, etc.)

3. **Configure backups:**
   - Set up database backups
   - Export important data regularly

4. **Security checklist:**
   - Verify HTTPS is working
   - Check CSRF protection
   - Review allowed hosts
   - Test rate limiting

## Updating Your Application

1. Push changes to your Git repository
2. Render will automatically detect changes and redeploy
3. Monitor deployment logs
4. Test the updated application

## Manual Deployment Trigger

If auto-deploy is disabled:
1. Go to your web service dashboard
2. Click "Manual Deploy"
3. Select branch and click "Deploy"

## Next Steps

- Review the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Set up monitoring and alerts
- Configure custom domain
- Implement CI/CD pipeline
- Set up staging environment

---

**Need Help?**
- Check the troubleshooting guide
- Review Render documentation
- Check application logs in Render dashboard
- Contact support if needed
