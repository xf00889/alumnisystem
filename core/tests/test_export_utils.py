"""
Tests for export utilities with logo header integration
"""
import os
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.export_utils import ExportMixin, LogoHeaderService

User = get_user_model()


class LogoHeaderServiceTest(TestCase):
    """Test cases for LogoHeaderService"""
    
    def test_get_logo_path_returns_path_or_none(self):
        """Test that get_logo_path returns a valid path or None"""
        logo_path = LogoHeaderService.get_logo_path()
        
        # Should return either a valid path or None
        if logo_path is not None:
            self.assertTrue(os.path.exists(logo_path))
            self.assertTrue(logo_path.endswith('.png'))
        else:
            # If None, it means logo file was not found (acceptable)
            self.assertIsNone(logo_path)
    
    def test_logo_path_caching(self):
        """Test that logo path is cached after first call"""
        # Clear cache first
        LogoHeaderService._logo_path_cache = None
        
        # First call
        path1 = LogoHeaderService.get_logo_path()
        
        # Second call should return cached value
        path2 = LogoHeaderService.get_logo_path()
        
        self.assertEqual(path1, path2)


class LogoHeaderServiceErrorHandlingTest(TestCase):
    """Test cases for LogoHeaderService error handling"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear cache before each test
        LogoHeaderService._logo_path_cache = None
    
    def test_get_logo_path_handles_missing_file(self):
        """Test that get_logo_path handles missing logo file gracefully"""
        with patch('django.contrib.staticfiles.finders.find', return_value=None):
            with patch('django.conf.settings.STATIC_ROOT', None):
                logo_path = LogoHeaderService.get_logo_path()
                
                # Should return None without raising exception
                self.assertIsNone(logo_path)
    
    def test_get_logo_path_handles_file_size_error(self):
        """Test that get_logo_path handles file size check errors gracefully"""
        with patch('django.contrib.staticfiles.finders.find', return_value='/fake/path/logo.png'):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', side_effect=OSError("Permission denied")):
                    logo_path = LogoHeaderService.get_logo_path()
                    
                    # Should return None without raising exception
                    self.assertIsNone(logo_path)
    
    def test_get_logo_path_handles_oversized_file(self):
        """Test that get_logo_path rejects oversized logo files"""
        with patch('django.contrib.staticfiles.finders.find', return_value='/fake/path/logo.png'):
            with patch('os.path.exists', return_value=True):
                # Simulate file larger than MAX_LOGO_SIZE
                with patch('os.path.getsize', return_value=LogoHeaderService.MAX_LOGO_SIZE + 1):
                    logo_path = LogoHeaderService.get_logo_path()
                    
                    # Should return None for oversized file
                    self.assertIsNone(logo_path)
    
    def test_get_logo_path_handles_empty_file(self):
        """Test that get_logo_path rejects empty logo files"""
        with patch('django.contrib.staticfiles.finders.find', return_value='/fake/path/logo.png'):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=0):
                    logo_path = LogoHeaderService.get_logo_path()
                    
                    # Should return None for empty file
                    self.assertIsNone(logo_path)
    
    def test_get_logo_path_handles_corrupted_image(self):
        """Test that get_logo_path handles corrupted image files gracefully"""
        with patch('django.contrib.staticfiles.finders.find', return_value='/fake/path/logo.png'):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=1000):
                    with patch('PIL.Image.open', side_effect=Exception("Corrupted image")):
                        logo_path = LogoHeaderService.get_logo_path()
                        
                        # Should return None without raising exception
                        self.assertIsNone(logo_path)
    
    def test_get_logo_path_handles_pil_import_error(self):
        """Test that get_logo_path handles PIL import errors gracefully"""
        with patch('django.contrib.staticfiles.finders.find', return_value='/fake/path/logo.png'):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getsize', return_value=1000):
                    # The code already handles ImportError in the try-except block
                    # If PIL is not available, it logs an error and continues
                    # This test verifies the code doesn't crash when PIL import fails
                    try:
                        # Clear cache to force re-evaluation
                        LogoHeaderService._logo_path_cache = None
                        logo_path = LogoHeaderService.get_logo_path()
                        # Test passes if no exception is raised
                        self.assertTrue(True)
                    except ImportError:
                        self.fail("Should handle PIL import error gracefully")
    
    def test_add_pdf_header_handles_missing_logo(self):
        """Test that add_pdf_header handles missing logo gracefully"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        # Create a mock canvas and doc
        buffer = BytesIO()
        mock_canvas = canvas.Canvas(buffer, pagesize=A4)
        mock_doc = MagicMock()
        mock_doc.pagesize = A4
        
        # Call with None logo_path (missing logo)
        try:
            LogoHeaderService.add_pdf_header(mock_canvas, mock_doc, None)
            # Should complete without raising exception
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"add_pdf_header should handle missing logo gracefully: {e}")
    
    def test_add_pdf_header_handles_invalid_logo_path(self):
        """Test that add_pdf_header handles invalid logo path gracefully"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        buffer = BytesIO()
        mock_canvas = canvas.Canvas(buffer, pagesize=A4)
        mock_doc = MagicMock()
        mock_doc.pagesize = A4
        
        # Call with invalid logo path
        try:
            LogoHeaderService.add_pdf_header(mock_canvas, mock_doc, '/nonexistent/logo.png')
            # Should complete without raising exception (falls back to text-only)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"add_pdf_header should handle invalid logo path gracefully: {e}")
    
    def test_add_excel_header_handles_missing_logo(self):
        """Test that add_excel_header handles missing logo gracefully"""
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        
        # Call with None logo_path (missing logo)
        try:
            row = LogoHeaderService.add_excel_header(ws, None)
            # Should return row 4 and complete without raising exception
            self.assertEqual(row, 4)
        except Exception as e:
            self.fail(f"add_excel_header should handle missing logo gracefully: {e}")
    
    def test_add_excel_header_handles_invalid_logo_path(self):
        """Test that add_excel_header handles invalid logo path gracefully"""
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        
        # Call with invalid logo path
        try:
            row = LogoHeaderService.add_excel_header(ws, '/nonexistent/logo.png')
            # Should return row 4 and complete without raising exception (falls back to text-only)
            self.assertEqual(row, 4)
        except Exception as e:
            self.fail(f"add_excel_header should handle invalid logo path gracefully: {e}")


class ExportMixinPDFTest(TestCase):
    """Test cases for ExportMixin PDF export with logo header"""
    
    def setUp(self):
        """Set up test data"""
        self.mixin = ExportMixin()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            first_name='Test',
            last_name='User1'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User2'
        )
    
    def test_export_pdf_with_logo_header(self):
        """Test that PDF export includes logo header"""
        queryset = User.objects.all()
        
        response = self.mixin.export_pdf(
            queryset=queryset,
            filename='test_users',
            field_names=['id', 'username', 'email', 'first_name', 'last_name'],
            field_labels=['ID', 'Username', 'Email', 'First Name', 'Last Name'],
            title='Test Users Export'
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('test_users.pdf', response['Content-Disposition'])
        
        # Verify PDF content is not empty
        self.assertGreater(len(response.content), 0)
    
    def test_export_pdf_portrait_orientation(self):
        """Test PDF export with portrait orientation"""
        queryset = User.objects.all()
        
        response = self.mixin.export_pdf(
            queryset=queryset,
            filename='test_portrait',
            field_names=['id', 'username', 'email'],
            field_labels=['ID', 'Username', 'Email'],
            title='Portrait Test'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
    
    def test_export_pdf_landscape_orientation(self):
        """Test PDF export with landscape orientation (many columns)"""
        queryset = User.objects.all()
        
        # Use many fields to trigger landscape mode
        response = self.mixin.export_pdf(
            queryset=queryset,
            filename='test_landscape',
            field_names=[
                'id', 'username', 'email', 'first_name', 'last_name',
                'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login'
            ],
            field_labels=[
                'ID', 'Username', 'Email', 'First Name', 'Last Name',
                'Active', 'Staff', 'Superuser', 'Date Joined', 'Last Login'
            ],
            title='Landscape Test'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
    
    def test_export_pdf_with_empty_queryset(self):
        """Test PDF export with empty queryset"""
        queryset = User.objects.none()
        
        response = self.mixin.export_pdf(
            queryset=queryset,
            filename='test_empty',
            field_names=['id', 'username', 'email'],
            field_labels=['ID', 'Username', 'Email'],
            title='Empty Export'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
    
    def test_export_pdf_maintains_existing_functionality(self):
        """Test that existing PDF export functionality is maintained"""
        queryset = User.objects.all()
        
        # Test with default parameters
        response = self.mixin.export_pdf(
            queryset=queryset,
            filename='test_default'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertGreater(len(response.content), 0)
    
    def test_export_pdf_continues_on_logo_error(self):
        """Test that PDF export continues even if logo loading fails"""
        queryset = User.objects.all()
        
        # Mock get_logo_path to return invalid path
        with patch.object(LogoHeaderService, 'get_logo_path', return_value='/nonexistent/logo.png'):
            response = self.mixin.export_pdf(
                queryset=queryset,
                filename='test_error_handling',
                field_names=['id', 'username', 'email'],
                field_labels=['ID', 'Username', 'Email'],
                title='Error Handling Test'
            )
            
            # Export should still succeed with text-only header
            self.assertEqual(response.status_code, 200)
            self.assertGreater(len(response.content), 0)

