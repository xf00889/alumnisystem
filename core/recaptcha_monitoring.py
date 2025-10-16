"""
reCAPTCHA Monitoring and Analytics
Provides monitoring, logging, and analytics for reCAPTCHA usage
"""

import logging
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from typing import Dict, Any, Optional
import json

logger = logging.getLogger('recaptcha')

class ReCaptchaMonitor:
    """
    Monitor reCAPTCHA usage, failures, and performance
    """
    
    def __init__(self):
        self.cache_prefix = 'recaptcha_monitor'
        self.cache_timeout = 3600  # 1 hour
    
    def log_success(self, form_name: str, user_ip: str, score: Optional[float] = None):
        """
        Log successful reCAPTCHA validation
        """
        data = {
            'form_name': form_name,
            'user_ip': user_ip,
            'score': score,
            'timestamp': timezone.now().isoformat(),
            'status': 'success'
        }
        
        logger.info(f"reCAPTCHA Success: {form_name} from {user_ip} (score: {score})")
        self._update_metrics('success', form_name)
    
    def log_failure(self, form_name: str, user_ip: str, reason: str, score: Optional[float] = None):
        """
        Log failed reCAPTCHA validation
        """
        data = {
            'form_name': form_name,
            'user_ip': user_ip,
            'reason': reason,
            'score': score,
            'timestamp': timezone.now().isoformat(),
            'status': 'failure'
        }
        
        logger.warning(f"reCAPTCHA Failure: {form_name} from {user_ip} - {reason} (score: {score})")
        self._update_metrics('failure', form_name)
        
        # Check for suspicious activity
        self._check_suspicious_activity(user_ip, form_name)
    
    def log_error(self, form_name: str, user_ip: str, error: str):
        """
        Log reCAPTCHA errors (network issues, etc.)
        """
        data = {
            'form_name': form_name,
            'user_ip': user_ip,
            'error': error,
            'timestamp': timezone.now().isoformat(),
            'status': 'error'
        }
        
        logger.error(f"reCAPTCHA Error: {form_name} from {user_ip} - {error}")
        self._update_metrics('error', form_name)
    
    def _update_metrics(self, status: str, form_name: str):
        """
        Update cached metrics for monitoring
        """
        # Update overall metrics
        overall_key = f"{self.cache_prefix}:overall:{status}"
        overall_count = cache.get(overall_key, 0)
        cache.set(overall_key, overall_count + 1, self.cache_timeout)
        
        # Update form-specific metrics
        form_key = f"{self.cache_prefix}:form:{form_name}:{status}"
        form_count = cache.get(form_key, 0)
        cache.set(form_key, form_count + 1, self.cache_timeout)
        
        # Update hourly metrics
        hour_key = f"{self.cache_prefix}:hourly:{timezone.now().strftime('%Y-%m-%d-%H')}:{status}"
        hour_count = cache.get(hour_key, 0)
        cache.set(hour_key, hour_count + 1, self.cache_timeout)
    
    def _check_suspicious_activity(self, user_ip: str, form_name: str):
        """
        Check for suspicious activity patterns
        """
        # Track failures per IP
        ip_key = f"{self.cache_prefix}:ip:{user_ip}:failures"
        failures = cache.get(ip_key, 0) + 1
        cache.set(ip_key, failures, self.cache_timeout)
        
        # Alert if too many failures from same IP
        if failures >= 10:  # Threshold for suspicious activity
            logger.warning(f"Suspicious reCAPTCHA activity detected: {failures} failures from {user_ip} on {form_name}")
            self._send_alert(f"High reCAPTCHA failure rate from {user_ip}: {failures} failures")
    
    def _send_alert(self, message: str):
        """
        Send alert for suspicious activity
        """
        # In a production environment, this would send emails, Slack notifications, etc.
        logger.critical(f"reCAPTCHA ALERT: {message}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current reCAPTCHA metrics
        """
        metrics = {
            'overall': {
                'success': cache.get(f"{self.cache_prefix}:overall:success", 0),
                'failure': cache.get(f"{self.cache_prefix}:overall:failure", 0),
                'error': cache.get(f"{self.cache_prefix}:overall:error", 0),
            },
            'forms': {},
            'hourly': {},
            'suspicious_ips': []
        }
        
        # Get form-specific metrics
        forms = ['login', 'signup', 'contact', 'event', 'feedback', 'password_reset']
        for form in forms:
            metrics['forms'][form] = {
                'success': cache.get(f"{self.cache_prefix}:form:{form}:success", 0),
                'failure': cache.get(f"{self.cache_prefix}:form:{form}:failure", 0),
                'error': cache.get(f"{self.cache_prefix}:form:{form}:error", 0),
            }
        
        # Get hourly metrics for last 24 hours
        for i in range(24):
            hour = timezone.now().replace(hour=(timezone.now().hour - i) % 24)
            hour_str = hour.strftime('%Y-%m-%d-%H')
            metrics['hourly'][hour_str] = {
                'success': cache.get(f"{self.cache_prefix}:hourly:{hour_str}:success", 0),
                'failure': cache.get(f"{self.cache_prefix}:hourly:{hour_str}:failure", 0),
                'error': cache.get(f"{self.cache_prefix}:hourly:{hour_str}:error", 0),
            }
        
        return metrics
    
    def get_success_rate(self) -> float:
        """
        Calculate overall success rate
        """
        success = cache.get(f"{self.cache_prefix}:overall:success", 0)
        failure = cache.get(f"{self.cache_prefix}:overall:failure", 0)
        total = success + failure
        
        if total == 0:
            return 0.0
        
        return (success / total) * 100
    
    def get_spam_reduction_estimate(self) -> Dict[str, Any]:
        """
        Estimate spam reduction based on reCAPTCHA failures
        """
        failure_count = cache.get(f"{self.cache_prefix}:overall:failure", 0)
        success_count = cache.get(f"{self.cache_prefix}:overall:success", 0)
        
        # Estimate that failures represent blocked spam attempts
        estimated_spam_blocked = failure_count
        total_attempts = success_count + failure_count
        
        if total_attempts == 0:
            return {
                'spam_blocked': 0,
                'total_attempts': 0,
                'reduction_percentage': 0.0
            }
        
        reduction_percentage = (estimated_spam_blocked / total_attempts) * 100
        
        return {
            'spam_blocked': estimated_spam_blocked,
            'total_attempts': total_attempts,
            'reduction_percentage': round(reduction_percentage, 2)
        }


# Global monitor instance
recaptcha_monitor = ReCaptchaMonitor()


def log_recaptcha_success(form_name: str, user_ip: str, score: Optional[float] = None):
    """
    Convenience function to log reCAPTCHA success
    """
    recaptcha_monitor.log_success(form_name, user_ip, score)


def log_recaptcha_failure(form_name: str, user_ip: str, reason: str, score: Optional[float] = None):
    """
    Convenience function to log reCAPTCHA failure
    """
    recaptcha_monitor.log_failure(form_name, user_ip, reason, score)


def log_recaptcha_error(form_name: str, user_ip: str, error: str):
    """
    Convenience function to log reCAPTCHA error
    """
    recaptcha_monitor.log_error(form_name, user_ip, error)


def get_recaptcha_metrics() -> Dict[str, Any]:
    """
    Convenience function to get reCAPTCHA metrics
    """
    return recaptcha_monitor.get_metrics()


def get_recaptcha_success_rate() -> float:
    """
    Convenience function to get reCAPTCHA success rate
    """
    return recaptcha_monitor.get_success_rate()


def get_spam_reduction_estimate() -> Dict[str, Any]:
    """
    Convenience function to get spam reduction estimate
    """
    return recaptcha_monitor.get_spam_reduction_estimate()
