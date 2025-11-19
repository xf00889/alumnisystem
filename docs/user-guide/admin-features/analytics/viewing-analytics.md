# Viewing Analytics

## Overview

The Admin Dashboard provides comprehensive analytics and statistics about your alumni system. This centralized view gives you insights into user activity, donations, events, jobs, mentorships, surveys, and more.

## Who Can Use This Feature

- **Admin Users**: Full access to all analytics and statistics
- **Staff Users**: Access to view analytics data

## Prerequisites

- Admin or staff account with appropriate permissions
- Active alumni system with data to analyze

## How to Access

1. Log in to your admin account
2. Click on **Admin Dashboard** in the navigation menu
3. Or navigate directly to: `/admin-dashboard/`

The dashboard will load automatically with the latest statistics.

## Key Features

### Real-Time Statistics

The dashboard displays key metrics across multiple categories:

#### User & Alumni Statistics
- **Total Users**: Total number of registered users in the system
- **Active Users**: Users who have logged in within the last 30 days
- **New Users This Month**: Number of users registered in the current month
- **Total Alumni**: Total number of alumni profiles
- **Verified Alumni**: Number of verified alumni accounts

#### Activity Statistics
- **Total Events**: All events in the system
- **Upcoming Events**: Events scheduled for the future
- **Total RSVPs**: Number of event registrations
- **Job Postings**: Total and active job listings
- **Job Applications**: Total number of applications received
- **Active Mentorships**: Currently active mentorship relationships
- **Pending Mentorship Requests**: Requests awaiting approval

#### Financial Statistics
- **Total Donations**: Sum of all completed donations
- **Donation Count**: Number of individual donations
- **Active Campaigns**: Currently running donation campaigns

#### Engagement Statistics
- **Total Surveys**: All surveys created
- **Active Surveys**: Currently open surveys
- **Survey Responses**: Total responses received
- **Total Feedback**: All feedback submissions
- **Pending Feedback**: Feedback awaiting review
- **Total Announcements**: All announcements published

## Step-by-Step Guide

### Task 1: View Dashboard Overview

1. **Access the Dashboard**
   - Navigate to the Admin Dashboard from the main menu
   - The page will load with all current statistics

2. **Review Key Metrics**
   - Scroll through the metric cards at the top of the page
   - Each card shows a primary metric with additional context
   - Hover over cards for additional information

3. **Understand Color Coding**
   - **Blue (Primary)**: User and event statistics
   - **Green (Success)**: Active users and job postings
   - **Light Blue (Info)**: Alumni and mentorship data
   - **Orange (Warning)**: Financial and survey data

### Task 2: Analyze Trends with Time Periods

1. **Select Time Period**
   - At the top of the dashboard, you'll see time period buttons
   - Available options: **7 Days**, **30 Days**, **90 Days**
   - Click on a time period to update the analytics

2. **View Updated Data**
   - Charts and graphs will automatically refresh
   - Recent activity sections will update based on the selected period

### Task 3: View User Registration Trends

1. **Locate the Chart**
   - Scroll down to the "User Registration Trends" section
   - This chart shows user registrations over time

2. **Interpret the Data**
   - The line graph displays daily registration counts
   - Hover over data points to see exact numbers
   - Use this to identify registration patterns and trends

3. **Analyze Patterns**
   - Look for spikes in registrations (may correlate with events or campaigns)
   - Identify slow periods that may need attention
   - Compare different time periods using the time selector

### Task 4: View Alumni Distribution

1. **Alumni by College**
   - View the distribution of alumni across different colleges
   - Data is displayed in a table format with counts
   - Helps identify which colleges have the most alumni representation

2. **Alumni by Graduation Year**
   - See the breakdown of alumni by their graduation year
   - Useful for understanding the age distribution of your network
   - Identify which batches are most active

### Task 5: Monitor Recent Activity

1. **Recent Users**
   - View the 5 most recently registered users
   - See their registration date and basic information
   - Quick way to monitor new member growth

2. **Recent Donations**
   - Track the latest donations received
   - See donor information and campaign details
   - Monitor donation amounts and frequency

3. **Recent Events**
   - View recently created events
   - See event details and creation dates
   - Track event creation activity

### Task 6: Access Detailed Analytics

1. **Navigate to Specific Sections**
   - Use the dashboard as a starting point
   - Click on specific metrics to drill down into details
   - Access dedicated management pages for each feature

2. **Export Data**
   - Scroll to the "Data Export" section
   - Select the data type you want to export
   - Choose format (CSV, Excel, or PDF)
   - Click the export button to download

## Understanding the Dashboard Layout

### Top Section: Key Metrics
- Grid of metric cards showing the most important statistics
- Color-coded for easy identification
- Updates in real-time

### Middle Section: Charts and Graphs
- Visual representations of trends over time
- Interactive charts that respond to time period selection
- Includes user registrations, donations, RSVPs, and applications

### Bottom Section: Recent Activity
- Lists of recent actions in the system
- Quick overview of what's happening
- Links to detailed views

### Export Section
- Tools for exporting data
- Multiple format options
- Bulk export capabilities

## Tips and Best Practices

### Regular Monitoring
- Check the dashboard daily to stay informed
- Look for unusual patterns or anomalies
- Use trends to inform decision-making

### Time Period Selection
- Use 7-day view for immediate insights
- Use 30-day view for monthly reporting
- Use 90-day view for quarterly analysis

### Data Interpretation
- Compare metrics across different time periods
- Look for correlations between different metrics
- Use data to identify areas needing attention

### Performance Tracking
- Monitor user growth trends
- Track engagement metrics (RSVPs, applications, responses)
- Measure campaign effectiveness through donation data

### Exporting Data
- Export data regularly for backup purposes
- Use exports for detailed analysis in spreadsheet software
- Share reports with stakeholders

## Troubleshooting

### Dashboard Not Loading
- **Issue**: Dashboard page is blank or shows errors
- **Solution**: 
  - Refresh the page
  - Clear your browser cache
  - Check your internet connection
  - Verify you have admin/staff permissions

### Statistics Appear Incorrect
- **Issue**: Numbers don't match expectations
- **Solution**:
  - Verify the time period selected
  - Check if filters are applied
  - Ensure data has been properly synced
  - Contact system administrator if issues persist

### Charts Not Displaying
- **Issue**: Chart areas are empty or show loading indicators
- **Solution**:
  - Wait for data to load (may take a few seconds)
  - Check browser console for JavaScript errors
  - Try a different browser
  - Ensure JavaScript is enabled

### Slow Performance
- **Issue**: Dashboard takes a long time to load
- **Solution**:
  - This is normal for systems with large amounts of data
  - Consider using shorter time periods
  - Close other browser tabs
  - Contact administrator about database optimization

## Related Features

- [Location Tracking (Admin View)](./location-tracking.md) - View alumni locations on a map
- [User Management](../user-management/README.md) - Manage user accounts
- [Export Data](./viewing-analytics.md#task-6-access-detailed-analytics) - Export system data

## Additional Resources

### API Endpoints
For developers integrating with the analytics system:
- `/api/dashboard-analytics/` - Get analytics data programmatically
- `/api/alumni-by-college/` - Get alumni distribution by college

### Data Refresh
- Dashboard statistics update in real-time
- Charts refresh when time period is changed
- Recent activity lists show the latest 5 items

### Security
- All analytics data is protected by authentication
- Only staff and admin users can access the dashboard
- Sensitive user information is not displayed in aggregate views
