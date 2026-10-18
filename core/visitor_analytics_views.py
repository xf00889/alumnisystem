"""Superuser-only privacy-limited traffic summary."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Max, Sum
from django.shortcuts import render
from django.utils import timezone

from core.models.visitor_analytics import DailyVisitor


@user_passes_test(lambda user: user.is_authenticated and user.is_active and user.is_superuser)
def visitor_analytics_dashboard(request):
    days = 7 if request.GET.get('days') == '7' else 30
    today = timezone.localdate()
    since = today - timedelta(days=days-1)
    records = DailyVisitor.objects.filter(day__gte=since, day__lte=today)
    rows = (records.values('ip_address').annotate(
        last_seen=Max('last_seen'), sampled_page_loads=Sum('sampled_page_loads'),
        active_days=Count('day', distinct=True),
    ).order_by('-last_seen')[:100])
    daily_counts = dict(records.values('day').annotate(unique_ips=Count('ip_address')).values_list('day','unique_ips'))
    chart = [{'day': (since+timedelta(days=d)), 'count':daily_counts.get(since+timedelta(days=d),0)} for d in range(days)]
    peak = max((item['count'] for item in chart), default=0) or 1
    for item in chart:
        item['height'] = round(100 * item['count'] / peak)
    now = timezone.now()
    context = {
        'analytics_enabled': settings.VISITOR_ANALYTICS_ENABLED,
        'days': days,
        'retention_days': settings.VISITOR_ANALYTICS_RETENTION_DAYS,
        'unique_ips': records.values('ip_address').distinct().count(),
        'today_ips': records.filter(day=today).count(),
        'recent_ips': records.filter(last_seen__gte=now-timedelta(minutes=15)).values('ip_address').distinct().count(),
        'sampled_page_loads': records.aggregate(total=Sum('sampled_page_loads'))['total'] or 0,
        'rows': rows,
        'chart': chart,
        'visible_count': len(rows),
    }
    return render(request, 'admin/visitor_analytics.html', context)
