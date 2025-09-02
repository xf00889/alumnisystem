import csv
import io
import json
from datetime import datetime
from django.http import HttpResponse
from django.db.models import QuerySet
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def get_nested_value(obj, field_name):
    """Get value from nested field (e.g., 'user__username')"""
    if '__' not in field_name:
        return getattr(obj, field_name, '')
    
    # Handle nested field access
    parts = field_name.split('__')
    current_obj = obj
    
    for part in parts:
        if current_obj is None:
            return ''
        current_obj = getattr(current_obj, part, None)
    
    return current_obj if current_obj is not None else ''

def calculate_table_width(field_labels, sample_data):
    """Calculate approximate table width to determine page orientation"""
    total_width = 0
    for i, label in enumerate(field_labels):
        # Base width on label length
        col_width = len(label) * 8
        
        # Check sample data for this column
        for row in sample_data:
            if i < len(row):
                content_length = len(str(row[i])) * 6
                col_width = max(col_width, content_length)
        
        # Cap width and add to total
        col_width = min(col_width, 120)
        total_width += col_width
    
    return total_width

def should_use_landscape(field_labels, sample_data):
    """Determine if landscape orientation is needed"""
    table_width = calculate_table_width(field_labels, sample_data)
    # If table width is more than 500 points, use landscape
    return table_width > 500

class ExportMixin:
    """Mixin class to add export functionality to views"""
    
    def export_csv(self, queryset, filename, field_names=None, field_labels=None):
        """Export queryset to CSV format"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        if field_names is None:
            # Get all field names from the model
            field_names = [field.name for field in queryset.model._meta.fields]
        
        if field_labels is None:
            field_labels = field_names
        
        writer = csv.writer(response)
        writer.writerow(field_labels)
        
        for obj in queryset:
            row = []
            for field_name in field_names:
                value = get_nested_value(obj, field_name)
                if hasattr(value, 'strftime'):  # Handle datetime fields
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    value = ''
                row.append(str(value))
            writer.writerow(row)
        
        return response
    
    def export_excel(self, queryset, filename, field_names=None, field_labels=None, sheet_name="Data"):
        """Export queryset to Excel format"""
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        if field_names is None:
            field_names = [field.name for field in queryset.model._meta.fields]
        
        if field_labels is None:
            field_labels = field_names
        
        # Style for header row
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Write header row
        for col, label in enumerate(field_labels, 1):
            cell = ws.cell(row=1, column=col, value=label)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Write data rows
        for row, obj in enumerate(queryset, 2):
            for col, field_name in enumerate(field_names, 1):
                value = get_nested_value(obj, field_name)
                if hasattr(value, 'strftime'):  # Handle datetime fields
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    value = ''
                ws.cell(row=row, column=col, value=str(value))
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        response.write(output.getvalue())
        
        return response
    
    def export_pdf(self, queryset, filename, field_names=None, field_labels=None, title="Data Export"):
        """Export queryset to PDF format"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        
        if field_names is None:
            field_names = [field.name for field in queryset.model._meta.fields]
        
        if field_labels is None:
            field_labels = field_names
        
        # Prepare sample data to determine page orientation
        sample_data = []
        sample_queryset = queryset[:10]  # Get first 10 records for width calculation
        
        for obj in sample_queryset:
            row = []
            for field_name in field_names:
                value = get_nested_value(obj, field_name)
                if hasattr(value, 'strftime'):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    value = ''
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + '...'
                row.append(value_str)
            sample_data.append(row)
        
        # Determine page orientation
        use_landscape = should_use_landscape(field_labels, sample_data)
        
        # Create PDF document with appropriate orientation
        if use_landscape:
            pagesize = landscape(A4)
        else:
            pagesize = A4
            
        doc = SimpleDocTemplate(
            response, 
            pagesize=pagesize, 
            rightMargin=20, 
            leftMargin=20, 
            topMargin=30, 
            bottomMargin=30
        )
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=12 if use_landscape else 14,
            spaceAfter=15 if use_landscape else 20,
            alignment=TA_CENTER
        )
        
        # Add title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 10 if use_landscape else 15))
        
        # Add export info
        export_info = f"Exported on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Records: {queryset.count()}"
        if use_landscape:
            export_info += " | Landscape Mode"
        elements.append(Paragraph(export_info, styles['Normal']))
        elements.append(Spacer(1, 10 if use_landscape else 15))
        
        # Prepare table data
        table_data = [field_labels]  # Header row
        
        # Limit data rows to prevent memory issues and improve performance
        max_rows = 1000  # Limit to 1000 rows per page
        queryset_limited = queryset[:max_rows]
        
        for obj in queryset_limited:
            row = []
            for field_name in field_names:
                value = get_nested_value(obj, field_name)
                if hasattr(value, 'strftime'):  # Handle datetime fields
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    value = ''
                # Truncate long values to prevent table overflow
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + '...'
                row.append(value_str)
            table_data.append(row)
        
        # Calculate column widths based on content and orientation
        col_widths = []
        for i, field_name in enumerate(field_names):
            # Base width on field label length
            base_width = len(field_labels[i]) * (6 if use_landscape else 8)
            
            # Check data content for this column
            max_content_length = base_width
            for row in table_data[1:]:  # Skip header row
                content_length = len(str(row[i])) * (4 if use_landscape else 6)
                max_content_length = max(max_content_length, content_length)
            
            # Cap the width to prevent overflow
            max_width = 80 if use_landscape else 120
            col_width = min(max_content_length, max_width)
            col_widths.append(col_width)
        
        # Create table with calculated column widths
        table = Table(table_data, colWidths=col_widths)
        
        # Improved table styling
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7 if use_landscape else 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6 if use_landscape else 8),
            ('TOPPADDING', (0, 0), (-1, 0), 6 if use_landscape else 8),
            
            # Data row styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 6 if use_landscape else 7),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3 if use_landscape else 4),
            ('TOPPADDING', (0, 1), (-1, -1), 3 if use_landscape else 4),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Text wrapping for long content
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        
        elements.append(table)
        
        # Add note if data was truncated
        if queryset.count() > max_rows:
            elements.append(Spacer(1, 8 if use_landscape else 10))
            note_style = ParagraphStyle(
                'Note',
                parent=styles['Normal'],
                fontSize=7 if use_landscape else 8,
                textColor=colors.grey
            )
            elements.append(Paragraph(f"Note: Showing first {max_rows} records out of {queryset.count()} total records.", note_style))
        
        # Build PDF
        doc.build(elements)
        return response

