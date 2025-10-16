"""
Custom session middleware with database fallback.
"""
import logging
import os
import json
import tempfile
import time
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import ImproperlyConfigured
from django.utils.http import http_date

logger = logging.getLogger(__name__)


class FileBasedSessionStore(SessionBase):
    """
    File-based session store for fallback when database is not available.
    """
    
    def __init__(self, session_key=None):
        super().__init__(session_key)
        self.session_dir = getattr(settings, 'SESSION_FILE_PATH', tempfile.gettempdir())
        os.makedirs(self.session_dir, exist_ok=True)
    
    def _get_session_file_path(self, session_key):
        """Get the file path for a session key."""
        return os.path.join(self.session_dir, f'session_{session_key}.json')
    
    def load(self):
        """Load session data from file."""
        if not self.session_key:
            return {}
        
        session_file = self._get_session_file_path(self.session_key)
        try:
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f'Failed to load session from file: {e}')
        
        return {}
    
    def exists(self, session_key):
        """Check if session exists in file."""
        if not session_key:
            return False
        return os.path.exists(self._get_session_file_path(session_key))
    
    def create(self):
        """Create a new session."""
        while True:
            self.session_key = self._get_new_session_key()
            if not self.exists(self.session_key):
                break
        self.save(must_create=True)
        self.modified = True
        return True
    
    def save(self, must_create=False):
        """Save session data to file."""
        if not self.session_key:
            return
        
        session_file = self._get_session_file_path(self.session_key)
        try:
            with open(session_file, 'w') as f:
                json.dump(self._session, f)
        except IOError as e:
            logger.error(f'Failed to save session to file: {e}')
            raise
    
    def delete(self, session_key=None):
        """Delete session file."""
        if session_key is None:
            session_key = self.session_key
        
        if session_key:
            session_file = self._get_session_file_path(session_key)
            try:
                if os.path.exists(session_file):
                    os.remove(session_file)
            except IOError as e:
                logger.warning(f'Failed to delete session file: {e}')


class DatabaseFallbackSessionMiddleware(SessionMiddleware):
    """
    Session middleware that falls back to file-based sessions when database is not available.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self._database_available = None
    
    def _is_database_available(self):
        """Check if database is available for sessions."""
        if self._database_available is None:
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                self._database_available = True
                logger.info("Database available for sessions")
            except Exception as e:
                self._database_available = False
                logger.warning(f"Database not available for sessions: {e}")
        
        return self._database_available
    
    def process_request(self, request):
        """Process the request and set up session."""
        # Check if we're in setup mode and database is not available
        if (request.path.startswith('/setup/') and 
            not self._is_database_available()):
            
            # Use file-based session for setup
            session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
            request.session = FileBasedSessionStore(session_key)
            logger.info("Using file-based session for setup")
        else:
            # Use normal database-based session
            super().process_request(request)
    
    def process_response(self, request, response):
        """Process the response and save session."""
        # Check if we're in setup mode and database is not available
        if (request.path.startswith('/setup/') and 
            not self._is_database_available()):
            
            # Handle file-based session
            if hasattr(request, 'session') and request.session:
                if request.session.accessed:
                    patch_vary_headers = hasattr(response, 'patch_vary_headers')
                    if patch_vary_headers:
                        response.patch_vary_headers(['Cookie'])
                    
                    if request.session.modified or request.session.get_expire_at_browser_close():
                        max_age = request.session.get_expiry_age()
                        expires_time = time.time() + max_age
                        expires = http_date(expires_time)
                        
                        response.set_cookie(
                            settings.SESSION_COOKIE_NAME,
                            request.session.session_key,
                            max_age=max_age,
                            expires=expires,
                            domain=settings.SESSION_COOKIE_DOMAIN,
                            path=settings.SESSION_COOKIE_PATH,
                            secure=settings.SESSION_COOKIE_SECURE,
                            httponly=settings.SESSION_COOKIE_HTTPONLY,
                            samesite=settings.SESSION_COOKIE_SAMESITE,
                        )
            
            return response
        else:
            # Use normal database-based session
            return super().process_response(request, response)
