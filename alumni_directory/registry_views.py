"""Restricted Graduate Registry administration: read, compare, then import."""
import csv
import logging
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import Alumni, GraduateRegistry
from .services.graduate_registry_import import compare_graduate_registry, import_graduate_registry

logger = logging.getLogger(__name__)


def can_manage_registry(user):
    if not user.is_authenticated:
        return False
    # The university-wide eligibility list must not be exposed to regular alumni,
    # campus coordinators without central privileges, or unauthenticated users.
    profile = getattr(user, 'profile', None)
    return bool(user.is_superuser or (
        user.is_staff and not getattr(profile, 'is_alumni_coordinator', False)
        and not getattr(profile, 'is_hr', False)
    ))


@login_required
def graduate_registry(request):
    if not can_manage_registry(request.user):
        raise PermissionDenied('Only central administrators can view the university-wide Graduate Registry.')
    if request.method != 'GET':
        return HttpResponse(status=405)
    queryset = GraduateRegistry.objects.select_related('claimed_by').all()
    search = request.GET.get('q', '').strip()[:100]
    year = request.GET.get('year', '').strip()
    campus = request.GET.get('campus', '').strip()
    college = request.GET.get('college', '').strip()
    status = request.GET.get('status', '').strip()
    if search:
        queryset = queryset.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(course__icontains=search) | Q(major__icontains=search))
    if year:
        if not (year.isdecimal() and 1940 <= int(year) <= 2100): year = ''
        else: queryset = queryset.filter(graduation_year=int(year))
    if campus:
        if campus not in dict(Alumni.CAMPUS_CHOICES): campus = ''
        else: queryset = queryset.filter(campus=campus)
    if college:
        if college not in dict(Alumni.COLLEGE_CHOICES): college = ''
        else: queryset = queryset.filter(college=college)
    if status == 'claimed': queryset = queryset.filter(claimed_by__isnull=False)
    elif status == 'available': queryset = queryset.filter(claimed_by__isnull=True)
    elif status: status = ''
    page = Paginator(queryset.order_by('-graduation_year', 'last_name', 'first_name', 'pk'), 25).get_page(request.GET.get('page'))
    return render(request, 'alumni_directory/graduate_registry.html', {
        'registry_page': page,
        'registry_total': GraduateRegistry.objects.count(),
        'registry_claimed': GraduateRegistry.objects.filter(claimed_by__isnull=False).count(),
        'registry_available': GraduateRegistry.objects.filter(claimed_by__isnull=True).count(),
        'registry_filtered': queryset.count(),
        'campuses': Alumni.CAMPUS_CHOICES, 'colleges': Alumni.COLLEGE_CHOICES,
        'years': GraduateRegistry.objects.order_by('-graduation_year').values_list('graduation_year', flat=True).distinct(),
        'q': search, 'selected_year': year, 'selected_campus': campus,
        'selected_college': college, 'selected_status': status,
    })


def _registry_file(request):
    upload = request.FILES.get('registry_file')
    if not upload:
        raise ValueError('Select a CSV or Excel file before continuing.')
    campus = request.POST.get('campus', '')
    year = request.POST.get('year_fallback', '') or None
    return upload, campus, year


@require_POST
@login_required
def registry_compare(request):
    if not can_manage_registry(request.user):
        raise PermissionDenied('Only central administrators can compare registrar records.')
    try:
        upload, campus, year = _registry_file(request)
        comparison = compare_graduate_registry(upload, default_campus=campus, graduation_year_override=year)
        if request.POST.get('download') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="graduate_registry_comparison.csv"'
            writer = csv.writer(response)
            writer.writerow(('Source row', 'Name', 'Graduation year', 'Campus', 'College', 'Program', 'Result', 'Differences / reason'))
            for item in comparison['rows']:
                # Neutralize CSV spreadsheet-formula injection in exported registrar text.
                safe = lambda value: "'" + str(value) if str(value).lstrip().startswith(('=', '+', '-', '@')) else str(value)
                writer.writerow([safe(item.get(k, '')) for k in ('source','name','year','campus','college','course','status','changes')])
            return response
        # Keep the UI responsive on long rosters; full comparison can be downloaded as CSV.
        return JsonResponse({'ok': True, 'totals': comparison['totals'],
                             'rows': comparison['rows'][:100], 'shown': min(100, len(comparison['rows'])),
                             'total_rows': len(comparison['rows']), 'warnings': comparison['warnings'][:12]})
    except (ValueError, UnicodeError) as exc:
        return JsonResponse({'ok': False, 'message': str(exc)}, status=400)
    except Exception:
        logger.exception('Registrar comparison failed')
        return JsonResponse({'ok': False, 'message': 'Could not compare the file. No records were modified.'}, status=500)


@require_POST
@login_required
def registry_import(request):
    if not can_manage_registry(request.user):
        raise PermissionDenied('Only central administrators can import registrar records.')
    try:
        if request.POST.get('confirmed') != 'yes':
            raise ValueError('Review the comparison and confirm the import before saving.')
        upload, campus, year = _registry_file(request)
        result = import_graduate_registry(upload, default_campus=campus, graduation_year_override=year)
        return JsonResponse({'ok': True, 'created': result.created, 'updated': result.updated,
                             'skipped': result.skipped, 'warnings': result.warnings[:12]})
    except (ValueError, UnicodeError) as exc:
        return JsonResponse({'ok': False, 'message': str(exc)}, status=400)
    except Exception:
        logger.exception('Registrar import failed')
        return JsonResponse({'ok': False, 'message': 'Import failed. No changes were committed.'}, status=500)
