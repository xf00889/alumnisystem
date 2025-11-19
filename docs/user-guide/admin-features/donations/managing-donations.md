# Managing Donations

## Overview

The donation management feature allows administrators to review, verify, and process donations made to campaigns. You can view payment proofs, update donation status, send receipts, filter donations by various criteria, and export donation data for reporting. This is a critical function for maintaining donor trust and ensuring accurate financial records.

## Who Can Use This Feature

- **User Role**: Admin users and staff members only
- **Permissions Required**: Admin or staff privileges
- **Prerequisites**: 
  - Active admin or staff account
  - Access to donation management area
  - Existing donations to manage

## How to Access

1. Log in to your admin account
2. Navigate to the **Donations** section from the admin menu
3. Click on **Manage Donations** or **Verify Donations**

## Key Features

- View all donations with comprehensive filtering
- Verify payment proofs submitted by donors
- Update donation status (Pending, Completed, Failed, Disputed)
- Send receipt emails to donors
- Filter donations by campaign, status, date range, and search terms
- Export donation data to CSV
- View payment proof images
- Add verification notes
- Track verification history

## Step-by-Step Guide

### Task 1: Viewing and Filtering Donations

This task covers accessing the donation list and using filters to find specific donations.

1. **Access the donation management page**
   - Navigate to **Donations > Manage Donations**
   - **Expected Result**: List of all donations appears with filter options

2. **View donation statistics**
   - At the top of the page, view summary statistics:
     - Total donations (filtered)
     - Completed donations count
     - Pending donations count
     - Failed/Refunded donations count
   - **Expected Result**: Overview of donation status distribution

3. **Use the search function**
   - Enter keywords in the search box
   - Search looks in:
     - Donor names
     - Donor emails
     - Reference numbers
     - GCash transaction IDs
     - Campaign names
   - Press Enter or click Search
   - **Expected Result**: Filtered list shows matching donations

4. **Filter by campaign**
   - Use the **Campaign** dropdown
   - Select specific campaign to view its donations
   - **Expected Result**: List shows only donations for selected campaign

5. **Filter by donation status**
   - Use the **Status** dropdown to filter:
     - All Statuses
     - Pending Payment
     - Pending Verification
     - Completed
     - Failed
     - Refunded
     - Disputed
   - **Expected Result**: List shows only donations with selected status

6. **Filter by date range**
   - Enter **Start Date** to filter donations from that date
   - Enter **End Date** to filter donations up to that date
   - Use both for a specific date range
   - **Expected Result**: List shows donations within date range

7. **Clear filters**
   - Click **Clear Filters** or remove individual filter selections
   - **Expected Result**: Full donation list is restored

8. **View donation details in list**
   - Each donation row shows:
     - Donor name (or "Anonymous")
     - Campaign name
     - Amount
     - Status badge
     - Reference number
     - Donation date
     - Action buttons (View, Verify, Send Receipt)
   - **Expected Result**: Quick overview of each donation

### Task 2: Verifying Payment Proofs

This task covers the critical process of reviewing and verifying donation payments.

1. **Access pending verifications**
   - Filter by status: **Pending Verification**
   - Or navigate to **Donations > Verify Donations**
   - **Expected Result**: List of donations awaiting verification

2. **Select donation to verify**
   - Click **View** or **Verify** button on a donation
   - **Expected Result**: Donation detail page or verification modal appears

3. **Review payment proof image**
   - Click on the payment proof thumbnail to view full size
   - Verify the image shows:
     - GCash transaction confirmation
     - Correct amount
     - Transaction date
     - Reference number
     - Recipient account matches your GCash
   - **Expected Result**: Payment proof is clearly visible and readable

4. **Verify reference number**
   - Check the reference number entered by donor
   - Compare with reference number in payment proof image
   - Ensure they match
   - **Expected Result**: Reference number is confirmed

5. **Verify donation amount**
   - Check the amount in the payment proof
   - Compare with the donation amount in the system
   - Ensure they match exactly
   - **Expected Result**: Amount is confirmed

6. **Check transaction date**
   - Verify the transaction date is reasonable
   - Should be close to the donation creation date
   - Flag if there's a significant discrepancy
   - **Expected Result**: Transaction timing is verified

7. **Update donation status**
   - If verification is successful:
     - Change **Status** to "Completed"
     - Add verification notes (optional): "Payment verified, amount and reference confirmed"
   - If verification fails:
     - Change **Status** to "Failed" or "Disputed"
     - Add detailed verification notes explaining the issue
   - **Expected Result**: Appropriate status is selected

