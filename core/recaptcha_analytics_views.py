"""
reCAPTCHA Analytics Views
Provides admin views for monitoring reCAPTCHA performance and metrics
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from .recaptcha_monitoring import get_recaptcha_metrics, get_recaptcha_success_rate, get_spam_reduction_estimate
import json


class ReCaptchaAnalyticsView(UserPassesTestMixin, TemplateView):
    """
    View for displaying reCAPTCHA analytics dashboard
    """
    template_name = 'recaptcha_analytics.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get reCAPTCHA metrics
        metrics = get_recaptcha_metrics()
        success_rate = get_recaptcha_success_rate()
        spam_reduction = get_spam_reduction_estimate()
        
        context.update({
            'page_title': 'reCAPTCHA Analytics',
            'metrics': metrics,
            'success_rate': success_rate,
            'spam_reduction': spam_reduction,
            'chart_data': self._prepare_chart_data(metrics),
        })
        
        return context
    
    def _prepare_chart_data(self, metrics):
        """
        Prepare data for charts
        """
        # Prepare hourly data for line chart
        hourly_data = []
        for hour, data in metrics['hourly'].items():
            hourly_data.append({
                'hour': hour,
                'success': data['success'],
                'failure': data['failure'],
                'error': data['error']
            })
        
        # Prepare form data for bar chart
        form_data = []
        for form, data in metrics['forms'].items():
            form_data.append({
                'form': form.title(),
                'success': data['success'],
                'failure': data['failure'],
                'error': data['error']
            })
        
        return {
            'hourly': hourly_data,
            'forms': form_data,
            'overall': metrics['overall']
        }


@staff_member_required
def recaptcha_analytics_api(request):
    """
    API endpoint for reCAPTCHA analytics data
    """
    if request.method == 'GET':
        metrics = get_recaptcha_metrics()
        success_rate = get_recaptcha_success_rate()
        spam_reduction = get_spam_reduction_estimate()
        
        return JsonResponse({
            'metrics': metrics,
            'success_rate': success_rate,
            'spam_reduction': spam_reduction,
            'status': 'success'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@staff_member_required
def recaptcha_analytics_reset(request):
    """
    Reset reCAPTCHA analytics data
    """
    if request.method == 'POST':
        from django.core.cache import cache
        
        # Clear all reCAPTCHA monitoring cache
        cache.delete_many(cache.keys('recaptcha_monitor:*'))
        
        return JsonResponse({
            'status': 'success',
            'message': 'reCAPTCHA analytics data has been reset'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
