# Location Tracking

## Overview

The Location Tracking feature provides administrators with a real-time map view of alumni who are currently sharing their location. This powerful analytics tool helps visualize the geographic distribution of active alumni and provides insights into where your alumni network is located.

## Who Can Use This Feature

- **Admin Users**: Staff members with administrative privileges
- **Requirements**: 
  - Admin/staff account access
  - Alumni must have granted location permissions in their browsers
  - Alumni must be logged in and actively sharing their location

## How to Access

1. Log in to your admin account
2. Navigate to the admin dashboard
3. Click on **Location Tracking** or **Alumni Map** in the analytics section
4. The map interface will load showing all currently active alumni locations

**Direct URL**: `/location_tracking/map/`

## Key Features

- **Real-time Map View**: Interactive map displaying alumni locations
- **Batch Grouping**: Alumni organized by graduation year/batch
- **Search and Filtering**: Find specific alumni or filter by batch, course, or location
- **Statistics Dashboard**: View total online alumni, batches represented, and courses
- **Alumni Details**: Click on markers or list items to view alumni information
- **Auto-refresh**: Location data updates automatically every 5 minutes

## Understanding the Interface

### Statistics Cards

At the top of the page, you'll see three key statistics:

1. **Total Alumni Online**: Number of alumni currently sharing their location
2. **Batches Represented**: Number of different graduation years/batches
3. **Different Courses**: Number of unique courses represented

### Alumni List Panel (Left Side)

The left panel displays:
- **Search Box**: Search for specific alumni by name
- **Filter Dropdowns**: Filter by batch, course, or location
- **Batch Groups**: Alumni organized by graduation year
  - Each batch shows the number of alumni in that group
  - Alumni are listed with their avatar, name, and course
  - Click on any alumni to highlight their location on the map

### Map View (Right Side)

The interactive map shows:
- **Alumni Markers**: Circular markers with alumni avatars
- **Marker Clusters**: When multiple alumni are close together, markers cluster with a count
- **Popup Information**: Click markers to see alumni details
- **Refresh Button**: Manually refresh the map data

## Step-by-Step Guide

### Task 1: View Alumni Locations

1. Access the Location Tracking page from the admin dashboard
2. The map will automatically load with all currently active alumni locations
3. Review the statistics at the top to see overall engagement
4. Observe the map markers showing where alumni are located

**Expected Result**: You'll see a map with markers representing each alumni's current location, along with summary statistics.

### Task 2: Search for Specific Alumni

1. Locate the search box in the left panel
2. Type the name of the alumni you're looking for
3. The list will filter in real-time as you type
4. Click on the alumni name in the filtered results

**Expected Result**: The map will center on the selected alumni's location and highlight their marker.

### Task 3: Filter Alumni by Batch

1. Click on the **Batch Filter** dropdown
2. Select a specific graduation year from the list
3. The map and list will update to show only alumni from that batch
4. To clear the filter, select "All Batches"

**Expected Result**: Only alumni from the selected batch will be displayed on the map and in the list.

### Task 4: Filter Alumni by Course

1. Click on the **Course Filter** dropdown
2. Select a specific course/program
3. The display will update to show only alumni from that course
4. To clear the filter, select "All Courses"

**Expected Result**: The map and list will show only alumni who studied the selected course.

### Task 5: View Alumni Details

1. Click on any marker on the map, OR
2. Click on any alumni name in the left panel list
3. A popup will appear showing:
   - Alumni name
   - Profile photo
   - Course/program
   - Batch/graduation year
   - Current location (if available)

**Expected Result**: Detailed information about the selected alumni is displayed.

### Task 6: Navigate the Map

1. **Zoom In/Out**: Use the + and - buttons on the map, or scroll with your mouse
2. **Pan**: Click and drag the map to move around
3. **Cluster Expansion**: Click on clustered markers (showing a number) to zoom in and see individual alumni
4. **Reset View**: Click the "Refresh Map" button to reload and reset the view

**Expected Result**: You can explore different areas of the map and view alumni locations at various zoom levels.

### Task 7: Refresh Location Data

1. Click the **Refresh Map** button in the top-right of the map container
2. The map will reload with the latest location data
3. A loading indicator will briefly appear during the refresh

**Expected Result**: The map updates with the most current alumni location information.

### Task 8: View Batch Groups

1. Scroll through the left panel to see different batch groups
2. Each batch group shows:
   - Graduation year
   - Number of alumni in that batch
   - List of alumni with avatars and courses
3. Click on any batch header to focus on that group