8. **Add verification notes**
   - Enter notes in the **Verification Notes** field
   - Include:
     - Verification outcome
     - Any discrepancies found
     - Actions taken
     - Contact with donor (if any)
   - **Expected Result**: Detailed notes are recorded

9. **Enter GCash Transaction ID (optional)**
   - If visible in payment proof, enter the GCash transaction ID
   - This provides additional verification record
   - **Expected Result**: Transaction ID is recorded

10. **Save verification**
    - Click **Save** or **Verify Donation**
    - **Expected Result**: Donation status is updated
    - System records verification date and verifier
    - Campaign total is updated if status is "Completed"

11. **Send receipt (if completed)**
    - After marking as completed, send receipt to donor
    - See Task 4 for receipt sending process
    - **Expected Result**: Donor receives confirmation email

### Task 3: Updating Donation Status

This task covers changing donation status for various scenarios.

1. **Understand status options**
   - **Pending Payment**: Donation created, awaiting payment proof
   - **Pending Verification**: Payment proof submitted, awaiting admin review
   - **Completed**: Payment verified and accepted
   - **Failed**: Payment verification failed or payment not received
   - **Refunded**: Payment was refunded to donor
   - **Disputed**: Payment is under dispute or investigation
   - **Expected Result**: Clear understanding of each status

2. **Mark donation as completed**
   - Used when payment is verified successfully
   - Updates campaign total automatically
   - Triggers receipt email (if configured)
   - **Expected Result**: Donation is confirmed and counted

3. **Mark donation as failed**
   - Used when:
     - Payment proof is invalid or fake
     - Amount doesn't match
     - Payment was not received
     - Reference number is incorrect
   - Add detailed notes explaining failure reason
   - **Expected Result**: Donation is marked failed with explanation

4. **Mark donation as disputed**
   - Used when:
     - Payment proof is suspicious
     - Duplicate payment proof detected
     - Fraud alert triggered
     - Requires further investigation
   - Add notes about the dispute
   - **Expected Result**: Donation is flagged for investigation

5. **Mark donation as refunded**
   - Used when payment was returned to donor
   - Add notes about refund reason and date
   - Updates campaign total automatically
   - **Expected Result**: Donation is marked refunded

6. **Change status from completed to failed**
   - Used if completed donation is later found to be invalid
   - Updates campaign total automatically (decreases)
   - Add detailed notes explaining the change
   - **Expected Result**: Donation is reversed and campaign total adjusted

7. **Save status changes**
   - Click **Save** or **Update Status**
   - **Expected Result**: Status change is recorded with timestamp and verifier

### Task 4: Sending Receipts

This task covers sending confirmation emails to donors.

1. **Verify donation is completed**
   - Receipts should only be sent for completed donations
   - Check that status is "Completed"
   - **Expected Result**: Donation is verified and ready for receipt

2. **Check donor email availability**
   - For registered users: Email is from user account
   - For anonymous donors: Email is from donation form
   - Verify email address is valid
   - **Expected Result**: Valid email address is available

3. **Send receipt from donation list**
   - Click **Send Receipt** button next to the donation
   - **Expected Result**: Confirmation dialog appears

4. **Confirm receipt sending**
   - Review donor email address in confirmation
   - Click **Confirm** or **Send Receipt**
   - **Expected Result**: Receipt email is sent

5. **Verify receipt was sent**
   - Check for success message
   - Donation record shows "Receipt Sent" status
   - **Expected Result**: Receipt sending is confirmed

6. **Handle receipt sending errors**
   - If error occurs, check:
     - Email configuration is set up
     - Donor email is valid
     - Email service is working
   - Try again or contact system administrator
   - **Expected Result**: Error is identified and resolved

7. **Resend receipt if needed**
   - If donor didn't receive receipt, click **Send Receipt** again
   - System allows resending receipts
   - **Expected Result**: Receipt is resent to donor

### Task 5: Filtering and Exporting Donations

This task covers advanced filtering and data export for reporting.

1. **Apply multiple filters**
   - Combine filters for specific reports:
     - Campaign + Date Range: Campaign performance over time
     - Status + Date Range: Verification workload
     - Search + Campaign: Find specific donor in campaign
   - **Expected Result**: Highly targeted donation list

2. **Sort donation list**
   - Click column headers to sort:
     - Date (newest/oldest first)
     - Amount (highest/lowest first)
     - Status (alphabetical)
   - **Expected Result**: List is sorted by selected criteria

3. **View donation totals**
   - Check summary statistics at top of page
   - Shows totals for filtered results
   - **Expected Result**: Financial summary of filtered donations

