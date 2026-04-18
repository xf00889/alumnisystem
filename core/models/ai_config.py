"""
AI API Configuration Model
Stores API keys for AI services (e.g., Google Gemini) in the database
instead of environment variables, managed via the custom admin dashboard.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class AIConfig(models.Model):
    """
    Model to store AI API configuration settings.
    Supports multiple providers; only one can be active at a time.
    """

    PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI'),
    ]

    name = models.CharField(
        max_length=100,
        help_text="A descriptive name for this configuration (e.g., 'Gemini Production')"
    )

    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='gemini',
        help_text="AI provider"
    )

    api_key = models.CharField(
        max_length=500,
        help_text="API key from the provider console"
    )

    model_name = models.CharField(
        max_length=100,
        default='gemini-2.5-flash',
        help_text="Model to use (e.g., gemini-2.5-flash, gpt-4o-mini)"
    )

    is_active = models.BooleanField(
        default=False,
        help_text="Use this configuration for AI features"
    )

    enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable AI features globally"
    )

    is_verified = models.BooleanField(
        default=False,
        help_text="Configuration has been tested and verified"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_tested = models.DateTimeField(null=True, blank=True)

    # Test result
    test_result = models.TextField(
        blank=True,
        help_text="Result of the last test"
    )

    class Meta:
        verbose_name = "AI Configuration"
        verbose_name_plural = "AI Configurations"
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        status = "✓" if self.is_verified else "✗"
        active = " [ACTIVE]" if self.is_active else ""
        return f"{status} {self.name} ({self.get_provider_display()}){active}"

    def clean(self):
        """Validate AI configuration."""
        super().clean()
        if not self.api_key or len(self.api_key) < 10:
            raise ValidationError({'api_key': 'API key appears to be invalid or too short.'})
        if not self.model_name:
            raise ValidationError({'model_name': 'Model name is required.'})

    def test_configuration(self):
        """
        Test the API key by making a minimal request to the provider.
        Returns (success: bool, message: str).
        """
        try:
            if self.provider == 'gemini':
                return self._test_gemini()
            elif self.provider == 'openai':
                return self._test_openai()
            else:
                return False, f"Unknown provider: {self.provider}"
        except Exception as e:
            msg = f"Test failed: {str(e)}"
            AIConfig.objects.filter(pk=self.pk).update(
                is_verified=False,
                test_result=msg,
                last_tested=timezone.now()
            )
            return False, msg

    def _test_gemini(self):
        """Test Google Gemini API key using the new google-genai SDK."""
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)

            # Build config — disable thinking for 2.5 models so we get plain text
            config_kwargs = {
                "max_output_tokens": 10,
                "temperature": 0,
            }
            if '2.5' in self.model_name:
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)

            response = client.models.generate_content(
                model=self.model_name,
                contents="Reply with the word OK only.",
                config=types.GenerateContentConfig(**config_kwargs)
            )

            # Safely extract text
            text = ""
            try:
                text = response.text or ""
            except Exception:
                pass
            if not text:
                for candidate in (response.candidates or []):
                    content = getattr(candidate, 'content', None)
                    if content:
                        for part in getattr(content, 'parts', []) or []:
                            # Skip thought parts
                            if getattr(part, 'thought', False):
                                continue
                            t = getattr(part, 'text', None)
                            if t:
                                text += t

            if not text:
                raise ValueError("Model returned an empty response. Check your API key and model name.")

            msg = f"Gemini API key is valid. Model '{self.model_name}' responded successfully."
            AIConfig.objects.filter(pk=self.pk).update(
                is_verified=True,
                test_result=msg,
                last_tested=timezone.now()
            )
            return True, msg
        except ImportError:
            msg = "google-genai package is not installed. Run: pip install google-genai"
            AIConfig.objects.filter(pk=self.pk).update(
                is_verified=False, test_result=msg, last_tested=timezone.now()
            )
            return False, msg
        except Exception as e:
            msg = f"Gemini test failed: {str(e)}"
            AIConfig.objects.filter(pk=self.pk).update(
                is_verified=False, test_result=msg, last_tested=timezone.now()
            )
            return False, msg

    def _test_openai(self):
        """Test OpenAI API key."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            client.models.list()
            msg = "OpenAI API key is valid."
            AIConfig.objects.filter(pk=self.pk).update(
                is_verified=True, test_result=msg, last_tested=timezone.now()
            )
            return True, msg
        except ImportError:
            msg = "openai package is not installed. Run: pip install openai"
            AIConfig.objects.filter(pk=self.pk).update(
                is_verified=False, test_result=msg, last_tested=timezone.now()
            )
            return False, msg
        except Exception as e:
            msg = f"OpenAI test failed: {str(e)}"
            AIConfig.objects.filter(pk=self.pk).update(
                is_verified=False, test_result=msg, last_tested=timezone.now()
            )
            return False, msg

    def save(self, *args, **kwargs):
        """Ensure only one active configuration at a time."""
        if self.is_active:
            AIConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
        # Clear cache on save
        from django.core.cache import cache
        cache.delete('ai_active_config')

    @classmethod
    def get_active_config(cls):
        """Return the currently active and enabled AI configuration."""
        return cls.objects.filter(is_active=True, enabled=True).first()
