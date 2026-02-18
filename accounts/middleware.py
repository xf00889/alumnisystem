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
    
    def process_request(self, request):
        """
        Process request and filter out unwanted messages BEFORE template rendering.
        This ensures messages are properly consumed and not re-added.
        """
        if hasattr(request, '_messages'):
            storage = messages.get_messages(request)
            
            # Collect messages we want to keep
            messages_to_keep = []
            
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
                messages_to_keep.append({
                    'level': message.level,
                    'message': message.message,
                    'extra_tags': message.extra_tags
                })
            
            # Messages are now consumed (storage was iterated)
            # Re-add only the filtered messages
            for msg in messages_to_keep:
                messages.add_message(
                    request,
                    msg['level'],
                    msg['message'],
                    extra_tags=msg['extra_tags']
                )
        
        return None
    
    def process_response(self, request, response):
        """
        No longer needed - filtering happens in process_request.
        """
        return response
