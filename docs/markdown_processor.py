"""
Markdown processing module for documentation viewer.

This module handles rendering markdown files to HTML with caching,
syntax highlighting, and relative link processing.
"""

import markdown
from markdown.extensions import fenced_code, tables, toc, codehilite, nl2br, sane_lists
from pathlib import Path
from django.core.cache import cache
from django.conf import settings
import hashlib
import re
import logging
from typing import Optional, Dict, Any
import bleach

logger = logging.getLogger(__name__)


class MarkdownProcessor:
    """
    Processes markdown files and converts them to HTML with caching.
    
    Features:
    - GitHub-style markdown rendering
    - Syntax highlighting for code blocks
    - Table support
    - Table of contents generation
    - Relative link conversion (.md -> URLs)
    - File modification time-based caching
    """
    
    def __init__(self, base_path: str = 'docs/user-guide'):
        """
        Initialize the markdown processor.
        
        Args:
            base_path: Base directory path for documentation files
        """
        self.base_path = Path(base_path)
        
        # Configure markdown extensions
        self.extensions = [
            'fenced_code',      # GitHub-style code blocks
            'tables',           # Table support
            'toc',              # Table of contents
            'codehilite',       # Syntax highlighting
            'nl2br',            # Convert newlines to <br>
            'sane_lists',       # Better list handling
        ]
        
        # Extension configuration
        self.extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'linenums': False,
                'guess_lang': True,
            },
            'toc': {
                'permalink': True,
                'permalink_class': 'headerlink',
                'permalink_title': 'Permanent link',
            },
        }
        
        # Configure allowed HTML tags and attributes for XSS prevention
        # These are safe tags that markdown can generate
        self.allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div',
            'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li',
            'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th',
            'thead', 'tr', 'ul', 'dl', 'dt', 'dd', 'mark', 'del', 'ins', 'sup',
            'sub', 'kbd', 'samp', 'var', 'cite', 'q', 'dfn', 'small'
        ]
        
        # Configure allowed attributes for each tag
        self.allowed_attributes = {
            'a': ['href', 'title', 'class', 'id'],
            'abbr': ['title'],
            'acronym': ['title'],
            'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
            'div': ['class', 'id'],
            'span': ['class', 'id'],
            'code': ['class'],
            'pre': ['class'],
            'h1': ['id', 'class'],
            'h2': ['id', 'class'],
            'h3': ['id', 'class'],
            'h4': ['id', 'class'],
            'h5': ['id', 'class'],
            'h6': ['id', 'class'],
            'table': ['class'],
            'td': ['colspan', 'rowspan', 'class'],
            'th': ['colspan', 'rowspan', 'class', 'scope'],
            'ol': ['start', 'type', 'class'],
            'ul': ['class'],
            'li': ['class'],
        }
        
        # Configure allowed URL protocols
        self.allowed_protocols = ['http', 'https', 'mailto', 'ftp']
    
    def render(self, file_path: str) -> Dict[str, Any]:
        """
        Render a markdown file to HTML with caching.
        
        Args:
            file_path: Relative path to markdown file from base_path
            
        Returns:
            Dictionary containing:
                - html: Rendered HTML content
                - toc: Table of contents HTML (if generated)
                - title: Extracted document title
                - error: Error flag (if rendering failed)
                - message: Error message (if applicable)
        """
        try:
            full_path = self.base_path / file_path
            
            # Validate file exists and is within base path
            if not full_path.exists():
                logger.warning(f"Markdown file not found: {full_path}")
                return {
                    'error': True,
                    'message': 'Document not found',
                    'file_path': file_path,
                }
            
            # Security: Ensure file is within base_path (prevent path traversal)
            try:
                full_path.resolve().relative_to(self.base_path.resolve())
            except ValueError:
                logger.error(f"Path traversal attempt detected: {file_path}")
                return {
                    'error': True,
                    'message': 'Invalid file path',
                }
            
            # Generate cache key based on file path and modification time
            cache_key = self._get_cache_key(full_path)
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {file_path}")
                return cached_result
            
            # Read markdown content
            logger.debug(f"Reading and rendering {file_path}")
            with open(full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Create markdown instance
            md = markdown.Markdown(
                extensions=self.extensions,
                extension_configs=self.extension_configs,
            )
            
            # Render to HTML
            html = md.convert(md_content)
            
            # Process relative links to convert .md to URLs
            html = self._process_links(html, file_path)
            
            # Sanitize HTML to prevent XSS attacks
            # This removes any potentially dangerous HTML/JavaScript
            html = self._sanitize_html(html)
            
            # Extract title from content
            title = self._extract_title(md_content)
            
            # Build result
            result = {
                'html': html,
                'toc': md.toc if hasattr(md, 'toc') else '',
                'title': title,
                'error': False,
            }
            
            # Cache the result (1 hour timeout)
            cache.set(cache_key, result, timeout=3600)
            logger.debug(f"Cached result for {file_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error rendering markdown file {file_path}: {e}", exc_info=True)
            return {
                'error': True,
                'message': f'Error rendering document: {str(e)}',
                'file_path': file_path,
            }
    
    def _get_cache_key(self, file_path: Path) -> str:
        """
        Generate cache key based on file path and modification time.
        
        This ensures cache is invalidated when file is modified.
        
        Args:
            file_path: Full path to the file
            
        Returns:
            Cache key string
        """
        try:
            mtime = file_path.stat().st_mtime
            content = f"{file_path}:{mtime}"
            hash_digest = hashlib.md5(content.encode()).hexdigest()
            return f"docs_md_{hash_digest}"
        except Exception as e:
            logger.error(f"Error generating cache key for {file_path}: {e}")
            # Fallback to path-only cache key
            hash_digest = hashlib.md5(str(file_path).encode()).hexdigest()
            return f"docs_md_{hash_digest}"
    
    def _process_links(self, html: str, current_file: str) -> str:
        """
        Convert relative markdown links to proper documentation URLs.
        
        Converts links like:
        - [text](../other-doc.md) -> /docs/other-doc/
        - [text](folder/doc.md) -> /docs/folder/doc/
        - [text](http://example.com) -> unchanged (external)
        
        Args:
            html: Rendered HTML content
            current_file: Current file path (for resolving relative links)
            
        Returns:
            HTML with processed links
        """
        current_path = Path(current_file).parent
        
        def replace_link(match):
            href = match.group(1)
            
            # Skip external links (http://, https://, mailto:, etc.)
            if re.match(r'^[a-zA-Z]+:', href):
                return match.group(0)
            
            # Skip anchor links
            if href.startswith('#'):
                return match.group(0)
            
            # Process .md links
            if href.endswith('.md'):
                # Remove .md extension
                href = href[:-3]
                
                # Resolve relative path
                if href.startswith('/'):
                    # Absolute path from docs root
                    resolved = href.lstrip('/')
                else:
                    # Relative path
                    resolved = (current_path / href).as_posix()
                
                # Normalize path (remove .., ., etc.)
                resolved = Path(resolved).as_posix()
                
                # Build documentation URL
                new_href = f"/docs/{resolved}/"
                return f'href="{new_href}"'
            
            return match.group(0)
        
        # Replace href attributes in anchor tags
        html = re.sub(r'href="([^"]+)"', replace_link, html)
        
        return html
    
    def _sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML to prevent XSS attacks.
        
        Uses bleach library to remove potentially dangerous HTML/JavaScript
        while preserving safe markdown-generated HTML.
        
        Args:
            html: Raw HTML from markdown rendering
            
        Returns:
            Sanitized HTML safe for display
            
        Requirements: 1.3 (XSS Prevention)
        """
        try:
            # Use bleach to sanitize HTML
            sanitized = bleach.clean(
                html,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                protocols=self.allowed_protocols,
                strip=True,  # Strip disallowed tags instead of escaping
            )
            
            # Also linkify any plain URLs (optional, but safe)
            # This converts plain text URLs to clickable links
            sanitized = bleach.linkify(
                sanitized,
                callbacks=[],
                skip_tags=['pre', 'code'],  # Don't linkify in code blocks
            )
            
            return sanitized
        except Exception as e:
            logger.error(f"Error sanitizing HTML: {e}", exc_info=True)
            # If sanitization fails, escape everything as a safety measure
            from django.utils.html import escape
            return escape(html)
    
    def _extract_title(self, md_content: str) -> str:
        """
        Extract title from markdown content.
        
        Looks for the first H1 heading (# Title).
        
        Args:
            md_content: Raw markdown content
            
        Returns:
            Extracted title or 'Untitled'
        """
        # Look for first H1 heading
        match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        return 'Untitled'
    
    def invalidate_cache(self, file_path: Optional[str] = None) -> None:
        """
        Invalidate cached markdown rendering.
        
        Args:
            file_path: Specific file to invalidate, or None to clear all
        """
        if file_path:
            full_path = self.base_path / file_path
            if full_path.exists():
                cache_key = self._get_cache_key(full_path)
                cache.delete(cache_key)
                logger.info(f"Invalidated cache for {file_path}")
        else:
            # Clear all documentation caches
            # Note: This is a simple implementation. For production,
            # consider using cache key patterns or tags
            logger.info("Cache invalidation requested for all docs")
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a markdown file.
        
        Args:
            file_path: Relative path to markdown file
            
        Returns:
            Dictionary with file metadata or None if file doesn't exist
        """
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                'path': file_path,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'exists': True,
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
