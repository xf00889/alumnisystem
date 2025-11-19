# Search Functionality Implementation

## Overview

This document describes the implementation of the search functionality for the documentation viewer system, completed as part of Task 5.

## Implementation Summary

### Files Created/Modified

1. **docs/utils.py** (NEW)
   - Main search functionality module
   - Contains all search-related utility functions

2. **docs/views.py** (MODIFIED)
   - Updated `DocumentationSearchView` to use the new search functionality
   - Added query sanitization and error handling

3. **docs/test_utils.py** (NEW)
   - Comprehensive test suite for search functionality
   - 38 tests covering all aspects of search

## Features Implemented

### 1. Full-Text Search (`search_documentation`)
- Searches across all markdown files in the documentation directory
- Case-insensitive search
- Skips hidden and private files (starting with _ or .)
- Handles nested directories
- Returns structured results with metadata

### 2. Context Extraction (`find_matches_with_context`)
- Extracts text snippets around search matches
- Configurable context length (default: 100 characters)
- Adds ellipsis for truncated content
- Cleans up excessive whitespace
- Limits to 3 matches per file

### 3. Title Extraction (`extract_title`)
- Extracts document title from markdown content
- Looks for first H1 heading (# Title)
- Falls back to H2 heading if no H1 found
- Returns "Untitled" if no heading found

### 4. Relevance Scoring (`calculate_relevance_score`)
Sophisticated scoring algorithm based on:
- Number of query occurrences (1 point each, max 10)
- Query in title (20 points bonus)
- Exact title match (additional 30 points)
- Query in headings (5 points per heading, max 15)
- Early appearance in document (up to 10 points)
- Whole word match (5 points bonus)

### 5. Query Sanitization (`sanitize_search_query`)
- Strips whitespace
- Limits query length (default: 200 characters)
- Removes control characters
- Handles empty and None queries

### 6. Search Term Highlighting (`highlight_search_term`)
- Wraps search terms in HTML span tags
- Case-insensitive highlighting
- Escapes HTML to prevent XSS
- Configurable CSS class

## Error Handling

The implementation includes comprehensive error handling for:
- Empty or invalid queries (minimum 2 characters)
- Nonexistent base paths
- File read errors
- Invalid query types
- Search exceptions

## Security Features

1. **Path Traversal Prevention**: Only searches within the specified base directory
2. **Query Sanitization**: Removes potentially dangerous characters
3. **XSS Prevention**: HTML escaping in highlight function
4. **Input Validation**: Type checking and length limits

## Testing

All functionality is thoroughly tested with 38 unit tests covering:
- Search functionality (9 tests)
- Context extraction (7 tests)
- Title extraction (5 tests)
- Relevance scoring (6 tests)
- Query sanitization (6 tests)
- Term highlighting (6 tests)

**Test Results**: All 38 tests pass ✓

## Usage Example

```python
from docs.utils import search_documentation

# Perform a search
results = search_documentation('admin')

# Results structure:
# [
#     {
#         'path': 'quick-start/admin-guide.md',
#         'title': 'Quick Start Guide for Administrators',
#         'matches': [
#             {
#                 'context': '...text snippet with match...',
#                 'position': 123
#             }
#         ],
#         'url': '/docs/quick-start/admin-guide/',
#         'score': 59.9
#     },
#     ...
# ]
```

## Integration with Views

The `DocumentationSearchView` now:
1. Sanitizes user input
2. Performs the search
3. Displays results with context snippets
4. Shows appropriate messages for empty/invalid queries
5. Handles errors gracefully

## Performance Considerations

- Results are sorted by relevance score
- Search is limited to markdown files only
- Context extraction is limited to 3 matches per file
- Efficient regex-based matching

## Requirements Satisfied

✓ **Requirement 4.7**: Documentation search functionality
✓ **Requirement 7.5**: Error handling for search queries

All acceptance criteria from the requirements document have been met:
- Full-text search across markdown files
- Context extraction around matches
- Title extraction from markdown
- Search result ranking logic
- Empty and invalid query handling

## Next Steps

The search functionality is now complete and ready for integration with the frontend templates (Task 9).
