"""
File validation utilities for secure file uploads
"""
import os
from django.core.exceptions import ValidationError
from django.conf import settings


# Allowed file extensions for message attachments
ALLOWED_MESSAGE_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.txt',
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.zip', '.rar',
    '.xls', '.xlsx', '.csv',
    '.ppt', '.pptx'
]

# Maximum file size (5MB)
MAX_MESSAGE_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes


def validate_message_attachment(file):
    """
    Validate file attachments for messages
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: If file is invalid
    """
    if not file:
        return
    
    # Check file extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_MESSAGE_EXTENSIONS:
        raise ValidationError(
            f'File type "{ext}" is not allowed. '
            f'Allowed types: {", ".join(ALLOWED_MESSAGE_EXTENSIONS)}'
        )
    
    # Check file size
    if file.size > MAX_MESSAGE_FILE_SIZE:
        max_size_mb = MAX_MESSAGE_FILE_SIZE / (1024 * 1024)
        raise ValidationError(
            f'File size exceeds maximum allowed size of {max_size_mb}MB. '
            f'Your file is {file.size / (1024 * 1024):.2f}MB.'
        )
    
    # Sanitize filename - remove any path components
    file.name = os.path.basename(file.name)
    
    return file


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and other attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    import re
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit filename length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def get_file_extension(filename):
    """
    Get file extension safely
    
    Args:
        filename: Filename
        
    Returns:
        Lowercase file extension including the dot
    """
    return os.path.splitext(filename)[1].lower()


def is_image_file(filename):
    """
    Check if file is an image based on extension
    
    Args:
        filename: Filename
        
    Returns:
        Boolean indicating if file is an image
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    return get_file_extension(filename) in image_extensions
