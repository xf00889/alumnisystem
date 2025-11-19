"""
Tests for the navigation builder module.

Tests TOC generation, breadcrumb building, prev/next calculation,
and caching functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
from django.test import TestCase
from django.core.cache import cache
from docs.navigation import NavigationBuilder


class NavigationBuilderTestCase(TestCase):
    """Test cases for NavigationBuilder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test documentation
        self.test_dir = tempfile.mkdtemp()
        self.builder = NavigationBuilder(base_path=self.test_dir)
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
        cache.clear()
    
    def _create_test_structure(self):
        """Create a test documentation structure."""
        # Create directories
        Path(self.test_dir, 'getting-started').mkdir()
        Path(self.test_dir, 'user-guide').mkdir()
        Path(self.test_dir, 'user-guide', 'features').mkdir()
        
        # Create markdown files
        Path(self.test_dir, 'README.md').write_text('# Root README')
        Path(self.test_dir, 'introduction.md').write_text('# Introduction')
        Path(self.test_dir, 'getting-started', 'README.md').write_text('# Getting Started')
        Path(self.test_dir, 'getting-started', 'installation.md').write_text('# Installation')
        Path(self.test_dir, 'user-guide', 'README.md').write_text('# User Guide')
        Path(self.test_dir, 'user-guide', 'basics.md').write_text('# Basics')
        Path(self.test_dir, 'user-guide', 'features', 'feature-one.md').write_text('# Feature One')
        Path(self.test_dir, 'user-guide', 'features', 'feature-two.md').write_text('# Feature Two')
        
        # Create a hidden file (should be ignored)
        Path(self.test_dir, '.hidden.md').write_text('# Hidden')
        
        # Create a private directory (should be ignored)
        Path(self.test_dir, '_private').mkdir()
        Path(self.test_dir, '_private', 'secret.md').write_text('# Secret')
    
    def test_build_toc_structure(self):
        """Test that TOC is built correctly from directory structure."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        
        # Should have 3 top-level items (2 folders + 2 files, excluding hidden)
        self.assertEqual(len(toc), 4)
        
        # Check folder structure
        folders = [item for item in toc if item['type'] == 'folder']
        self.assertEqual(len(folders), 2)
        
        # Check files
        files = [item for item in toc if item['type'] == 'file']
        self.assertEqual(len(files), 2)
    
    def test_toc_hierarchical_structure(self):
        """Test that TOC maintains hierarchical structure."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        
        # Find user-guide folder
        user_guide = next(item for item in toc if item['name'] == 'User Guide')
        
        # Should have children
        self.assertIn('children', user_guide)
        self.assertGreater(len(user_guide['children']), 0)
        
        # Check nested folder
        features_folder = next(
            item for item in user_guide['children'] 
            if item['type'] == 'folder' and item['name'] == 'Features'
        )
        self.assertEqual(len(features_folder['children']), 2)
    
    def test_toc_ignores_hidden_files(self):
        """Test that hidden files and directories are ignored."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        flat = self.builder._flatten_toc(toc)
        
        # Check that hidden file is not in TOC
        hidden_files = [item for item in flat if '.hidden' in item['path']]
        self.assertEqual(len(hidden_files), 0)
        
        # Check that private directory is not in TOC
        private_files = [item for item in flat if '_private' in item['path']]
        self.assertEqual(len(private_files), 0)
    
    def test_format_name_readme(self):
        """Test that README is formatted as 'Overview'."""
        result = self.builder._format_name('README')
        self.assertEqual(result, 'Overview')
        
        result = self.builder._format_name('readme')
        self.assertEqual(result, 'Overview')
    
    def test_format_name_kebab_case(self):
        """Test that kebab-case is converted to Title Case."""
        result = self.builder._format_name('getting-started')
        self.assertEqual(result, 'Getting Started')
        
        result = self.builder._format_name('user-guide')
        self.assertEqual(result, 'User Guide')
    
    def test_format_name_snake_case(self):
        """Test that snake_case is converted to Title Case."""
        result = self.builder._format_name('user_guide')
        self.assertEqual(result, 'User Guide')
        
        result = self.builder._format_name('feature_one')
        self.assertEqual(result, 'Feature One')
    
    def test_build_breadcrumbs_root(self):
        """Test breadcrumb generation for root level."""
        breadcrumbs = self.builder.build_breadcrumbs('')
        
        # Should only have Documentation root
        self.assertEqual(len(breadcrumbs), 1)
        self.assertEqual(breadcrumbs[0]['name'], 'Documentation')
        self.assertEqual(breadcrumbs[0]['url'], '/docs/')
    
    def test_build_breadcrumbs_nested_path(self):
        """Test breadcrumb generation for nested paths."""
        breadcrumbs = self.builder.build_breadcrumbs('user-guide/features/feature-one.md')
        
        # Should have: Documentation > User Guide > Features > Feature One
        self.assertEqual(len(breadcrumbs), 4)
        
        # Check root
        self.assertEqual(breadcrumbs[0]['name'], 'Documentation')
        self.assertEqual(breadcrumbs[0]['url'], '/docs/')
        
        # Check intermediate directories
        self.assertEqual(breadcrumbs[1]['name'], 'User Guide')
        self.assertEqual(breadcrumbs[1]['url'], '/docs/user-guide/')
        
        self.assertEqual(breadcrumbs[2]['name'], 'Features')
        self.assertEqual(breadcrumbs[2]['url'], '/docs/user-guide/features/')
        
        # Check current file (no URL)
        self.assertEqual(breadcrumbs[3]['name'], 'Feature One')
        self.assertIsNone(breadcrumbs[3]['url'])
    
    def test_flatten_toc(self):
        """Test that TOC is correctly flattened to sequential list."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        flat = self.builder._flatten_toc(toc)
        
        # Should only contain files, not folders
        for item in flat:
            self.assertEqual(item['type'], 'file')
        
        # Should have all markdown files (excluding hidden)
        self.assertEqual(len(flat), 8)
    
    def test_get_prev_next_first_document(self):
        """Test prev/next for first document (no previous)."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        flat = self.builder._flatten_toc(toc)
        first_path = flat[0]['path']
        
        result = self.builder.get_prev_next(first_path, toc)
        
        # First document should have no previous
        self.assertIsNone(result['prev'])
        # Should have next
        self.assertIsNotNone(result['next'])
    
    def test_get_prev_next_last_document(self):
        """Test prev/next for last document (no next)."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        flat = self.builder._flatten_toc(toc)
        last_path = flat[-1]['path']
        
        result = self.builder.get_prev_next(last_path, toc)
        
        # Last document should have no next
        self.assertIsNone(result['next'])
        # Should have previous
        self.assertIsNotNone(result['prev'])
    
    def test_get_prev_next_middle_document(self):
        """Test prev/next for middle document (has both)."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        flat = self.builder._flatten_toc(toc)
        
        # Get a middle document
        if len(flat) > 2:
            middle_path = flat[len(flat) // 2]['path']
            
            result = self.builder.get_prev_next(middle_path, toc)
            
            # Should have both prev and next
            self.assertIsNotNone(result['prev'])
            self.assertIsNotNone(result['next'])
    
    def test_get_prev_next_invalid_path(self):
        """Test prev/next with invalid path."""
        self._create_test_structure()
        
        result = self.builder.get_prev_next('nonexistent/path.md')
        
        # Should return None for both
        self.assertIsNone(result['prev'])
        self.assertIsNone(result['next'])
    
    def test_toc_caching(self):
        """Test that TOC is cached properly."""
        self._create_test_structure()
        
        # First call should build and cache
        toc1 = self.builder.build_toc()
        
        # Second call should return cached version
        toc2 = self.builder.build_toc()
        
        # Should be the same object (from cache)
        self.assertEqual(toc1, toc2)
        
        # Verify cache was used
        cache_key = 'docs_toc_structure'
        cached = cache.get(cache_key)
        self.assertIsNotNone(cached)
    
    def test_invalidate_cache(self):
        """Test cache invalidation."""
        self._create_test_structure()
        
        # Build and cache TOC
        self.builder.build_toc()
        
        # Verify it's cached
        cache_key = 'docs_toc_structure'
        self.assertIsNotNone(cache.get(cache_key))
        
        # Invalidate cache
        self.builder.invalidate_cache()
        
        # Verify cache is cleared
        self.assertIsNone(cache.get(cache_key))
    
    def test_get_document_count(self):
        """Test document count calculation."""
        self._create_test_structure()
        
        count = self.builder.get_document_count()
        
        # Should count all markdown files (excluding hidden)
        self.assertEqual(count, 8)
    
    def test_folder_has_readme_flag(self):
        """Test that folders correctly indicate if they have README."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        
        # Find getting-started folder (has README)
        getting_started = next(
            item for item in toc 
            if item['type'] == 'folder' and item['name'] == 'Getting Started'
        )
        self.assertTrue(getting_started['has_readme'])
        
        # Find features folder (no README)
        user_guide = next(item for item in toc if item['name'] == 'User Guide')
        features = next(
            item for item in user_guide['children']
            if item['type'] == 'folder' and item['name'] == 'Features'
        )
        self.assertFalse(features['has_readme'])
    
    def test_sorting_folders_before_files(self):
        """Test that folders are sorted before files."""
        self._create_test_structure()
        
        toc = self.builder.build_toc()
        
        # Check that folders come before files at the same level
        types = [item['type'] for item in toc]
        
        # Find first file index
        first_file_idx = types.index('file') if 'file' in types else len(types)
        
        # All folders should come before first file
        for i in range(first_file_idx):
            if i < len(types):
                self.assertEqual(types[i], 'folder')
    
    def test_empty_directory(self):
        """Test handling of empty documentation directory."""
        # Use empty temp directory
        toc = self.builder.build_toc()
        
        # Should return empty list
        self.assertEqual(toc, [])
    
    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        builder = NavigationBuilder(base_path='/nonexistent/path')
        
        toc = builder.build_toc()
        
        # Should return empty list without crashing
        self.assertEqual(toc, [])