**Expected Result**: You can see how alumni are distributed across different graduation years.

## Understanding Location Data

### Online Status

Alumni are considered "online" and visible on the map when:
- They are logged into the system
- They have granted location permissions to their browser
- Their location has been updated within the last **2 hours**

### Location Updates

- Alumni locations are automatically updated when they access the system
- The map refreshes every 5 minutes to show the latest data
- Alumni who haven't updated their location in 2+ hours are not shown

### Privacy Considerations

- Only alumni who have actively granted location permissions are tracked
- Alumni can disable location sharing at any time through their browser settings
- Location data is used solely for network analytics and visualization

## Tips and Best Practices

### Maximizing Visibility

- **Encourage Location Sharing**: Remind alumni to enable location permissions for better network insights
- **Regular Monitoring**: Check the map during peak hours (evenings, weekends) for maximum visibility
- **Event Tracking**: Monitor location data during alumni events to see attendance patterns

### Using Filters Effectively

- **Batch Analysis**: Filter by batch to see geographic distribution of specific graduation years
- **Course Insights**: Use course filters to understand where alumni from different programs are located
- **Combined Filters**: Use multiple filters together for more specific analysis

### Data Interpretation

- **Low Numbers**: If few alumni appear, it may indicate:
  - Alumni haven't granted location permissions
  - Alumni aren't currently logged in
  - Time of day (fewer users during work hours)
- **Clusters**: Large clusters indicate areas with high alumni concentration
- **Spread**: Wide geographic spread shows the reach of your alumni network

## Troubleshooting

### No Alumni Appearing on Map

**Possible Causes**:
- No alumni are currently logged in
- Alumni haven't granted location permissions
- Location services are disabled on alumni devices

**Solutions**:
- Check during different times of day
- Send reminders to alumni about enabling location sharing
- Verify that the location tracking feature is enabled system-wide

### Map Not Loading

**Possible Causes**:
- Internet connection issues
- Browser compatibility problems
- JavaScript errors

**Solutions**:
- Refresh the page (F5 or Ctrl+R)
- Clear browser cache and cookies
- Try a different browser (Chrome, Firefox, Edge recommended)
- Check browser console for error messages

### Filters Not Working

**Possible Causes**:
- No data matches the selected filters
- Filter dropdowns not populated

**Solutions**:
- Clear all filters and try again
- Refresh the page
- Verify that alumni data includes the fields you're filtering by

### Alumni Location Seems Outdated

**Possible Causes**:
- Alumni hasn't logged in recently
- Location hasn't been updated in the last 2 hours

**Solutions**:
- Click the "Refresh Map" button
- Note the 2-hour threshold for "online" status
- Encourage alumni to log in more frequently

## Technical Notes

### Location Accuracy

- Location accuracy depends on the device and method used:
  - **GPS**: Most accurate (within meters)
  - **Wi-Fi**: Moderately accurate (within 100 meters)
  - **IP Address**: Least accurate (city-level)

### Browser Compatibility

The location tracking feature works best with:
- Google Chrome (recommended)
- Mozilla Firefox
- Microsoft Edge
- Safari (iOS and macOS)

### Performance Considerations

- The map can handle hundreds of markers efficiently
- Clustering automatically groups nearby markers for better performance
- Large numbers of alumni may take a few seconds to load

## Related Features

- [Viewing Analytics](viewing-analytics.md) - Overall system analytics and reports
- [User Management](../user-management/viewing-users.md) - Managing alumni accounts
- [Alumni Directory](../../user-features/alumni-directory/README.md) - Public-facing alumni directory

## Additional Resources

### Understanding the Map Interface

The map uses Leaflet.js, an open-source mapping library:
- **Markers**: Represent individual alumni locations
- **Clusters**: Group nearby markers to reduce clutter
- **Popups**: Show detailed information when clicking markers
- **Controls**: Zoom, pan, and navigation tools

### Data Privacy and Compliance

- Location data is stored securely and used only for analytics
- Alumni can opt out of location sharing at any time
- Data retention follows your institution's privacy policy
- Complies with GDPR and other privacy regulations

### Future Enhancements

Potential improvements to the location tracking feature:
- Historical location data and trends
- Export location data to CSV/Excel
- Custom geographic regions and boundaries
- Location-based event notifications
- Alumni density heat maps

---

**Need Help?**

If you encounter issues with the location tracking feature:
1. Check the troubleshooting section above
2. Contact your system administrator
3. Submit a feedback report through the system
4. Refer to the technical documentation for advanced configuration
