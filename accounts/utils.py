"""
Utility functions for accounts app
"""
from django.contrib.auth import get_user_model

User = get_user_model()

def get_user_display(user):
    """
    Custom user display function for Django Allauth
    Returns the user's full name or username
    """
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return user.username
    else:
        return user.email