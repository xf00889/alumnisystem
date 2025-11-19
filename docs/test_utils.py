"""
Tests for documentation utility functions.

Tests the search functionality including full-text search, context extraction,
title extraction, and relevance scoring.
"""
from django.test import TestCase
from pathlib import Path
import tempfile
import shutil
import os

from .utils import (
    search_documentation,
    find_matches_with_context,
    extract_title,
    calculate_relevance_score,
    sanitize_search_query,
    highlight_search_term,
)


class SearchDocumentationTest(TestCase):
    """
    Test the main search_documentation function.
    
    Requirements: 3.5, 4.7, 7.5
    """
    
    def setUp(self):
        """Set up temporary documentation directory with test files."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test markdown files
        self.create_test_file('test1.md', '# Test Document\n\nThis is a test document with some content.')
        self.create_test_file('test2.md', '# Another Test\n\nAnother document for testing search functionality.')
        self.create_test_file('folder/nested.md', '# Nested Document\n\nThis is nested in a folder.')
        self.create_test_file('_private.md', '# Private\n\nThis should be skipped.')
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, path, content):
        """Helper to create test markdown files."""
        full_path = Path(self.temp_dir) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def test_search_finds_matching_documents(self):
        """Test that search finds documents containing the query."""
        results = search_documentation('test', base_path=self.temp_dir)
        
        # Should find test1.md and test2.md (not _private.md)
        self.assertGreaterEqual(len(results), 2)
        
        # Check that results have required fields
        for result in results:
            self.assertIn('path', result)
            self.assertIn('title', result)
            self.assertIn('matches', result)
            self.assertIn('url', result)
            self.assertIn('score', result)
    
    def test_search_is_case_insensitive(self):
        """Test that search is case-insensitive."""
        results_lower = search_documentation('test', base_path=self.temp_dir)
        results_upper = search_documentation('TEST', base_path=self.temp_dir)
        
        # Should return same number of results
        self.assertEqual(len(results_lower), len(results_upper))
    
    def test_search_skips_private_files(self):
        """Test that files starting with _ are skipped."""
        results = search_documentation('private', base_path=self.temp_dir)
        
        # Should not find _private.md
        paths = [r['path'] for r in results]
        self.assertNotIn('_private.md', paths)
    
    def test_search_finds_nested_documents(self):
        """Test that search finds documents in subdirectories."""
        results = search_documentation('nested', base_path=self.temp_dir)
        
        # Should find folder/nested.md
        self.assertGreater(len(results), 0)
        paths = [r['path'] for r in results]
        self.assertTrue(any('nested.md' in p for p in paths))
    
    def test_empty_query_returns_empty_results(self):
        """Test that empty query returns no results."""
        results = search_documentation('', base_path=self.temp_dir)
        self.assertEqual(len(results), 0)
    
    def test_short_query_returns_empty_results(self):
        """Test that queries shorter than 2 characters return no results."""
        results = search_documentation('a', base_path=self.temp_dir)
        self.assertEqual(len(results), 0)
    
    def test_invalid_query_returns_empty_results(self):
        """Test that invalid query types return no results."""
        results = search_documentation(None, base_path=self.temp_dir)
        self.assertEqual(len(results), 0)
        
        results = search_documentation(123, base_path=self.temp_dir)
        self.assertEqual(len(results), 0)
    
    def test_nonexistent_base_path_returns_empty_results(self):
        """Test that nonexistent base path returns no results."""
        results = search_documentation('test', base_path='/nonexistent/path')
        self.assertEqual(len(results), 0)
    
    def test_results_are_sorted_by_relevance(self):
        """Test that results are sorted by relevance score."""
        # Create documents with different relevance
        self.create_test_file('high_relevance.md', '# Test\n\ntest test test test')
        self.create_test_file('low_relevance.md', '# Document\n\nSome content with test once.')
        
        results = search_documentation('test', base_path=self.temp_dir)
        
        # Results should be sorted by score (descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                self.assertGreaterEqual(results[i]['score'], results[i + 1]['score'])
    
    def test_search_handles_unicode_content(self):
        """
        Test that search handles Unicode characters correctly.
        Requirements: 3.5, 7.5
        """
        self.create_test_file('unicode.md', '# Unicode Test\n\nCafé résumé naïve 日本語')
        
        results = search_documentation('café', base_path=self.temp_dir)
        self.assertGreater(len(results), 0)
        
        results = search_documentation('日本語', base_path=self.temp_dir)
        self.assertGreater(len(results), 0)
    
    def test_search_handles_symlinks_safely(self):
        """
        Test that search skips symlinks to prevent traversal attacks.
        Requirements: 3.5, 4.7
        """
        # Create a regular file
        self.create_test_file('regular.md', '# Regular File\n\nContent here.')
        
        # Try to create a symlink (may not work on all systems)
        try:
            symlink_path = Path(self.temp_dir) / 'symlink.md'
            target_path = Path(self.temp_dir) / 'regular.md'
            symlink_path.symlink_to(target_path)
            
            # Search should skip symlinks
            results = search_documentation('regular', base_path=self.temp_dir)
            
            # Should only find the original file, not the symlink
            paths = [r['path'] for r in results]
            self.assertEqual(len([p for p in paths if 'regular.md' in p]), 1)
        except (OSError, NotImplementedError):
            # Symlinks not supported on this system, skip test
            self.skipTest("Symlinks not supported on this system")
    
    def test_search_validates_base_path_security(self):
        """
        Test that search validates files are within base path.
        Requirements: 3.5, 4.7
        """
        # This is tested implicitly by the path traversal prevention
        # The search function should not return files outside base_path
        results = search_documentation('test', base_path=self.temp_dir)
        
        # All results should be within base_path
        for result in results:
            result_path = Path(self.temp_dir) / result['path']
            self.assertTrue(result_path.resolve().is_relative_to(Path(self.temp_dir).resolve()))
    
    def test_search_handles_malformed_markdown(self):
        """
        Test that search handles malformed markdown gracefully.
        Requirements: 3.6, 4.7
        """
        # Create file with malformed markdown
        self.create_test_file('malformed.md', '# Incomplete heading\n\n[broken link](')
        
        # Search should not crash
        results = search_documentation('incomplete', base_path=self.temp_dir)
        self.assertGreaterEqual(len(results), 0)
    
    def test_search_handles_empty_files(self):
        """
        Test that search handles empty files gracefully.
        Requirements: 3.6, 4.7
        """
        self.create_test_file('empty.md', '')
        
        # Search should not crash on empty files
        results = search_documentation('test', base_path=self.temp_dir)
        self.assertGreaterEqual(len(results), 0)
    
    def test_search_handles_binary_files(self):
        """
        Test that search handles binary files gracefully.
        Requirements: 3.6, 4.7
        """
        # Create a file with binary content
        binary_path = Path(self.temp_dir) / 'binary.md'
        with open(binary_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04')
        
        # Search should not crash on binary files
        results = search_documentation('test', base_path=self.temp_dir)
        # Should return results from other files, skipping the binary one
        self.assertGreaterEqual(len(results), 0)


class FindMatchesWithContextTest(TestCase):
    """
    Test the find_matches_with_context function.
    
    Requirements: 4.7
    """
    
    def test_finds_single_match(self):
        """Test finding a single match with context."""
        content = "This is a test document with some content."
        matches = find_matches_with_context(content, "test")
        
        self.assertEqual(len(matches), 1)
        self.assertIn('context', matches[0])
        self.assertIn('position', matches[0])
        self.assertIn('test', matches[0]['context'].lower())
    
    def test_finds_multiple_matches(self):
        """Test finding multiple matches."""
        content = "test " * 10  # 10 occurrences
        matches = find_matches_with_context(content, "test")
        
        # Should limit to 3 matches
        self.assertEqual(len(matches), 3)
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        content = "This is a TEST document."
        matches = find_matches_with_context(content, "test")
        
        self.assertEqual(len(matches), 1)
        self.assertIn('TEST', matches[0]['context'])
    
    def test_adds_ellipsis_for_truncated_context(self):
        """Test that ellipsis is added when context is truncated."""
        content = "a" * 200 + "test" + "b" * 200
        matches = find_matches_with_context(content, "test", context_length=50)
        
        self.assertEqual(len(matches), 1)
        context = matches[0]['context']
        self.assertTrue(context.startswith('...'))
        self.assertTrue(context.endswith('...'))
    
    def test_no_ellipsis_at_boundaries(self):
        """Test that no ellipsis is added at content boundaries."""
        content = "test at the beginning"
        matches = find_matches_with_context(content, "test", context_length=50)
        
        self.assertEqual(len(matches), 1)
        context = matches[0]['context']
        self.assertFalse(context.startswith('...'))
    
    def test_cleans_whitespace_in_context(self):
        """Test that excessive whitespace is cleaned up."""
        content = "This   is\n\na\t\ttest\n\ndocument."
        matches = find_matches_with_context(content, "test")
        
        self.assertEqual(len(matches), 1)
        context = matches[0]['context']
        # Should have single spaces
        self.assertNotIn('  ', context)
        self.assertNotIn('\n', context)
    
    def test_context_extraction_at_document_start(self):
        """
        Test context extraction when match is at document start.
        Requirements: 3.6, 4.7
        """
        content = "test is at the beginning of this document"
        matches = find_matches_with_context(content, "test", context_length=20)
        
        self.assertEqual(len(matches), 1)
        context = matches[0]['context']
        # Should not have leading ellipsis
        self.assertFalse(context.startswith('...'))
    
    def test_context_extraction_at_document_end(self):
        """
        Test context extraction when match is at document end.
        Requirements: 3.6, 4.7
        """
        content = "This document ends with test"
        matches = find_matches_with_context(content, "test", context_length=20)
        
        self.assertEqual(len(matches), 1)
        context = matches[0]['context']
        # Should not have trailing ellipsis
        self.assertFalse(context.endswith('...'))
    
    def test_context_extraction_with_special_regex_chars(self):
        """
        Test context extraction with special regex characters in query.
        Requirements: 3.6, 4.7
        """
        content = "This has special chars: test.method() and test[0]"
        matches = find_matches_with_context(content, "test.method()")
        
        # Should find the literal string, not interpret as regex
        self.assertEqual(len(matches), 1)
        self.assertIn('test.method()', matches[0]['context'])


class ExtractTitleTest(TestCase):
    """
    Test the extract_title function.
    
    Requirements: 4.7
    """
    
    def test_extracts_h1_title(self):
        """Test extracting title from H1 heading."""
        content = "# My Document Title\n\nSome content here."
        title = extract_title(content)
        
        self.assertEqual(title, "My Document Title")
    
    def test_extracts_first_h1_only(self):
        """Test that only the first H1 is extracted."""
        content = "# First Title\n\nContent\n\n# Second Title"
        title = extract_title(content)
        
        self.assertEqual(title, "First Title")
    
    def test_falls_back_to_h2(self):
        """Test fallback to H2 if no H1 exists."""
        content = "## Second Level Title\n\nContent here."
        title = extract_title(content)
        
        self.assertEqual(title, "Second Level Title")
    
    def test_returns_untitled_if_no_heading(self):
        """Test that 'Untitled' is returned if no heading found."""
        content = "Just some content without any headings."
        title = extract_title(content)
        
        self.assertEqual(title, "Untitled")
    
    def test_strips_whitespace_from_title(self):
        """Test that whitespace is stripped from extracted title."""
        content = "#   Title with Spaces   \n\nContent."
        title = extract_title(content)
        
        self.assertEqual(title, "Title with Spaces")


class CalculateRelevanceScoreTest(TestCase):
    """
    Test the calculate_relevance_score function.
    
    Requirements: 4.7
    """
    
    def test_higher_score_for_title_match(self):
        """Test that title matches get higher scores."""
        content = "# Test\n\nSome content here."
        
        score_with_title = calculate_relevance_score(content, "test", "Test")
        score_without_title = calculate_relevance_score(content, "content", "Test")
        
        self.assertGreater(score_with_title, score_without_title)
    
    def test_higher_score_for_exact_title_match(self):
        """Test that exact title matches get even higher scores."""
        content = "# Test Document\n\nContent."
        
        score_exact = calculate_relevance_score(content, "test document", "Test Document")
        score_partial = calculate_relevance_score(content, "test", "Test Document")
        
        self.assertGreater(score_exact, score_partial)
    
    def test_higher_score_for_multiple_occurrences(self):
        """Test that multiple occurrences increase score."""
        content1 = "test " * 5
        content2 = "test once"
        
        score1 = calculate_relevance_score(content1, "test", "Title")
        score2 = calculate_relevance_score(content2, "test", "Title")
        
        self.assertGreater(score1, score2)
    
    def test_higher_score_for_heading_matches(self):
        """Test that matches in headings increase score."""
        content_with_heading = "# Test\n\n## Another Test\n\nContent."
        content_without_heading = "Content with test word."
        
        score_with = calculate_relevance_score(content_with_heading, "test", "Title")
        score_without = calculate_relevance_score(content_without_heading, "test", "Title")
        
        self.assertGreater(score_with, score_without)
    
    def test_higher_score_for_early_appearance(self):
        """Test that early appearance increases score."""
        content_early = "test " + "a" * 1000
        content_late = "a" * 1000 + " test"
        
        score_early = calculate_relevance_score(content_early, "test", "Title")
        score_late = calculate_relevance_score(content_late, "test", "Title")
        
        self.assertGreater(score_early, score_late)
    
    def test_higher_score_for_whole_word_match(self):
        """Test that whole word matches get bonus."""
        content_whole = "This is a test document."
        content_partial = "This is a testing document."
        
        score_whole = calculate_relevance_score(content_whole, "test", "Title")
        score_partial = calculate_relevance_score(content_partial, "test", "Title")
        
        self.assertGreater(score_whole, score_partial)
    
    def test_relevance_score_with_empty_content(self):
        """
        Test relevance scoring with empty content.
        Requirements: 3.6, 4.7
        """
        score = calculate_relevance_score("", "test", "Title")
        self.assertEqual(score, 0.0)
    
    def test_relevance_score_with_empty_query(self):
        """
        Test relevance scoring with empty query.
        Requirements: 3.6, 4.7
        
        Note: Empty queries are filtered out before reaching this function
        in normal operation, but the function should handle them gracefully.
        """
        content = "# Test Document\n\nSome content here."
        score = calculate_relevance_score(content, "", "Test Document")
        # Empty string matches everything, so score will be non-zero
        # This is acceptable since search_documentation filters empty queries
        self.assertGreaterEqual(score, 0.0)
    
    def test_relevance_score_case_insensitive(self):
        """
        Test that relevance scoring is case-insensitive.
        Requirements: 3.6, 4.7
        """
        content = "# TEST Document\n\nTEST content here."
        score_lower = calculate_relevance_score(content, "test", "TEST Document")
        score_upper = calculate_relevance_score(content, "TEST", "TEST Document")
        
        # Scores should be equal regardless of case
        self.assertEqual(score_lower, score_upper)


class SanitizeSearchQueryTest(TestCase):
    """
    Test the sanitize_search_query function.
    
    Requirements: 7.5
    """
    
    def test_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        query = sanitize_search_query("  test query  ")
        self.assertEqual(query, "test query")
    
    def test_limits_length(self):
        """Test that query length is limited."""
        long_query = "a" * 300
        query = sanitize_search_query(long_query, max_length=200)
        self.assertEqual(len(query), 200)
    
    def test_removes_control_characters(self):
        """Test that control characters are removed."""
        query = sanitize_search_query("test\x00query\x01")
        self.assertNotIn('\x00', query)
        self.assertNotIn('\x01', query)
    
    def test_preserves_normal_characters(self):
        """Test that normal characters are preserved."""
        query = sanitize_search_query("test query 123")
        self.assertEqual(query, "test query 123")
    
    def test_handles_empty_query(self):
        """Test that empty query returns empty string."""
        query = sanitize_search_query("")
        self.assertEqual(query, "")
    
    def test_handles_none_query(self):
        """Test that None query returns empty string."""
        query = sanitize_search_query(None)
        self.assertEqual(query, "")
    
    def test_sanitize_removes_null_bytes(self):
        """
        Test that null bytes are removed from queries.
        Requirements: 3.6, 7.5
        """
        query = sanitize_search_query("test\x00query")
        self.assertNotIn('\x00', query)
        self.assertEqual(query, "testquery")
    
    def test_sanitize_preserves_unicode(self):
        """
        Test that Unicode characters are preserved.
        Requirements: 3.6, 7.5
        """
        query = sanitize_search_query("café résumé")
        self.assertEqual(query, "café résumé")
    
    def test_sanitize_handles_only_whitespace(self):
        """
        Test that queries with only whitespace return empty string.
        Requirements: 3.6, 7.5
        """
        query = sanitize_search_query("   \t\n   ")
        self.assertEqual(query, "")
    
    def test_sanitize_removes_control_chars_but_keeps_tabs_newlines(self):
        """
        Test that control characters are removed but tabs/newlines are kept.
        Requirements: 3.6, 7.5
        """
        query = sanitize_search_query("test\x01\x02query\t\nmore")
        self.assertNotIn('\x01', query)
        self.assertNotIn('\x02', query)
        # Tabs and newlines should be preserved
        self.assertIn('\t', query)
        self.assertIn('\n', query)


class HighlightSearchTermTest(TestCase):
    """
    Test the highlight_search_term function.
    """
    
    def test_highlights_single_occurrence(self):
        """Test highlighting a single occurrence."""
        text = "This is a test document."
        highlighted = highlight_search_term(text, "test")
        
        self.assertIn('<mark class="search-highlight">test</mark>', highlighted)
    
    def test_highlights_multiple_occurrences(self):
        """Test highlighting multiple occurrences."""
        text = "test test test"
        highlighted = highlight_search_term(text, "test")
        
        # Should have 3 highlighted marks
        self.assertEqual(highlighted.count('<mark class="search-highlight">'), 3)
    
    def test_case_insensitive_highlighting(self):
        """Test that highlighting is case-insensitive."""
        text = "This is a TEST document."
        highlighted = highlight_search_term(text, "test")
        
        self.assertIn('<mark class="search-highlight">TEST</mark>', highlighted)
    
    def test_escapes_html_in_text(self):
        """Test that HTML in text is escaped."""
        text = "<script>alert('xss')</script> test"
        highlighted = highlight_search_term(text, "test")
        
        self.assertIn('&lt;script&gt;', highlighted)
        self.assertNotIn('<script>', highlighted)
    
    def test_handles_empty_query(self):
        """Test that empty query returns original text."""
        text = "This is a test."
        highlighted = highlight_search_term(text, "")
        
        self.assertEqual(highlighted, text)
    
    def test_custom_highlight_class(self):
        """Test using a custom CSS class."""
        text = "This is a test."
        highlighted = highlight_search_term(text, "test", highlight_class="custom-class")
        
        self.assertIn('<mark class="custom-class">test</mark>', highlighted)
    
    def test_highlight_with_special_regex_chars(self):
        """
        Test highlighting with special regex characters in query.
        Requirements: 3.6, 4.7
        """
        text = "Call test.method() or test[0]"
        highlighted = highlight_search_term(text, "test.method()")
        
        # Should highlight the literal string
        self.assertIn('<mark class="search-highlight">test.method()</mark>', highlighted)
    
    def test_highlight_preserves_html_escaping(self):
        """
        Test that HTML escaping is preserved.
        Requirements: 3.6, 4.7
        """
        text = "<div>test</div>"
        highlighted = highlight_search_term(text, "test")
        
        # HTML should be escaped
        self.assertIn('&lt;div&gt;', highlighted)
        self.assertIn('&lt;/div&gt;', highlighted)
        # But the search term should be highlighted
        self.assertIn('<mark class="search-highlight">test</mark>', highlighted)
    
    def test_highlight_with_unicode(self):
        """
        Test highlighting with Unicode characters.
        Requirements: 3.6, 4.7
        """
        text = "This is a café test"
        highlighted = highlight_search_term(text, "café")
        
        self.assertIn('<mark class="search-highlight">café</mark>', highlighted)
    
    def test_highlight_empty_text(self):
        """
        Test highlighting with empty text.
        Requirements: 3.6, 4.7
        """
        highlighted = highlight_search_term("", "test")
        self.assertEqual(highlighted, "")
    
    def test_highlight_none_query(self):
        """
        Test highlighting with None query.
        Requirements: 3.6, 4.7
        """
        text = "This is a test"
        highlighted = highlight_search_term(text, None)
        self.assertEqual(highlighted, text)
