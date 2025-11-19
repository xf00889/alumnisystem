# Statistics

## Overview

Alumni Statistics Management allows you to create and display impressive metrics and numbers about the alumni network on the About page. Statistics provide visual impact and demonstrate the scale and success of the alumni community.

## Who Can Use This Feature

- Admin users with staff privileges
- Users with CMS management permissions
- Alumni relations staff
- Data analysts

## Prerequisites

- Admin account with appropriate permissions
- Logged into the system
- Access to CMS Dashboard
- Statistical data about alumni network

## How to Access

### Method 1: Through CMS Dashboard
1. Navigate to CMS Dashboard (`/cms/dashboard/`)
2. Click on "Alumni Statistics" or "Manage Statistics"
3. You will see the list of all statistic entries

### Method 2: Direct URL
- Navigate to `/cms/alumni-statistics/`

## Statistic Types

The system supports the following statistic types:

1. **Alumni Members**: Total registered alumni
2. **Alumni Groups**: Number of active groups
3. **Annual Events**: Events held per year
4. **Job Opportunities**: Jobs posted or filled
5. **Mentors**: Active mentors in the network
6. **Scholarships**: Scholarships provided
7. **Countries Represented**: Geographic reach
8. **Industries Represented**: Industry diversity

## Key Features

### 1. View All Statistics
- List view of all statistic entries
- Sort by type or order
- Filter by active status
- Pagination for large lists

### 2. Add New Statistics
- Create new statistic displays
- Choose statistic type
- Set values and labels
- Choose icons and colors
- Set display order

### 3. Edit Statistics
- Update statistic values
- Change labels
- Modify icons and colors
- Adjust display order
- Toggle active status

### 4. Delete Statistics
- Remove outdated statistics
- Confirmation required
- Permanent action

### 5. Statistic Ordering
- Control display sequence
- Lower numbers appear first
- Organize by importance

## Step-by-Step Guide

### Task 1: View Statistics List

1. Access Alumni Statistics from CMS Dashboard
2. View the list of all statistic entries
3. Observe the following information:
   - Statistic type
   - Value
   - Label
   - Icon
   - Icon color
   - Display order
   - Active status
4. Use pagination to navigate through multiple pages

**Expected Result**: Complete list of all alumni statistics with their details.

### Task 2: Create a New Statistic

1. From the Alumni Statistics list, click "Add Statistic" or "Create New"
2. Fill in the statistic details:

   **Statistic Type** (required):
   - Select from dropdown menu
   - Choose the category that best fits
   - Options: Alumni Members, Alumni Groups, Annual Events, Job Opportunities, Mentors, Scholarships, Countries, Industries
   
   **Value** (required):
   - Enter the statistic value
   - Maximum 20 characters
   - Use formatting for impact:
     - "5,000+" (with comma and plus)
     - "25+" (for growing numbers)
     - "100%" (for percentages)
     - "50K+" (for large numbers)
   - Examples: "5,000+", "25+", "100+", "50K+"
   
   **Label** (required):
   - Enter display label
   - Maximum 100 characters
   - Describes what the number represents
   - Examples:
     - "Alumni Members"
     - "Active Groups"
     - "Annual Events"
     - "Job Opportunities"
     - "Countries Worldwide"
   
   **Icon** (optional):
   - Enter Font Awesome icon class
   - Default: "fas fa-users"
   - Choose icons that represent the statistic
   - Examples:
     - "fas fa-users" (members, community)
     - "fas fa-user-friends" (groups)
     - "fas fa-calendar" (events)
     - "fas fa-briefcase" (jobs)
     - "fas fa-chalkboard-teacher" (mentors)
     - "fas fa-graduation-cap" (scholarships)
     - "fas fa-globe" (countries)
     - "fas fa-industry" (industries)
   
   **Icon Color** (optional):
   - Enter hex color code
   - Default: "#007bff" (blue)
   - Include the # symbol
   - Examples:
     - "#007bff" (blue)
     - "#28a745" (green)
     - "#dc3545" (red)
     - "#ffc107" (yellow/orange)
     - "#6f42c1" (purple)
     - "#17a2b8" (cyan)
   
   **Order**:
   - Enter a number for display order
   - Lower numbers appear first
   - Default: 0
   - Use increments of 10 (10, 20, 30...)
   
   **Is Active**:
   - Check to make statistic visible
   - Uncheck to hide without deleting

3. Review all entered information
4. Click "Save" or "Create Statistic"

**Expected Result**: New statistic is created and appears on the About page.

### Task 3: Edit an Existing Statistic

1. From the Alumni Statistics list, find the statistic to edit
2. Click the "Edit" button or statistic label
3. Update any of the following fields:
   - Statistic type
   - Value (update with current numbers)
   - Label
   - Icon
   - Icon color
   - Order
   - Active status
4. Make necessary changes
5. Click "Save" or "Update Statistic"

**Expected Result**: Statistic is updated with new information. Changes appear on the About page.

### Task 4: Update Statistics with Current Data

**Regular Update Process**:

1. **Gather Current Data**:
   - Query database for actual numbers
   - Use analytics tools
   - Consult with relevant departments
   - Verify data accuracy

2. **Update Each Statistic**:
   - Alumni Members: Check user count
   - Alumni Groups: Count active groups
   - Annual Events: Count events in past year
   - Job Opportunities: Count posted jobs
   - Mentors: Count active mentors
   - Scholarships: Count scholarships provided
   - Countries: Count unique countries
   - Industries: Count represented industries

3. **Format Values**:
   - Round to impressive numbers
   - Add "+" for growing metrics
   - Use "K" for thousands (5K+)
   - Use commas for readability (5,000+)

4. **Save Updates**:
   - Edit each statistic
   - Update value field
   - Save changes