class ModelExporter:
    """Class to handle model-specific export configurations"""
    
    @staticmethod
    def get_alumni_export_config():
        """Get export configuration for Alumni model"""
        return {
            'field_names': [
                'id', 'user__username', 'user__email', 'user__first_name', 'user__last_name',
                'college', 'graduation_year', 'course', 'current_company', 'job_title', 'is_verified',
                'created_at', 'updated_at'
            ],
            'field_labels': [
                'ID', 'Username', 'Email', 'First Name', 'Last Name',
                'College', 'Graduation Year', 'Course', 'Current Company', 'Job Title', 'Verified',
                'Created At', 'Updated At'
            ],
            'sheet_name': 'Alumni Data'
        }
    
    @staticmethod
    def get_job_export_config():
        """Get export configuration for JobPosting model"""
        return {
            'field_names': [
                'id', 'title', 'company', 'location', 'job_type', 'salary_range',
                'description', 'requirements', 'is_active', 'created_at', 'updated_at'
            ],
            'field_labels': [
                'ID', 'Title', 'Company', 'Location', 'Job Type', 'Salary Range',
                'Description', 'Requirements', 'Active', 'Created At', 'Updated At'
            ],
            'sheet_name': 'Job Postings'
        }
    
    @staticmethod
    def get_mentorship_export_config():
        """Get export configuration for MentorshipRequest model"""
        return {
            'field_names': [
                'id', 'mentor__user__username', 'mentee__user__username',
                'status', 'created_at', 'updated_at'
            ],
            'field_labels': [
                'ID', 'Mentor', 'Mentee', 'Status', 'Created At', 'Updated At'
            ],
            'sheet_name': 'Mentorship Requests'
        }
    
    @staticmethod
    def get_event_export_config():
        """Get export configuration for Event model"""
        return {
            'field_names': [
                'id', 'title', 'description', 'start_date', 'end_date',
                'location', 'is_active', 'created_at', 'updated_at'
            ],
            'field_labels': [
                'ID', 'Title', 'Description', 'Start Date', 'End Date',
                'Location', 'Active', 'Created At', 'Updated At'
            ],
            'sheet_name': 'Events'
        }
    
    @staticmethod
    def get_donation_export_config():
        """Get export configuration for Donation model"""
        return {
            'field_names': [
                'id', 'donor__user__username', 'campaign__title', 'amount',
                'status', 'donation_date', 'created_at'
            ],
            'field_labels': [
                'ID', 'Donor', 'Campaign', 'Amount', 'Status', 'Donation Date', 'Created At'
            ],
            'sheet_name': 'Donations'
        }
    
    @staticmethod
    def get_user_export_config():
        """Get export configuration for User model"""
        return {
            'field_names': [
                'id', 'username', 'email', 'first_name', 'last_name',
                'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login'
            ],
            'field_labels': [
                'ID', 'Username', 'Email', 'First Name', 'Last Name',
                'Active', 'Staff', 'Superuser', 'Date Joined', 'Last Login'
            ],
            'sheet_name': 'Users'
        }
    
    @staticmethod
    def get_announcement_export_config():
        """Get export configuration for Announcement model"""
        return {
            'field_names': [
                'id', 'title', 'content', 'category__name', 'author__username',
                'is_published', 'created_at', 'updated_at'
            ],
            'field_labels': [
                'ID', 'Title', 'Content', 'Category', 'Author',
                'Published', 'Created At', 'Updated At'
            ],
            'sheet_name': 'Announcements'
        }
    
    @staticmethod
    def get_feedback_export_config():
        """Get export configuration for Feedback model"""
        return {
            'field_names': [
                'id', 'user__username', 'subject', 'message', 'rating',
                'status', 'created_at', 'updated_at'
            ],
            'field_labels': [
                'ID', 'User', 'Subject', 'Message', 'Rating',
                'Status', 'Created At', 'Updated At'
            ],
            'sheet_name': 'Feedback'
        }
    
    @staticmethod
    def get_survey_export_config():
        """Get export configuration for Survey model"""
        return {
            'field_names': [
                'id', 'title', 'description', 'status', 'created_by__username',
                'created_at', 'updated_at'
            ],
            'field_labels': [
                'ID', 'Title', 'Description', 'Status', 'Created By',
                'Created At', 'Updated At'
            ],
            'sheet_name': 'Surveys'
        }

def get_export_filename(model_name, format_type):
    """Generate standardized export filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{timestamp}"

def export_queryset(queryset, format_type, model_name, export_config=None):
    """Main export function that handles different formats"""
    if export_config is None:
        export_config = {}
    
    filename = get_export_filename(model_name, format_type)
    
    if format_type == 'csv':
        return ExportMixin().export_csv(
            queryset, 
            filename, 
            export_config.get('field_names'),
            export_config.get('field_labels')
        )
    elif format_type == 'excel':
        return ExportMixin().export_excel(
            queryset, 
            filename, 
            export_config.get('field_names'),
            export_config.get('field_labels'),
            export_config.get('sheet_name', 'Data')
        )
    elif format_type == 'pdf':
        return ExportMixin().export_pdf(
            queryset, 
            filename, 
            export_config.get('field_names'),
            export_config.get('field_labels'),
            export_config.get('sheet_name', 'Data Export')
        )
    else:
        raise ValueError(f"Unsupported format: {format_type}")