4. **Export donations to CSV**
   - Click **Export** or **Download CSV** button
   - **Expected Result**: Export dialog appears

5. **Configure export options (if available)**
   - Select fields to include in export
   - Choose date format
   - Set file name
   - **Expected Result**: Export is configured

6. **Download export file**
   - Click **Download** or **Export**
   - **Expected Result**: CSV file downloads to your computer

7. **Review exported data**
   - Open CSV file in spreadsheet software
   - Verify data is complete and accurate
   - Use for reporting, analysis, or record-keeping
   - **Expected Result**: Donation data is available for analysis

## Tips and Best Practices

- **Timely Verification**: Verify donations within 24 hours to maintain donor trust
- **Detailed Notes**: Always add verification notes, especially for failed or disputed donations
- **Double-Check**: Verify amount, reference number, and date carefully before approving
- **Fraud Awareness**: Watch for duplicate payment proofs or suspicious patterns
- **Communication**: Contact donors if payment proof is unclear or has issues
- **Receipt Sending**: Send receipts promptly after verification
- **Regular Monitoring**: Check pending verifications daily
- **Status Accuracy**: Use correct status for each situation
- **Data Export**: Export donation data regularly for backup and reporting
- **Campaign Updates**: Keep donors informed through campaign updates

## Common Use Cases

### Use Case 1: Daily Verification Routine
Each morning, filter for "Pending Verification" donations, verify payment proofs, update statuses, and send receipts. This ensures timely processing and donor satisfaction.

### Use Case 2: Campaign Report
Filter donations by specific campaign and date range, export to CSV, and create a report showing total raised, number of donors, and donation patterns.

### Use Case 3: Disputed Payment Investigation
Mark suspicious donation as "Disputed", add detailed notes, contact donor for clarification, and update status based on investigation outcome.

### Use Case 4: Month-End Reconciliation
Export all completed donations for the month, compare with GCash transaction history, and verify all payments are accounted for.

## Troubleshooting

### Issue: Cannot View Payment Proof
**Symptoms**: Payment proof image won't load or shows error
**Solution**: 
- Check internet connection
- Try refreshing the page
- Verify image file was uploaded successfully
- Check browser console for errors
- Try different browser
- Contact donor to resubmit if image is corrupted

### Issue: Receipt Email Not Sending
**Symptoms**: Receipt send button doesn't work or error message appears
**Solution**: 
- Verify email configuration is set up (SMTP, Brevo, or SendGrid)
- Check that donor email address is valid
- Verify donation status is "Completed"
- Check email service logs for errors
- Contact system administrator if issue persists

### Issue: Campaign Total Not Updating
**Symptoms**: Campaign total doesn't reflect verified donations
**Solution**: 
- Verify donation status is set to "Completed"
- Refresh the campaign page
- Check that donation is associated with correct campaign
- System recalculates totals automatically on status change
- Contact system administrator if total is still incorrect

### Issue: Cannot Change Donation Status
**Symptoms**: Status dropdown is disabled or changes don't save
**Solution**: 
- Verify you have admin or staff permissions
- Check if donation is locked by another administrator
- Ensure all required fields are filled
- Try logging out and back in
- Clear browser cache

### Issue: Duplicate Payment Proofs
**Symptoms**: Same payment proof image appears on multiple donations
**Solution**: 
- Mark all but one as "Disputed" or "Failed"
- Add notes explaining duplicate detection
- Contact donors to clarify which donation is legitimate
- Investigate for potential fraud
- Keep detailed records of investigation

## Related Features

- [Creating Campaigns](creating-campaigns.md) - Create fundraising campaigns
- [Managing Campaigns](managing-campaigns.md) - Edit and update campaigns
- [GCash Configuration](gcash-configuration.md) - Set up payment accounts
- [Making Donations (User View)](../../user-features/donations/making-donations.md) - How users make donations

## Additional Notes

- Verification date and verifier are automatically recorded when status is updated
- Campaign totals are automatically recalculated when donation status changes
- Only completed donations count toward campaign goals
- Donation records cannot be deleted to preserve financial audit trail
- All status changes are logged for audit purposes
- Payment proof images are stored securely and backed up
- Reference numbers are provided by donors from their GCash receipts
- Anonymous donations hide donor identity but preserve financial records
- Receipt emails include donation details, campaign information, and thank you message

---

**Need Help?** If you encounter issues not covered in this guide, please contact system administrators or refer to the main Donations documentation.

*Last Updated: November 19, 2025*