**Expected Result**: Statistics reflect current, accurate data about the alumni network.

### Task 5: Choose Effective Icons and Colors

**Icon Selection Guide**:

- **Alumni Members**: fas fa-users, fas fa-user-graduate
- **Alumni Groups**: fas fa-user-friends, fas fa-users-cog
- **Annual Events**: fas fa-calendar, fas fa-calendar-check
- **Job Opportunities**: fas fa-briefcase, fas fa-user-tie
- **Mentors**: fas fa-chalkboard-teacher, fas fa-user-graduate
- **Scholarships**: fas fa-graduation-cap, fas fa-award
- **Countries**: fas fa-globe, fas fa-map-marked-alt
- **Industries**: fas fa-industry, fas fa-building

**Color Selection Guide**:

- **Blue (#007bff)**: Professional, trustworthy (jobs, members)
- **Green (#28a745)**: Growth, success (scholarships, opportunities)
- **Orange (#ffc107)**: Energy, enthusiasm (events, activities)
- **Purple (#6f42c1)**: Creativity, wisdom (mentors, education)
- **Cyan (#17a2b8)**: Modern, global (countries, reach)
- **Red (#dc3545)**: Impact, importance (use sparingly)

**Steps to Update**:
1. Edit each statistic
2. Update icon field with appropriate class
3. Update icon color with hex code
4. Save changes
5. Preview on About page

**Expected Result**: Statistics display with meaningful, visually appealing icons and colors.

### Task 6: Organize Statistics for Impact

**Recommended Organization**:

**Primary Statistics (Order 10-30)** - Most impressive:
- 10: Alumni Members (5,000+)
- 20: Countries Represented (50+)
- 30: Job Opportunities (500+)

**Secondary Statistics (Order 40-60)** - Supporting metrics:
- 40: Alumni Groups (25+)
- 50: Annual Events (100+)
- 60: Active Mentors (150+)

**Additional Statistics (Order 70+)** - Nice to have:
- 70: Scholarships Provided (50+)
- 80: Industries Represented (30+)

**Steps to Organize**:
1. Identify most impressive statistics
2. Assign order values by impact
3. Edit each statistic and update order
4. Save all changes
5. Review About page display

**Expected Result**: Most impressive statistics are prominently displayed first.

### Task 7: Deactivate a Statistic

1. From the Alumni Statistics list, find the statistic
2. Click "Edit" on the statistic
3. Uncheck the "Is Active" checkbox
4. Click "Save"

**Use Cases**:
- Temporarily outdated data
- Statistic no longer relevant
- Testing before making public
- Seasonal statistics

**Expected Result**: Statistic no longer appears on the About page but remains in admin list.

### Task 8: Delete a Statistic

1. From the Alumni Statistics list, find the statistic to delete
2. Click the "Delete" button
3. Review the confirmation page
4. Confirm you want to delete
5. Click "Yes, delete" or "Confirm deletion"

**Expected Result**: Statistic is permanently removed from the system.

## Tips and Best Practices

1. **Accuracy**: Ensure statistics are accurate and verifiable
2. **Regular Updates**: Update statistics quarterly or annually
3. **Impressive Numbers**: Use round, impressive numbers (5,000+ vs 4,987)
4. **Growth Indicators**: Use "+" to show ongoing growth
5. **Visual Variety**: Use different colors for different statistics
6. **Icon Relevance**: Choose icons that clearly represent the statistic
7. **Consistency**: Maintain consistent formatting across all statistics
8. **Verification**: Verify data sources before publishing
9. **Context**: Ensure labels provide clear context
10. **Impact**: Focus on statistics that demonstrate value and scale

## Important Notes

- **Data Accuracy**: Statistics should be based on real data
- **Update Frequency**: Plan regular updates to keep statistics current
- **Icon Library**: Icons use Font Awesome
- **Color Format**: Colors must be in hex format with # symbol
- **Deletion**: Deleting a statistic is permanent

## Troubleshooting

### Statistic Not Appearing

**Issue**: Created or edited statistic doesn't show on About page

**Solutions**:
- Verify "Is Active" checkbox is checked
- Clear browser cache and refresh
- Check display order
- Verify About page template includes statistics section
- Wait a few moments for cache to clear

### Icon Not Displaying

**Issue**: Icon doesn't appear or shows as box

**Solutions**:
- Verify Font Awesome is loaded
- Check icon class name is correct
- Ensure icon exists in Font Awesome library
- Try a different, common icon
- Check browser console for errors

### Icon Wrong Color

**Issue**: Icon displays in unexpected color

**Solutions**:
- Verify hex color code format (#007bff)
- Check that # symbol is included
- Try a different color code
- Clear browser cache
- Verify CSS isn't overriding color

### Value Formatting Issues

**Issue**: Value doesn't display as expected

**Solutions**:
- Check for special characters
- Verify character limit (20 characters)
- Use standard formatting (commas, +, K)
- Test with simple value first

### Cannot Save Statistic

**Issue**: Save button doesn't work or shows errors

**Solutions**:
- Check for validation errors
- Ensure required fields are filled
- Verify value doesn't exceed 20 characters
- Check icon color format
- Try refreshing and re-entering data

## Related Features

- [CMS Dashboard](dashboard.md) - Return to CMS main dashboard
- [About Page Configuration](about-page.md) - Configure about page content
- [Staff Members Management](staff-members.md) - Manage staff profiles
- [Timeline Management](timeline.md) - Manage university timeline

## Screenshots

> **Note**: Screenshots should be added showing:
> - Alumni Statistics list view
> - Create new statistic form
> - Statistic type dropdown
> - Icon and color fields
> - Edit statistic form
> - Statistics display on About page
> - Different icon colors
> - Success messages
> - Mobile view of statistics
