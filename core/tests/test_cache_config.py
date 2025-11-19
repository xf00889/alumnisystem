"""
Tests for cache configuration.

This module tests that the cache backend is correctly configured based on
environment variables, ensuring Redis is used in production and locmem in development.
"""

import os
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.conf import settings


class CacheConfigurationTestCase(TestCase):
    """Test cache backend configuration based on environment variables."""

    def tearDown(self):
        """Clear cache after each test."""
        cache.clear()

    def test_redis_backend_when_redis_url_set(self):
        """
        Test that Redis backend is selected when REDIS_URL is set.
        
        Validates: Requirements 4.1
        """
        # Check if REDIS_URL is set in current environment
        redis_url = os.environ.get('REDIS_URL')
        
        if redis_url:
            # If REDIS_URL is set, verify Redis backend is configured
            cache_backend = settings.CACHES['default']['BACKEND']
            self.assertEqual(
                cache_backend,
                'django.core.cache.backends.redis.RedisCache',
                "Redis backend should be used when REDIS_URL is set"
            )
            
            # Verify Redis location is set correctly
            self.assertEqual(
                settings.CACHES['default']['LOCATION'],
                redis_url,
                "Redis location should match REDIS_URL"
            )
            
            # Verify Redis-specific options are present
            self.assertIn('OPTIONS', settings.CACHES['default'])
            options = settings.CACHES['default']['OPTIONS']
            self.assertIn('CLIENT_CLASS', options)
            self.assertIn('CONNECTION_POOL_KWARGS', options)
            
            # Verify key prefix is set
            self.assertEqual(
                settings.CACHES['default'].get('KEY_PREFIX'),
                'norsu_alumni',
                "Key prefix should be set for Redis"
            )
        else:
            # If REDIS_URL is not set, this test is skipped
            self.skipTest("REDIS_URL not set in environment")

    def test_locmem_backend_when_redis_url_not_set(self):
        """
        Test that locmem backend is selected when REDIS_URL is not set.
        
        Validates: Requirements 4.2
        """
        # Check if REDIS_URL is not set in current environment
        redis_url = os.environ.get('REDIS_URL')
        
        if not redis_url:
            # If REDIS_URL is not set, verify locmem backend is configured
            cache_backend = settings.CACHES['default']['BACKEND']
            self.assertEqual(
                cache_backend,
                'django.core.cache.backends.locmem.LocMemCache',
                "Local memory backend should be used when REDIS_URL is not set"
            )
            
            # Verify locmem location is set
            self.assertEqual(
                settings.CACHES['default']['LOCATION'],
                'unique-snowflake',
                "Locmem location should be set"
            )
            
            # Verify timeout is configured
            self.assertIn('TIMEOUT', settings.CACHES['default'])
            self.assertEqual(
                settings.CACHES['default']['TIMEOUT'],
                300,
                "Cache timeout should be 5 minutes"
            )
        else:
            # If REDIS_URL is set, this test is skipped
            self.skipTest("REDIS_URL is set in environment")

    def test_cache_operations_work(self):
        """
        Test that basic cache operations work regardless of backend.
        
        This ensures the cache is functional in both development and production.
        Validates: Requirements 4.1, 4.2
        """
        # Test cache set
        cache.set('test_key', 'test_value', timeout=60)
        
        # Test cache get
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value', "Cache should store and retrieve values")
        
        # Test cache delete
        cache.delete('test_key')
        value = cache.get('test_key')
        self.assertIsNone(value, "Cache should delete values")
        
        # Test cache set with default
        value = cache.get('nonexistent_key', default='default_value')
        self.assertEqual(value, 'default_value', "Cache should return default for missing keys")

    def test_cache_timeout_configuration(self):
        """
        Test that cache timeout is properly configured.
        
        Validates: Requirements 4.1, 4.2
        """
        # Verify default timeout is set
        self.assertIn('TIMEOUT', settings.CACHES['default'])
        timeout = settings.CACHES['default']['TIMEOUT']
        self.assertEqual(timeout, 300, "Default cache timeout should be 5 minutes (300 seconds)")

    def test_documentation_cache_settings(self):
        """
        Test that documentation-specific cache settings are configured.
        
        Validates: Requirements 4.1, 4.2
        """
        # Verify documentation cache timeouts are set
        self.assertTrue(
            hasattr(settings, 'DOCS_CACHE_TIMEOUT'),
            "DOCS_CACHE_TIMEOUT should be configured"
        )
        self.assertEqual(
            settings.DOCS_CACHE_TIMEOUT,
            3600,
            "Documentation cache timeout should be 1 hour"
        )
        
        self.assertTrue(
            hasattr(settings, 'DOCS_TOC_CACHE_TIMEOUT'),
            "DOCS_TOC_CACHE_TIMEOUT should be configured"
        )
        self.assertEqual(
            settings.DOCS_TOC_CACHE_TIMEOUT,
            3600,
            "Documentation TOC cache timeout should be 1 hour"
        )

    def test_cache_key_prefix_for_redis(self):
        """
        Test that Redis cache uses a key prefix to avoid collisions.
        
        Validates: Requirements 4.1
        """
        redis_url = os.environ.get('REDIS_URL')
        
        if redis_url:
            # Verify key prefix is set for Redis
            self.assertIn('KEY_PREFIX', settings.CACHES['default'])
            self.assertEqual(
                settings.CACHES['default']['KEY_PREFIX'],
                'norsu_alumni',
                "Redis should use 'norsu_alumni' key prefix"
            )
        else:
            self.skipTest("REDIS_URL not set in environment")

    def test_cache_middleware_configuration(self):
        """
        Test that cache middleware settings are properly configured.
        
        Validates: Requirements 4.1, 4.2
        """
        # Verify cache middleware settings exist
        self.assertTrue(
            hasattr(settings, 'CACHE_MIDDLEWARE_ALIAS'),
            "CACHE_MIDDLEWARE_ALIAS should be configured"
        )
        self.assertEqual(
            settings.CACHE_MIDDLEWARE_ALIAS,
            'default',
            "Cache middleware should use default cache"
        )
        
        self.assertTrue(
            hasattr(settings, 'CACHE_MIDDLEWARE_SECONDS'),
            "CACHE_MIDDLEWARE_SECONDS should be configured"
        )
        self.assertEqual(
            settings.CACHE_MIDDLEWARE_SECONDS,
            300,
            "Cache middleware timeout should be 5 minutes"
        )
