"""
reCAPTCHA Configuration Model
"""
from django.db import models
from django.core.exceptions import ValidationError
import requests
import logging

logger = logging.getLogger(__name__)

class ReCaptchaConfig(models.Model):
    """
    Model to store reCAPTCHA configuration settings
    """
    name = models.CharField(
        max_length=100,
        help_text="A descriptive name for this reCAPTCHA configuration"
    )
    
    site_key = models.CharField(
        max_length=200,
        help_text="Your reCAPTCHA site key from Google reCAPTCHA console"
    )
    
    secret_key = models.CharField(
        max_length=200,
        help_text="Your reCAPTCHA secret key from Google reCAPTCHA console"
    )
    
    version = models.CharField(
        max_length=10,
        choices=[
            ('v2', 'reCAPTCHA v2'),
            ('v3', 'reCAPTCHA v3'),
        ],
        default='v3',
        help_text="reCAPTCHA version to use"
    )
    
    threshold = models.FloatField(
        default=0.5,
        help_text="Score threshold for reCAPTCHA v3 (0.0 to 1.0, where 1.0 is very likely a good interaction)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is currently active"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "reCAPTCHA Configuration"
        verbose_name_plural = "reCAPTCHA Configurations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.version})"
    
    def clean(self):
        """Validate reCAPTCHA configuration"""
        if self.version == 'v3' and not (0.0 <= self.threshold <= 1.0):
            raise ValidationError("Threshold must be between 0.0 and 1.0 for reCAPTCHA v3")
        
        if not self.site_key or not self.secret_key:
            raise ValidationError("Both site key and secret key are required")
    
    def test_configuration(self):
        """
        Test the reCAPTCHA configuration by making a test request
        """
        try:
            # Test with a dummy token to verify the keys are valid
            test_data = {
                'secret': self.secret_key,
                'response': 'test_token',
                'remoteip': '127.0.0.1'
            }
            
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'error-codes' in result:
                    # Check if it's just an invalid token error (which is expected)
                    error_codes = result.get('error-codes', [])
                    if 'invalid-input-response' in error_codes and len(error_codes) == 1:
                        return True, "reCAPTCHA configuration is valid (test token expected to fail)"
                    else:
                        return False, f"reCAPTCHA configuration error: {', '.join(error_codes)}"
                else:
                    return True, "reCAPTCHA configuration is valid"
            else:
                return False, f"Failed to connect to reCAPTCHA service (HTTP {response.status_code})"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error testing reCAPTCHA configuration: {str(e)}"
        except Exception as e:
            return False, f"Error testing reCAPTCHA configuration: {str(e)}"
    
    def get_verification_url(self):
        """Get the reCAPTCHA verification URL"""
        return 'https://www.google.com/recaptcha/api/siteverify'
    
    def verify_token(self, token, remote_ip=None):
        """
        Verify a reCAPTCHA token
        """
        try:
            data = {
                'secret': self.secret_key,
                'response': token,
            }
            
            if remote_ip:
                data['remoteip'] = remote_ip
            
            response = requests.post(
                self.get_verification_url(),
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                score = result.get('score', 0.0)
                action = result.get('action', '')
                error_codes = result.get('error-codes', [])
                
                # For v3, check if score meets threshold
                if self.version == 'v3' and success:
                    success = score >= self.threshold
                
                return {
                    'success': success,
                    'score': score,
                    'action': action,
                    'error_codes': error_codes,
                    'raw_response': result
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'raw_response': None
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'raw_response': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Verification error: {str(e)}',
                'raw_response': None
            }
