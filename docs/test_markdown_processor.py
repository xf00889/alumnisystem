"""
Tests for the markdown processor module.
"""

from django.test import TestCase
from django.core.cache import cache
from pathlib import Path
from docs.markdown_processor import MarkdownProcessor
import tempfile
import os


class MarkdownProcessorTestCase(TestCase):
    """Test cases for MarkdownProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear cache before each test
        cache.clear()
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.processor = MarkdownProcessor(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_file(self, filename, content):
        """Helper to create a test markdown file."""
        file_path = Path(self.test_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return filename
    
    def test_render_simple_markdown(self):
        """Test rendering simple markdown content."""
        content = "# Test Title\n\nThis is a paragraph."
        filename = self._create_test_file('test.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('<h1', result['html'])
        self.assertIn('Test Title', result['html'])
        self.assertIn('<p>This is a paragraph.</p>', result['html'])
        self.assertEqual(result['title'], 'Test Title')
    
    def test_render_with_code_blocks(self):
        """Test rendering markdown with code blocks."""
        content = """# Code Example

```python
def hello():
    print("Hello, World!")
```
"""
        filename = self._create_test_file('code.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('highlight', result['html'])
        # Check for syntax-highlighted code (may be wrapped in spans)
        self.assertIn('hello', result['html'])
    
    def test_render_with_tables(self):
        """Test rendering markdown with tables."""
        content = """# Table Example

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
        filename = self._create_test_file('table.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('<table>', result['html'])
        self.assertIn('<th>Header 1</th>', result['html'])
        self.assertIn('<td>Cell 1</td>', result['html'])
    
    def test_caching_behavior(self):
        """Test that rendered content is cached."""
        content = "# Cached Content\n\nThis should be cached."
        filename = self._create_test_file('cached.md', content)
        
        # First render
        result1 = self.processor.render(filename)
        self.assertFalse(result1.get('error', False))
        
        # Second render should come from cache
        result2 = self.processor.render(filename)
        self.assertFalse(result2.get('error', False))
        
        # Results should be identical
        self.assertEqual(result1['html'], result2['html'])
        self.assertEqual(result1['title'], result2['title'])
    
    def test_cache_invalidation_on_file_change(self):
        """Test that cache is invalidated when file is modified."""
        content1 = "# Version 1"
        filename = self._create_test_file('versioned.md', content1)
        
        # First render
        result1 = self.processor.render(filename)
        self.assertIn('Version 1', result1['html'])
        
        # Modify file
        import time
        time.sleep(0.1)  # Ensure different mtime
        content2 = "# Version 2"
        self._create_test_file(filename, content2)
        
        # Second render should reflect changes
        result2 = self.processor.render(filename)
        self.assertIn('Version 2', result2['html'])
        self.assertNotIn('Version 1', result2['html'])
    
    def test_relative_link_processing(self):
        """Test conversion of relative .md links to URLs."""
        content = """# Links

[Link to other doc](other-doc.md)
[External link](https://example.com)
[Anchor link](#section)
"""
        filename = self._create_test_file('links.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        # .md link should be converted
        self.assertIn('/docs/other-doc/', result['html'])
        # External link should remain unchanged
        self.assertIn('https://example.com', result['html'])
        # Anchor link should remain unchanged
        self.assertIn('#section', result['html'])
    
    def test_file_not_found(self):
        """Test handling of non-existent files."""
        result = self.processor.render('nonexistent.md')
        
        self.assertTrue(result.get('error', False))
        self.assertEqual(result.get('message'), 'Document not found')
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        # Try to access file outside base path
        result = self.processor.render('../../../etc/passwd')
        
        self.assertTrue(result.get('error', False))
    
    def test_title_extraction(self):
        """Test extraction of document title from H1."""
        content = """# My Document Title

Some content here.

## Subsection
"""
        filename = self._create_test_file('titled.md', content)
        
        result = self.processor.render(filename)
        
        self.assertEqual(result['title'], 'My Document Title')
    
    def test_title_extraction_no_h1(self):
        """Test title extraction when no H1 exists."""
        content = "Just some content without a title."
        filename = self._create_test_file('notitle.md', content)
        
        result = self.processor.render(filename)
        
        self.assertEqual(result['title'], 'Untitled')
    
    def test_toc_extraction_all_heading_levels(self):
        """
        Test that TOC extracts all heading levels correctly.
        Requirements: 3.7
        """
        content = """# Level 1 Heading

## Level 2 Heading

### Level 3 Heading

#### Level 4 Heading

##### Level 5 Heading

###### Level 6 Heading

Some content here.
"""
        filename = self._create_test_file('headings.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        
        # Check that TOC is generated
        self.assertIn('toc', result)
        toc_html = result['toc']
        
        # TOC should contain all heading levels
        self.assertIn('Level 1 Heading', toc_html)
        self.assertIn('Level 2 Heading', toc_html)
        self.assertIn('Level 3 Heading', toc_html)
        self.assertIn('Level 4 Heading', toc_html)
        self.assertIn('Level 5 Heading', toc_html)
        self.assertIn('Level 6 Heading', toc_html)
    
    def test_toc_extraction_with_special_characters(self):
        """
        Test that TOC handles headings with special characters.
        Requirements: 3.7
        """
        content = """# Heading with `code`

## Heading with **bold** text

### Heading with [link](url)

#### Heading with <em>HTML</em>
"""
        filename = self._create_test_file('special_headings.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('toc', result)
        
        # TOC should handle special characters
        toc_html = result['toc']
        self.assertIn('code', toc_html)
        self.assertIn('bold', toc_html)
        self.assertIn('link', toc_html)
    
    def test_toc_extraction_with_duplicate_headings(self):
        """
        Test that TOC handles duplicate heading text.
        Requirements: 3.7
        """
        content = """# Introduction

## Introduction

### Introduction
"""
        filename = self._create_test_file('duplicate_headings.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('toc', result)
        
        # TOC should include all headings even if text is duplicate
        toc_html = result['toc']
        # Should have multiple entries for "Introduction"
        self.assertGreater(toc_html.count('Introduction'), 1)
    
    def test_toc_extraction_empty_document(self):
        """
        Test that TOC handles documents with no headings.
        Requirements: 3.7
        """
        content = "Just some content without any headings."
        filename = self._create_test_file('no_headings.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('toc', result)
        
        # TOC should be empty or minimal
        toc_html = result['toc']
        # Should not crash, may be empty string or empty list
        self.assertIsNotNone(toc_html)
    
    def test_toc_extraction_nested_structure(self):
        """
        Test that TOC maintains proper nesting of headings.
        Requirements: 3.7
        """
        content = """# Main Section

## Subsection 1

### Sub-subsection 1.1

### Sub-subsection 1.2

## Subsection 2

### Sub-subsection 2.1
"""
        filename = self._create_test_file('nested_headings.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('toc', result)
        
        # TOC should maintain hierarchical structure
        toc_html = result['toc']
        self.assertIn('Main Section', toc_html)
        self.assertIn('Subsection 1', toc_html)
        self.assertIn('Sub-subsection 1.1', toc_html)
        self.assertIn('Sub-subsection 2.1', toc_html)
    
    def test_toc_extraction_with_unicode(self):
        """
        Test that TOC handles Unicode characters in headings.
        Requirements: 3.7
        """
        content = """# Café Documentation

## Résumé Section

### 日本語 Section
"""
        filename = self._create_test_file('unicode_headings.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('toc', result)
        
        # TOC should handle Unicode
        toc_html = result['toc']
        self.assertIn('Café', toc_html)
        self.assertIn('Résumé', toc_html)
        self.assertIn('日本語', toc_html)
    
    def test_toc_generates_anchor_links(self):
        """
        Test that TOC generates proper anchor links for navigation.
        Requirements: 3.7
        """
        content = """# First Heading

## Second Heading

### Third Heading
"""
        filename = self._create_test_file('anchors.md', content)
        
        result = self.processor.render(filename)
        
        self.assertFalse(result.get('error', False))
        self.assertIn('toc', result)
        
        # TOC should contain anchor links
        toc_html = result['toc']
        # Should have href attributes for navigation
        self.assertIn('href=', toc_html)
        # Should have anchor IDs (typically slugified heading text)
        self.assertTrue('#' in toc_html or 'id=' in toc_html)
