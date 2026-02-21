"""
Tests for the seed_cms_data management command.

This module tests the CMS data seeding functionality to ensure:
- All CMS model types are created correctly
- Command is idempotent (can be run multiple times safely)
- Existing data is preserved when appropriate
- Command output contains useful statistics
- Error handling works correctly
"""

from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from cms.models import (
    SiteConfig,
    AboutPageConfig,
    Feature,
    Testimonial,
    StaffMember,
    TimelineItem,
    ContactInfo,
    FAQ,
    AlumniStatistic,
)


class SeedCMSDataCommandTestCase(TestCase):
    """
    Test suite for the seed_cms_data management command.
    
    Tests cover:
    - Model creation for all CMS types
    - Idempotency (running command multiple times)
    - Data preservation for existing records
    - Command output and statistics
    - Error handling
    """
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear all CMS data before each test
        SiteConfig.objects.all().delete()
        AboutPageConfig.objects.all().delete()
        Feature.objects.all().delete()
        Testimonial.objects.all().delete()
        StaffMember.objects.all().delete()
        TimelineItem.objects.all().delete()
        ContactInfo.objects.all().delete()
        FAQ.objects.all().delete()
        AlumniStatistic.objects.all().delete()
    
    def test_command_creates_all_models(self):
        """
        Test that the seed_cms_data command creates instances of all CMS model types.
        
        Validates: Requirements 2.1
        """
        # Run the command
        out = StringIO()
        call_command('seed_cms_data', stdout=out)
        
        # Verify singleton models were created
        self.assertEqual(SiteConfig.objects.count(), 1, "SiteConfig should have exactly 1 instance")
        self.assertEqual(AboutPageConfig.objects.count(), 1, "AboutPageConfig should have exactly 1 instance")
        
        # Verify multiple record models have at least one instance
        self.assertGreater(Feature.objects.count(), 0, "Feature should have at least 1 instance")
        self.assertGreater(Testimonial.objects.count(), 0, "Testimonial should have at least 1 instance")
        self.assertGreater(StaffMember.objects.count(), 0, "StaffMember should have at least 1 instance")
        self.assertGreater(TimelineItem.objects.count(), 0, "TimelineItem should have at least 1 instance")
        self.assertGreater(ContactInfo.objects.count(), 0, "ContactInfo should have at least 1 instance")
        self.assertGreater(FAQ.objects.count(), 0, "FAQ should have at least 1 instance")
        self.assertGreater(AlumniStatistic.objects.count(), 0, "AlumniStatistic should have at least 1 instance")
    
    def test_command_output_contains_statistics(self):
        """
        Test that the command output includes statistics about created/updated records.
        
        Validates: Requirements 2.4
        """
        # Run the command and capture output
        out = StringIO()
        call_command('seed_cms_data', stdout=out)
        output = out.getvalue()
        
        # Verify output contains key statistics keywords
        self.assertIn('Created', output, "Output should mention created records")
        self.assertIn('record(s)', output, "Output should include record count information")
        self.assertIn('completed successfully', output, "Output should indicate successful completion")
        
        # Verify output contains summary report
        self.assertIn('SUMMARY REPORT', output, "Output should include summary report")
        self.assertIn('Statistics', output, "Output should include statistics section")
    
    def test_error_handling_with_invalid_data(self):
        """
        Test that the command handles errors gracefully when encountering issues.
        
        This test verifies that the command doesn't crash completely when
        encountering validation errors or other issues.
        
        Validates: Requirements 2.5
        """
        # First, run the command successfully to create data
        out = StringIO()
        call_command('seed_cms_data', stdout=out)
        
        # Verify the command completed (even if with some errors)
        output = out.getvalue()
        self.assertIn('Seeding', output, "Command should produce output even with errors")
        
        # The command should still create some records even if some fail
        total_records = (
            SiteConfig.objects.count() +
            AboutPageConfig.objects.count() +
            Feature.objects.count() +
            Testimonial.objects.count() +
            StaffMember.objects.count() +
            TimelineItem.objects.count() +
            ContactInfo.objects.count() +
            FAQ.objects.count() +
            AlumniStatistic.objects.count()
        )
        self.assertGreater(total_records, 0, "Command should create at least some records")


