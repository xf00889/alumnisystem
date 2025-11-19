"""
Utility functions for documentation viewer.

This module provides search functionality and other helper functions
for the documentation system.
"""

from pathlib import Path
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def search_documentation(query: str, base_path: str = 'docs/user-guide') -> List[Dict[str, Any]]:
    """
    Search documentation files for query string.
    
    Performs full-text search across all markdown files in the documentation
    directory and returns results with context snippets.
    
    Args:
        query: Search query string
        base_path: Base directory path for documentation files
    
    Returns:
        List of search result dictionaries, each containing:
            - path: Relative path to the file
            - title: Document title
            - matches: List of match contexts
            - url: URL to the document
            - score: Relevance score for ranking
    
    Requirements: 4.7, 7.5
    """
    # Handle empty and invalid search queries
    if not query or not isinstance(query, str):
        logger.debug("Empty or invalid search query")
        return []
    
    # Strip whitespace and check minimum length
    query = query.strip()
    if len(query) < 2:
        logger.debug(f"Search query too short: {query}")
        return []
    
    results = []
    base = Path(base_path)
    
    # Check if base path exists
    if not base.exists():
        logger.error(f"Documentation base path does not exist: {base_path}")
        return []
    
    try:
        # Search all markdown files
        for md_file in base.rglob('*.md'):
            # Skip hidden and private files
            if any(part.startswith('_') or part.startswith('.') for part in md_file.parts):
                continue
            
            # Security: Skip symlinks to prevent traversal
            if md_file.is_symlink():
                logger.warning(f"Skipping symlink in search: {md_file}")
                continue
            
            # Security: Ensure file is within base_path
            try:
                md_file.resolve().relative_to(base.resolve())
            except ValueError:
                logger.error(f"Path traversal attempt detected in search: {md_file}")
                continue
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Error reading file {md_file}: {e}")
                continue
            
            # Case-insensitive search
            if query.lower() in content.lower():
                # Extract context around matches
                matches = find_matches_with_context(content, query)
                
                # Extract title from content
                title = extract_title(content)
                
                # Calculate relevance score
                score = calculate_relevance_score(content, query, title)
                
                # Build relative path
                relative_path = md_file.relative_to(base)
                
                # Build URL (remove .md extension)
                url_path = str(relative_path.with_suffix('')).replace('\\', '/')
                
                results.append({
                    'path': str(relative_path).replace('\\', '/'),
                    'title': title,
                    'matches': matches,
                    'url': f"/docs/{url_path}/",
                    'score': score,
                })
    
    except Exception as e:
        logger.error(f"Error during documentation search: {e}", exc_info=True)
        return []
    
    # Sort results by relevance score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"Search for '{query}' returned {len(results)} results")
    
    return results


def find_matches_with_context(content: str, query: str, context_length: int = 100) -> List[Dict[str, Any]]:
    """
    Find query matches and extract surrounding context.
    
    Locates all occurrences of the query string in the content and
    extracts a snippet of text around each match for display in
    search results.
    
    Args:
        content: Full text content to search
        query: Search query string
        context_length: Number of characters to include before/after match
    
    Returns:
        List of match dictionaries, each containing:
            - context: Text snippet with the match highlighted
            - position: Character position of the match in content
    
    Requirements: 4.7
    """
    matches = []
    
    # Create case-insensitive regex pattern
    # Escape special regex characters in query
    escaped_query = re.escape(query)
    pattern = re.compile(escaped_query, re.IGNORECASE)
    
    # Find all matches
    for match in pattern.finditer(content):
        start_pos = match.start()
        end_pos = match.end()
        
        # Calculate context boundaries
        context_start = max(0, start_pos - context_length)
        context_end = min(len(content), end_pos + context_length)
        
        # Extract context
        context = content[context_start:context_end]
        
        # Clean up context (remove excessive whitespace, newlines)
        context = ' '.join(context.split())
        
        # Add ellipsis if truncated
        if context_start > 0:
            context = '...' + context
        if context_end < len(content):
            context = context + '...'
        
        matches.append({
            'context': context,
            'position': start_pos,
        })
        
        # Limit to 3 matches per file to avoid overwhelming results
        if len(matches) >= 3:
            break
    
    return matches


