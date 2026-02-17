"""
Middleware for accounts app.
"""
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class SuppressAuthMessagesMiddleware(MiddlewareMixin):
    """
    Middleware to suppress unwanted authentication messages.
    Removes login/logout success messages that clutter the UI.
    """
    
    def process_response(self, request, response):
        """
        Process response and filter out unwanted messages.
        """
        if hasattr(request, '_messages'):
            storage = messages.get_messages(request)
            filtered_messages = []
            
            for message in storage:
                message_text = str(message).lower()
                
                # Skip login/logout success messages
                if any(keyword in message_text for keyword in [
                    'signed out',
                    'logged out', 
                    'sign out',
                    'log out',
                    'logout',
                    'signed in',
                    'logged in',
                    'successfully signed in',
                    'successfully logged in'
                ]):
                    continue
                
                # Keep all other messages
                filtered_messages.append(message)
            
            # Clear all messages
            storage.used = True
            
            # Re-add only the filtered messages
            for msg in filtered_messages:
                messages.add_message(
                    request,
                    msg.level,
                    msg.message,
                    extra_tags=msg.extra_tags
                )
        
        return response
