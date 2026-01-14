"""
Validators for unique field validation (email and username).

This module provides case-insensitive uniqueness validation for user registration.
"""

from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UniqueFieldValidator:
    """
    Validates uniqueness of email and username fields (case-insensitive).
    
    This class provides static methods for checking if an email or username
    is already taken in the database, using case-insensitive comparisons.
    """
    
    @staticmethod
    def is_email_taken(email: str, exclude_user_id: int = None) -> bool:
        """
        Check if email exists in the database (case-insensitive).
        
        Args:
            email: The email address to check.
            exclude_user_id: Optional user ID to exclude from the check
                           (useful when updating an existing user's email).
        
        Returns:
            True if the email is already taken, False otherwise.
        """
        if not email:
            return False
        
        # Normalize email for comparison
        normalized_email = UniqueFieldValidator.normalize_email(email)
        
        # Build the query with case-insensitive lookup
        queryset = User.objects.filter(email__iexact=normalized_email)
        
        # Exclude the specified user if provided
        if exclude_user_id is not None:
            queryset = queryset.exclude(id=exclude_user_id)
        
        return queryset.exists()
    
    @staticmethod
    def is_username_taken(username: str, exclude_user_id: int = None) -> bool:
        """
        Check if username exists in the database (case-insensitive).
        
        Args:
            username: The username to check.
            exclude_user_id: Optional user ID to exclude from the check
                           (useful when updating an existing user's username).
        
        Returns:
            True if the username is already taken, False otherwise.
        """
        if not username:
            return False
        
        # Build the query with case-insensitive lookup
        queryset = User.objects.filter(username__iexact=username)
        
        # Exclude the specified user if provided
        if exclude_user_id is not None:
            queryset = queryset.exclude(id=exclude_user_id)
        
        return queryset.exists()
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """
        Normalize email to lowercase.
        
        Args:
            email: The email address to normalize.
        
        Returns:
            The email address converted to lowercase, or empty string if None.
        """
        if not email:
            return ''
        
        return email.lower().strip()