def extract_title(content: str) -> str:
    """
    Extract title from markdown content.
    
    Looks for the first H1 heading (# Title) in the markdown content.
    Falls back to the first H2 heading if no H1 is found.
    
    Args:
        content: Raw markdown content
    
    Returns:
        Extracted title or 'Untitled' if no heading found
    
    Requirements: 4.7
    """
    # Look for first H1 heading (# Title)
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    
    # Fallback to H2 heading (## Title)
    h2_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
    if h2_match:
        return h2_match.group(1).strip()
    
    return 'Untitled'


def calculate_relevance_score(content: str, query: str, title: str) -> float:
    """
    Calculate relevance score for search result ranking.
    
    Scores are based on:
    - Number of query occurrences in content
    - Query appearing in title (higher weight)
    - Query appearing in headings (medium weight)
    - Position of first match (earlier is better)
    
    Args:
        content: Full document content
        query: Search query string
        title: Document title
    
    Returns:
        Relevance score (higher is more relevant)
    
    Requirements: 4.7
    """
    score = 0.0
    query_lower = query.lower()
    content_lower = content.lower()
    title_lower = title.lower()
    
    # Count occurrences in content (1 point per occurrence, max 10)
    occurrence_count = content_lower.count(query_lower)
    score += min(occurrence_count, 10)
    
    # Bonus for query in title (20 points)
    if query_lower in title_lower:
        score += 20
    
    # Bonus for exact title match (additional 30 points)
    if query_lower == title_lower:
        score += 30
    
    # Bonus for query in headings (5 points per heading, max 15)
    heading_pattern = re.compile(r'^#+\s+(.+)$', re.MULTILINE)
    headings = heading_pattern.findall(content)
    heading_matches = sum(1 for h in headings if query_lower in h.lower())
    score += min(heading_matches * 5, 15)
    
    # Bonus for early appearance (up to 10 points)
    # Documents where query appears in first 20% get bonus
    first_match_pos = content_lower.find(query_lower)
    if first_match_pos != -1:
        relative_position = first_match_pos / len(content)
        if relative_position < 0.2:
            score += 10 * (1 - relative_position / 0.2)
    
    # Bonus for query as whole word (5 points)
    word_pattern = re.compile(r'\b' + re.escape(query_lower) + r'\b', re.IGNORECASE)
    if word_pattern.search(content):
        score += 5
    
    return score


def sanitize_search_query(query: str, max_length: int = 200) -> str:
    """
    Sanitize search query input for security.
    
    Removes potentially dangerous characters and limits length.
    
    Args:
        query: Raw search query from user input
        max_length: Maximum allowed query length
    
    Returns:
        Sanitized query string
    
    Requirements: 7.5
    """
    if not query:
        return ''
    
    # Strip whitespace
    query = query.strip()
    
    # Limit length
    if len(query) > max_length:
        query = query[:max_length]
    
    # Remove null bytes and other control characters
    query = ''.join(char for char in query if ord(char) >= 32 or char in '\t\n\r')
    
    return query


def highlight_search_term(text: str, query: str, highlight_class: str = 'search-highlight') -> str:
    """
    Highlight search term in text with HTML markup.
    
    Wraps occurrences of the query string in a mark tag for styling.
    
    Args:
        text: Text to process
        query: Search query to highlight
        highlight_class: CSS class for the highlight mark
    
    Returns:
        Text with search terms wrapped in <mark> tags
    
    Note: This function should be used with Django's |safe filter
    
    Requirements: 4.7
    """
    if not query or not text:
        return text
    
    # Escape HTML in text first
    from django.utils.html import escape
    text = escape(text)
    
    # Create case-insensitive pattern
    escaped_query = re.escape(query)
    pattern = re.compile(f'({escaped_query})', re.IGNORECASE)
    
    # Replace with highlighted version using <mark> tag
    highlighted = pattern.sub(
        f'<mark class="{highlight_class}">\\1</mark>',
        text
    )
    
    return highlighted
