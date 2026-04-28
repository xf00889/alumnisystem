import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from core.models.ai_config import AIConfig


class AIConfigGeminiTestCase(TestCase):
    def test_gemini_test_configuration_uses_the_config_rows_own_api_key(self):
        active_config = AIConfig.objects.create(
            name="Active Gemini",
            provider="gemini",
            api_key="invalid-active-key",
            model_name="gemini-2.5-flash",
            is_active=True,
            enabled=True,
        )
        config_under_test = AIConfig.objects.create(
            name="Candidate Gemini",
            provider="gemini",
            api_key="valid-candidate-key",
            model_name="gemini-2.5-flash",
            is_active=False,
            enabled=True,
        )

        class FakeClient:
            def __init__(self, api_key):
                self.api_key = api_key
                self.models = self

            def generate_content(self, model, contents, config=None):
                if self.api_key != config_under_test.api_key:
                    raise Exception("API key not valid. Please pass a valid API key.")
                return SimpleNamespace(text="OK", candidates=[])

        fake_google = ModuleType("google")
        fake_genai = ModuleType("google.genai")
        fake_genai.Client = FakeClient
        fake_google.genai = fake_genai

        with patch.dict(sys.modules, {"google": fake_google, "google.genai": fake_genai}):
            success, message = config_under_test.test_configuration()

        self.assertTrue(success, message)
        config_under_test.refresh_from_db()
        active_config.refresh_from_db()
        self.assertTrue(config_under_test.is_verified)
        self.assertFalse(active_config.is_verified)
