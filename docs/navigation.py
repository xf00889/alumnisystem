"""
Navigation builder module for documentation viewer.

This module provides functionality to:
- Generate table of contents from directory structure
- Build breadcrumb navigation
- Calculate previous/next document links
- Cache navigation structures for performance
"""

from pathlib import Path
from django.core.cache import cache
import os
import logging

logger = logging.getLogger(__name__)


class NavigationBuilder:
    """
    Builds navigation structures for the documentation viewer.
    
    Handles TOC generation, breadcrumbs, and sequential navigation.
    """
    
    # Internal documentation files to exclude from TOC
    EXCLUDED_FILES = {
        'COMPLETION_REPORT.md',
        'DOCUMENTATION_INDEX.md',
        'DOCUMENTATION_SUMMARY.md',
        'FINAL_REVIEW_CHECKLIST.md',
        'TECHNICAL_REVIEW.md',
        'USER_TESTING_FEEDBACK_FORM.md',
        'USER_TESTING_PLAN.md',
        'USER_TESTING_TASKS.md',
        '_template.md',
        'SCREENSHOTS_NOTE.md',
    }
    
    def __init__(self, base_path='docs/user-guide'):
        """
        Initialize the navigation builder.
        
        Args:
            base_path: Path to the documentation root directory
        """
        self.base_path = Path(base_path)
        
        if not self.base_path.exists():
            logger.warning(f"Documentation path does not exist: {self.base_path}")
    
    def build_toc(self):
        """
        Build table of contents from directory structure.
        
        Scans the documentation directory and creates a hierarchical
        structure representing folders and markdown files.
        
        Returns:
            list: Hierarchical list of folders and files with metadata
        """
        cache_key = 'docs_toc_structure'
        cached_toc = cache.get(cache_key)
        
        if cached_toc:
            logger.debug("Returning cached TOC structure")
            return cached_toc
        
        logger.info("Building TOC structure from filesystem")
        toc = self._scan_directory(self.base_path)
        
        # Cache for 1 hour
        cache.set(cache_key, toc, timeout=3600)
        
        return toc
    
    def _scan_directory(self, path, level=0):
        """
        Recursively scan directory and build TOC structure.
        
        Security: Only scans within base_path to prevent directory traversal.
        
        Args:
            path: Path object to scan
            level: Current nesting level (for hierarchy)
        
        Returns:
            list: List of folder and file dictionaries
            
        Requirements: 1.3 (Path Traversal Prevention)
        """
        items = []
        
        if not path.exists() or not path.is_dir():
            return items
        
        # Security check: Ensure path is within base_path
        try:
            path.resolve().relative_to(self.base_path.resolve())
        except ValueError:
            logger.error(f"Path traversal attempt detected in navigation: {path}")
            return items
        
        try:
            # Get all items in directory and sort them
            dir_items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in dir_items:
                # Skip hidden files and private directories
                if item.name.startswith('.') or item.name.startswith('_'):
                    continue
                
                # Additional security: Skip symlinks to prevent traversal
                if item.is_symlink():
                    logger.warning(f"Skipping symlink in documentation: {item}")
                    continue
                
                # Security check: Ensure item is within base_path
                try:
                    item.resolve().relative_to(self.base_path.resolve())
                except ValueError:
                    logger.error(f"Path traversal attempt detected: {item}")
                    continue
                
                if item.is_dir():
                    # Process folder
                    # Normalize path separators to forward slashes for URLs
                    folder_path = str(item.relative_to(self.base_path)).replace('\\', '/')
                    folder_data = {
                        'type': 'folder',
                        'name': self._format_name(item.name),
                        'path': folder_path,
                        'level': level,
                        'children': self._scan_directory(item, level + 1),
                        'has_readme': (item / 'README.md').exists(),
                    }
                    items.append(folder_data)
                
                elif item.suffix == '.md':
                    # Skip internal documentation files
                    if item.name in self.EXCLUDED_FILES:
                        continue
                    
                    # Process markdown file
                    # Normalize path separators to forward slashes for URLs
                    file_path = str(item.relative_to(self.base_path)).replace('\\', '/')
                    file_data = {
                        'type': 'file',
                        'name': self._format_name(item.stem),
                        'path': file_path,
                        'level': level,
                    }
                    items.append(file_data)
        
        except PermissionError:
            logger.error(f"Permission denied accessing directory: {path}")
        except Exception as e:
            logger.error(f"Error scanning directory {path}: {e}")
        
        return items
    
    def _format_name(self, name):
        """
        Convert filename to display name.
        
        Transforms technical filenames into human-readable titles:
        - README -> Overview
        - kebab-case -> Title Case
        - snake_case -> Title Case
        
        Args:
            name: Original filename or directory name
        
        Returns:
            str: Formatted display name
        """
        # Special case for README files
        if name.upper() == 'README':
            return 'Overview'
        
        # Convert kebab-case and snake_case to Title Case
        formatted = name.replace('-', ' ').replace('_', ' ')
        
        # Capitalize each word
        return formatted.title()
    
    def build_breadcrumbs(self, doc_path):
        """
        Build breadcrumb navigation for current path.
        
        Creates a trail of links from the documentation root to the
        current document, showing the hierarchy.
        
        Args:
            doc_path: Relative path to current document
        
        Returns:
            list: List of breadcrumb dictionaries with name and url
        """
        breadcrumbs = [{'name': 'Documentation', 'url': '/docs/'}]
        
        if not doc_path:
            return breadcrumbs
        
        # Normalize path separators to forward slashes for URLs
        doc_path = doc_path.replace('\\', '/')
        
        # Parse the path into parts
        path_obj = Path(doc_path)
        parts = path_obj.parts
        
        # Build breadcrumbs for each directory level
        current_path = ''
        for i, part in enumerate(parts):
            if current_path:
                current_path = current_path + '/' + part
            else:
                current_path = part
            
            # For the last part (the file), don't add a link
            if i == len(parts) - 1:
                # Remove .md extension if present
                display_name = Path(part).stem if part.endswith('.md') else part
                breadcrumbs.append({
                    'name': self._format_name(display_name),
                    'url': None,  # Current page, no link
                })
            else:
                # For directories, add a link
                breadcrumbs.append({
                    'name': self._format_name(part),
                    'url': f'/docs/{current_path}/',
                })
        
        return breadcrumbs
    
    def get_prev_next(self, current_path, toc=None):
        """
        Calculate previous and next documents in sequence.
        
        Determines which documents come before and after the current
        document in the linear reading order.
        
        Args:
            current_path: Path to current document
            toc: Table of contents structure (will be built if not provided)
        
        Returns:
            dict: Dictionary with 'prev' and 'next' document info
        """
        if toc is None:
            toc = self.build_toc()
        
        # Flatten the hierarchical TOC into a sequential list
        flat_list = self._flatten_toc(toc)
        
        # Find the current document in the flat list
        try:
            current_index = next(
                i for i, item in enumerate(flat_list)
                if item['path'] == current_path
            )
        except StopIteration:
            logger.warning(f"Current path not found in TOC: {current_path}")
            return {'prev': None, 'next': None}
        
        # Get previous and next documents
        prev_doc = flat_list[current_index - 1] if current_index > 0 else None
        next_doc = flat_list[current_index + 1] if current_index < len(flat_list) - 1 else None
        
        return {
            'prev': prev_doc,
            'next': next_doc,
        }
    
    def _flatten_toc(self, toc):
        """
        Flatten hierarchical TOC to sequential list.
        
        Converts the nested folder/file structure into a linear list
        of documents in reading order.
        
        Args:
            toc: Hierarchical TOC structure
        
        Returns:
            list: Flat list of file items only
        """
        flat = []
        
        for item in toc:
            if item['type'] == 'file':
                flat.append(item)
            elif item['type'] == 'folder' and 'children' in item:
                # Recursively flatten children
                flat.extend(self._flatten_toc(item['children']))
        
        return flat
    
    def invalidate_cache(self):
        """
        Invalidate the cached TOC structure.
        
        Call this when the documentation structure changes
        (files added, removed, or renamed).
        """
        cache_key = 'docs_toc_structure'
        cache.delete(cache_key)
        logger.info("TOC cache invalidated")
    
    def get_document_count(self, toc=None):
        """
        Get the total count of documentation files.
        
        Args:
            toc: Table of contents structure (will be built if not provided)
        
        Returns:
            int: Total number of markdown files
        """
        if toc is None:
            toc = self.build_toc()
        
        flat_list = self._flatten_toc(toc)
        return len(flat_list)
