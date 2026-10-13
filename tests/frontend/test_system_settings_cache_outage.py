"""Offline regression checks for per-request middleware's cache failure recovery."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


BASE_DIR = Path(__file__).resolve().parents[2]
SOURCE = BASE_DIR / 'core' / 'system_settings_utils.py'


class FakeCache:
    def __init__(self, fail_get=False, fail_set=False, fail_delete=False):
        self.fail_get = fail_get
        self.fail_set = fail_set
        self.fail_delete = fail_delete
        self.data = {}

    def get(self, key):
        if self.fail_get:
            raise ConnectionError('simulated Redis outage')
        return self.data.get(key)

    def set(self, key, value, ttl):
        if self.fail_set:
            raise ConnectionError('simulated Redis outage')
        self.data[key] = value

    def delete(self, key):
        if self.fail_delete:
            raise ConnectionError('simulated Redis outage')
        self.data.pop(key, None)


def load_settings_module(fake_cache, db_record=None):
    django = types.ModuleType('django')
    conf = types.ModuleType('django.conf')
    conf.settings = types.SimpleNamespace(DEBUG=False)
    django_core = types.ModuleType('django.core')
    cache_mod = types.ModuleType('django.core.cache')
    cache_mod.cache = fake_cache
    models = types.ModuleType('core.models')
    manager = types.SimpleNamespace(order_by=lambda *args: types.SimpleNamespace(first=lambda: db_record))
    models.SystemSettings = types.SimpleNamespace(objects=manager)
    stubs = {
        'django': django, 'django.conf': conf, 'django.core': django_core,
        'django.core.cache': cache_mod, 'core.models': models,
    }
    with patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location('_cache_safe_system_settings', SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module, stubs


class CacheOutageTests(unittest.TestCase):
    def test_redis_get_failure_keeps_database_maintenance_mode(self):
        db = types.SimpleNamespace(maintenance_mode=True, maintenance_message='Maintenance window', runtime_debug=False)
        for module, stubs in load_settings_module(FakeCache(fail_get=True), db):
            with patch.dict(sys.modules, stubs):
                self.assertTrue(module.is_maintenance_mode_enabled())
                self.assertEqual(module.get_maintenance_message(), 'Maintenance window')

    def test_redis_set_failure_does_not_break_request(self):
        for module, stubs in load_settings_module(FakeCache(fail_set=True)):
            with patch.dict(sys.modules, stubs):
                self.assertFalse(module.is_maintenance_mode_enabled())

    def test_redis_delete_failure_does_not_break_admin(self):
        for module, stubs in load_settings_module(FakeCache(fail_delete=True)):
            with patch.dict(sys.modules, stubs):
                self.assertIsNone(module.clear_system_settings_cache())

    def test_cache_success_retains_expected_ttl(self):
        cache = FakeCache()
        for module, stubs in load_settings_module(cache):
            with patch.dict(sys.modules, stubs):
                self.assertFalse(module.is_maintenance_mode_enabled())
                self.assertIn(module.CACHE_KEY, cache.data)


if __name__ == '__main__':
    unittest.main()