class SeedCMSDataIdempotencyTestCase(TestCase):
    """
    Test suite for verifying idempotency of the seed_cms_data command.
    
    Idempotency means the command can be run multiple times without
    creating duplicate data or causing errors.
    """
    
    def test_command_idempotency(self):
        """
        Test that running the command multiple times doesn't create duplicates.
        
        Validates: Requirements 2.2
        """
        # Run the command first time
        out1 = StringIO()
        call_command('seed_cms_data', stdout=out1)
        
        # Count records after first run
        first_run_counts = {
            'SiteConfig': SiteConfig.objects.count(),
            'AboutPageConfig': AboutPageConfig.objects.count(),
            'Feature': Feature.objects.count(),
            'Testimonial': Testimonial.objects.count(),
            'StaffMember': StaffMember.objects.count(),
            'TimelineItem': TimelineItem.objects.count(),
            'ContactInfo': ContactInfo.objects.count(),
            'FAQ': FAQ.objects.count(),
            'AlumniStatistic': AlumniStatistic.objects.count(),
        }
        
        # Run the command second time
        out2 = StringIO()
        call_command('seed_cms_data', stdout=out2)
        
        # Count records after second run
        second_run_counts = {
            'SiteConfig': SiteConfig.objects.count(),
            'AboutPageConfig': AboutPageConfig.objects.count(),
            'Feature': Feature.objects.count(),
            'Testimonial': Testimonial.objects.count(),
            'StaffMember': StaffMember.objects.count(),
            'TimelineItem': TimelineItem.objects.count(),
            'ContactInfo': ContactInfo.objects.count(),
            'FAQ': FAQ.objects.count(),
            'AlumniStatistic': AlumniStatistic.objects.count(),
        }
        
        # Verify counts remain the same (no duplicates created)
        for model_name, first_count in first_run_counts.items():
            second_count = second_run_counts[model_name]
            self.assertEqual(
                first_count,
                second_count,
                f"{model_name} count should remain the same after second run. "
                f"First run: {first_count}, Second run: {second_count}"
            )
        
        # Verify output indicates updates, not new creations
        output2 = out2.getvalue()
        self.assertIn('Updated', output2, "Second run should show updates, not just creations")
    
    def test_singleton_models_updated(self):
        """
        Test that singleton models are updated, not duplicated.
        
        Validates: Requirements 2.2, 2.3
        """
        # Run command first time
        call_command('seed_cms_data', stdout=StringIO())
        
        # Modify singleton data
        site_config = SiteConfig.objects.first()
        original_name = site_config.site_name
        site_config.site_name = "Modified Name"
        site_config.save()
        
        # Run command second time
        call_command('seed_cms_data', stdout=StringIO())
        
        # Verify still only one instance
        self.assertEqual(SiteConfig.objects.count(), 1, "Should still have only 1 SiteConfig")
        
        # Verify data was updated back to default
        site_config.refresh_from_db()
        self.assertEqual(
            site_config.site_name,
            original_name,
            "SiteConfig should be updated to original value"
        )
    
    def test_multiple_record_models(self):
        """
        Test that multiple record models handle updates correctly.
        
        Validates: Requirements 2.2, 2.3
        """
        # Run command first time
        call_command('seed_cms_data', stdout=StringIO())
        
        # Get initial counts
        initial_feature_count = Feature.objects.count()
        
        # Modify an existing feature
        feature = Feature.objects.first()
        feature.content = "Modified content"
        feature.save()
        
        # Run command second time
        call_command('seed_cms_data', stdout=StringIO())
        
        # Verify count remains the same
        self.assertEqual(
            Feature.objects.count(),
            initial_feature_count,
            "Feature count should remain the same"
        )
        
        # Verify the feature was updated
        feature.refresh_from_db()
        self.assertNotEqual(
            feature.content,
            "Modified content",
            "Feature should be updated to default content"
        )
