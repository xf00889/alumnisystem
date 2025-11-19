"""
Views for documentation viewer app.
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from pathlib import Path
import logging
import uuid
import re

from .markdown_processor import MarkdownProcessor
from .navigation import NavigationBuilder

logger = logging.getLogger(__name__)


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin to restrict access to admin users only.
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.is_superuser
        )
    
    def handle_no_permission(self):
        """Redirect to login or show 403 if not admin"""
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        # User is authenticated but not admin
        raise Http404("Documentation is only accessible to administrators.")


def validate_doc_path(doc_path: str) -> tuple[bool, str]:
    """
    Validate and sanitize document path for security.
    
    Prevents path traversal attacks and ensures path is safe.
    
    Args:
        doc_path: The document path to validate
        
    Returns:
        Tuple of (is_valid, sanitized_path)
        
    Requirements: 4.3, 4.4
    """
    if not doc_path:
        return False, ""
    
    # Store original for logging
    original_path = doc_path
    
    # Remove any null bytes
    doc_path = doc_path.replace('\x00', '')
    
    # If null bytes were present, reject the path
    if doc_path != original_path:
        logger.warning(f"Null bytes detected in path: {original_path}")
        return False, ""
    
    # Normalize path separators: convert backslashes to forward slashes
    # This handles Windows-style paths that may come from URLs or TOC
    doc_path = doc_path.replace('\\', '/')
    
    # Remove leading/trailing whitespace
    doc_path = doc_path.strip()
    
    # Check for absolute paths BEFORE stripping slashes (both Unix and Windows style)
    if doc_path.startswith('/') or (len(doc_path) > 1 and doc_path[1] == ':'):
        logger.warning(f"Absolute path attempt detected: {original_path}")
        return False, ""
    
    # Check using Path.is_absolute() as well
    if Path(doc_path).is_absolute():
        logger.warning(f"Absolute path attempt detected: {original_path}")
        return False, ""
    
    # Now strip slashes for normalization
    doc_path = doc_path.strip('/')
    
    # Check if path is empty after stripping
    if not doc_path:
        return False, ""
    
    # Check for path traversal attempts
    if '..' in doc_path:
        logger.warning(f"Path traversal attempt detected: {doc_path}")
        return False, ""
    
    # Only allow alphanumeric, hyphens, underscores, slashes, and dots
    if not re.match(r'^[a-zA-Z0-9/_.-]+$', doc_path):
        logger.warning(f"Invalid characters in path: {doc_path}")
        return False, ""
    
    # Ensure path doesn't start with a dot (hidden files)
    parts = doc_path.split('/')
    for part in parts:
        if part.startswith('.'):
            logger.warning(f"Hidden file/folder access attempt: {doc_path}")
            return False, ""
    
    return True, doc_path


class DocumentationIndexView(AdminRequiredMixin, TemplateView):
    """
    Main documentation landing page.
    Displays the table of contents and README content.
    
    Requirements: 1.2, 1.3, 1.4, 4.6, 7.3, 7.5
    """
    template_name = 'docs/index.html'
    
    def get(self, request, *args, **kwargs):
        """
        Override get to store last viewed page in session.
        Requirements: 4.6
        """
        response = super().get(request, *args, **kwargs)
        # Store current page in session for last-viewed tracking
        request.session['docs_last_viewed'] = request.path
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize processors
        nav_builder = NavigationBuilder()
        md_processor = MarkdownProcessor()
        
        # Build table of contents
        try:
            context['toc'] = nav_builder.build_toc()
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(
                f"[Error ID: {error_id}] Error building TOC for index page - User: {self.request.user.username}: {e}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'user': self.request.user.username,
                    'path': self.request.path,
                }
            )
            context['toc'] = []
            context['toc_error'] = True
        
        # Render README.md as the landing page content
        try:
            readme_result = md_processor.render('README.md')
            if readme_result.get('error'):
                error_id = str(uuid.uuid4())
                error_message = readme_result.get('message', 'Error loading documentation')
                logger.error(
                    f"[Error ID: {error_id}] Error rendering README.md: {error_message} - User: {self.request.user.username}",
                    exc_info=True,
                    extra={
                        'error_id': error_id,
                        'user': self.request.user.username,
                        'path': self.request.path,
                        'error_message': error_message,
                    }
                )
                context['content_error'] = True
                context['error_message'] = error_message
            else:
                context['readme_content'] = readme_result.get('html', '')
                context['readme_title'] = readme_result.get('title', 'Documentation')
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(
                f"[Error ID: {error_id}] Unexpected error rendering README: {e} - User: {self.request.user.username}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'user': self.request.user.username,
                    'path': self.request.path,
                }
            )
            context['content_error'] = True
            context['error_message'] = 'Error loading documentation'
        
        context['current_path'] = ''
        context['is_index'] = True
        
        # Add last viewed page to context (for "Continue Reading" feature)
        context['last_viewed_page'] = self.request.session.get('docs_last_viewed')
        
        return context


class DocumentationView(AdminRequiredMixin, TemplateView):
    """
    Individual documentation page view.
    Renders a specific markdown file with navigation.
    
    Requirements: 1.2, 1.3, 1.4, 4.3, 4.4, 4.5, 4.6, 7.1, 7.2, 7.3, 7.4
    """
    template_name = 'docs/document.html'
    
    def get(self, request, *args, **kwargs):
        """
        Override get to handle 404 errors with custom template and store last viewed page.
        Requirements: 4.6, 7.1, 7.2
        """
        try:
            # Validate doc_path before processing
            doc_path = kwargs.get('doc_path', '')
            is_valid, sanitized_path = validate_doc_path(doc_path)
            
            if not is_valid:
                logger.warning(
                    f"Invalid document path rejected: {doc_path} - User: {request.user.username}",
                    extra={
                        'user': request.user.username,
                        'doc_path': doc_path,
                        'path': request.path,
                    }
                )
                raise Http404("Invalid document path")
            
            # Update kwargs with sanitized path
            kwargs['doc_path'] = sanitized_path
            
            context = self.get_context_data(**kwargs)
            
            # Check if we have a 404 error
            if hasattr(self, '_is_404') and self._is_404:
                return render(request, 'docs/404.html', context, status=404)
            
            # Check if we have a rendering error
            if hasattr(self, '_is_error') and self._is_error:
                return render(request, 'docs/error.html', context, status=500)
            
            # Store current page in session for last-viewed tracking
            request.session['docs_last_viewed'] = request.path
            
            response = self.render_to_response(context)
            return response
        except Http404:
            # Re-raise Http404 for proper handling
            raise
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc_path = self.kwargs.get('doc_path', '')
        
        # Initialize processors
        nav_builder = NavigationBuilder()
        md_processor = MarkdownProcessor()
        
        # Ensure doc_path ends with .md
        if not doc_path.endswith('.md'):
            doc_path = doc_path + '.md'
        
        # Build table of contents
        try:
            toc = nav_builder.build_toc()
            context['toc'] = toc
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(
                f"[Error ID: {error_id}] Error building TOC for user {self.request.user.username}: {e}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'user': self.request.user.username,
                    'path': self.request.path,
                }
            )
            context['toc'] = []
            toc = []
        
        # Render the markdown document
        try:
            result = md_processor.render(doc_path)
            
            if result.get('error'):
                # Handle document not found or rendering errors
                error_message = result.get('message', 'Document not found')
                error_id = str(uuid.uuid4())
                
                # Raise 404 for missing documents
                if 'not found' in error_message.lower() or 'does not exist' in error_message.lower():
                    logger.warning(
                        f"[Error ID: {error_id}] Document not found: {doc_path} - User: {self.request.user.username}",
                        extra={
                            'error_id': error_id,
                            'user': self.request.user.username,
                            'doc_path': doc_path,
                            'path': self.request.path,
                        }
                    )
                    self._is_404 = True
                    context['doc_path'] = doc_path
                    context['error_id'] = error_id
                    context['timestamp'] = timezone.now()
                    return context
                
                # For other errors, show error page
                logger.error(
                    f"[Error ID: {error_id}] Error rendering document {doc_path}: {error_message} - User: {self.request.user.username}",
                    exc_info=True,
                    extra={
                        'error_id': error_id,
                        'user': self.request.user.username,
                        'doc_path': doc_path,
                        'path': self.request.path,
                        'error_message': error_message,
                    }
                )
                self._is_error = True
                context['error_message'] = error_message
                context['doc_path'] = doc_path
                context['error_type'] = 'Rendering Error'
                context['error_id'] = error_id
                context['timestamp'] = timezone.now()
                return context
            else:
                context['content'] = result.get('html', '')
                context['title'] = result.get('title', 'Documentation')
                context['doc_toc'] = result.get('toc', '')  # Document-specific TOC
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(
                f"[Error ID: {error_id}] Unexpected error rendering document {doc_path}: {e} - User: {self.request.user.username}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'user': self.request.user.username,
                    'doc_path': doc_path,
                    'path': self.request.path,
                }
            )
            self._is_error = True
            context['error_message'] = 'An unexpected error occurred while loading this document'
            context['doc_path'] = doc_path
            context['error_type'] = 'Unexpected Error'
            context['error_id'] = error_id
            context['timestamp'] = timezone.now()
            return context
        
        # Build breadcrumb navigation
        try:
            context['breadcrumbs'] = nav_builder.build_breadcrumbs(doc_path)
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(
                f"[Error ID: {error_id}] Error building breadcrumbs for {doc_path}: {e}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'user': self.request.user.username,
                    'doc_path': doc_path,
                }
            )
            context['breadcrumbs'] = [{'name': 'Documentation', 'url': '/docs/'}]
        
        # Calculate previous/next navigation
        try:
            prev_next = nav_builder.get_prev_next(doc_path, toc)
            context['prev_doc'] = prev_next.get('prev')
            context['next_doc'] = prev_next.get('next')
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(
                f"[Error ID: {error_id}] Error calculating prev/next for {doc_path}: {e}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'user': self.request.user.username,
                    'doc_path': doc_path,
                }
            )
            context['prev_doc'] = None
            context['next_doc'] = None
        
        context['current_path'] = doc_path
        context['is_index'] = False
        
        return context


class DocumentationSearchView(AdminRequiredMixin, TemplateView):
    """
    Documentation search results page.
    Searches through all markdown files for the query.
    
    Requirements: 4.6, 4.7, 5.1, 5.2, 5.3, 7.5
    """
    template_name = 'docs/search.html'
    
    @method_decorator(ratelimit(key='ip', rate='30/m', method='GET'))
    @method_decorator(ratelimit(key='user', rate='60/m', method='GET'))
    def dispatch(self, request, *args, **kwargs):
        """
        Apply rate limiting to search requests.
        - 30 requests per minute per IP address
        - 60 requests per minute per authenticated user
        
        Requirements: 5.1, 5.2, 5.3
        """
        # Check if rate limit was exceeded
        if getattr(request, 'limited', False):
            from django.http import HttpResponse
            error_id = str(uuid.uuid4())
            logger.warning(
                f"[Error ID: {error_id}] Rate limit exceeded for search - User: {request.user.username if request.user.is_authenticated else 'Anonymous'}, IP: {request.META.get('REMOTE_ADDR')}",
                extra={
                    'error_id': error_id,
                    'user': request.user.username if request.user.is_authenticated else 'Anonymous',
                    'ip': request.META.get('REMOTE_ADDR'),
                    'path': request.path,
                }
            )
            response = HttpResponse(
                "Rate limit exceeded. Please wait a moment before searching again.",
                status=429,
                content_type='text/plain'
            )
            response['Retry-After'] = '60'  # Suggest retry after 60 seconds
            return response
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """
        Override get to store last viewed page in session.
        Requirements: 4.6
        """
        response = super().get(request, *args, **kwargs)
        # Store current page in session for last-viewed tracking
        request.session['docs_last_viewed'] = request.path
        if request.GET.get('q'):
            request.session['docs_last_viewed'] += f"?q={request.GET.get('q')}"
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Import search function
        from .utils import search_documentation, sanitize_search_query, highlight_search_term
        
        # Get and sanitize query
        raw_query = self.request.GET.get('q', '')
        query = sanitize_search_query(raw_query)
        
        # Initialize navigation builder
        nav_builder = NavigationBuilder()
        
        # Build table of contents
        try:
            context['toc'] = nav_builder.build_toc()
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(
                f"[Error ID: {error_id}] Error building TOC for search page - User: {self.request.user.username}: {e}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'user': self.request.user.username,
                    'path': self.request.path,
                    'query': query,
                }
            )
            context['toc'] = []
        
        context['query'] = query
        
        # Perform search if query is valid
        if query and len(query) >= 2:
            try:
                results = search_documentation(query)
                
                # Highlight search terms in results
                for result in results:
                    if result.get('matches'):
                        for match in result['matches']:
                            # Highlight the query in the context
                            match['context'] = highlight_search_term(
                                match['context'], 
                                query, 
                                highlight_class='search-highlight'
                            )
                
                context['results'] = results
                context['result_count'] = len(results)
                
                if len(results) == 0:
                    context['message'] = f'No results found for "{query}".'
                    logger.info(
                        f"Search returned no results - User: {self.request.user.username}, Query: '{query}'",
                        extra={
                            'user': self.request.user.username,
                            'query': query,
                            'result_count': 0,
                        }
                    )
                else:
                    context['message'] = f'Found {len(results)} result{"s" if len(results) != 1 else ""} for "{query}".'
                    logger.info(
                        f"Search completed - User: {self.request.user.username}, Query: '{query}', Results: {len(results)}",
                        extra={
                            'user': self.request.user.username,
                            'query': query,
                            'result_count': len(results),
                        }
                    )
            except Exception as e:
                error_id = str(uuid.uuid4())
                logger.error(
                    f"[Error ID: {error_id}] Error performing search for query '{query}' - User: {self.request.user.username}: {e}",
                    exc_info=True,
                    extra={
                        'error_id': error_id,
                        'user': self.request.user.username,
                        'query': query,
                        'path': self.request.path,
                    }
                )
                context['results'] = []
                context['result_count'] = 0
                context['error'] = True
                context['message'] = 'An error occurred while searching. Please try again.'
        elif query:
            # Query too short
            context['results'] = []
            context['result_count'] = 0
            context['message'] = 'Please enter at least 2 characters to search.'
        else:
            # Empty query
            context['results'] = []
            context['result_count'] = 0
            context['message'] = 'Please enter a search query.'
        
        context['current_path'] = ''
        context['is_search'] = True
        
        return context
