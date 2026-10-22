"""Restricted Graduate Registry administration: read, compare, then import."""
import csv
import hashlib
import json
import logging

from django.core import signing
from django.db import connection, transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import Alumni, GraduateRegistry
from .services.graduate_registry_import import (
    MAX_FILE_BYTES, compare_graduate_registry, import_graduate_registry,
)

logger = logging.getLogger(__name__)

# A compare receipt is valid only for the same registrar file, admin, campus,
# fallback year and the same current registry contents. No database migration,
# account creation or server-side file storage is needed.
COMPARISON_RECEIPT_SALT = 'alumni-directory.graduate-registry.review.v1'
COMPARISON_RECEIPT_MAX_AGE = 20 * 60


def _upload_fingerprint(upload):
    if upload.size > MAX_FILE_BYTES:
        raise ValueError('File exceeds the 10 MB maximum.')
    upload.seek(0)
    digest = hashlib.sha256()
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    return digest.hexdigest()


def _comparison_fingerprint(comparison):
    # Include unchanged rows, not only the preview subset: changes to an
    # existing registration must invalidate the administrator's prior review.
    payload = json.dumps({
        'totals': comparison['totals'], 'rows': comparison['rows'],
        'warnings': comparison['warnings'],
    }, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _make_review_receipt(request, upload, campus, year, comparison):
    return signing.dumps({
        'version': 1,
        'user': str(request.user.pk),
        'file': _upload_fingerprint(upload),
        'campus': campus,
        'fallback_year': str(year or ''),
        'registry_state': _comparison_fingerprint(comparison),
    }, salt=COMPARISON_RECEIPT_SALT, compress=True)


def _verify_review_receipt(request, upload, campus, year, comparison):
    receipt = request.POST.get('review_receipt', '')
    if not receipt:
        raise ValueError('Compare the uploaded file before confirming an import.')
    try:
        signed = signing.loads(
            receipt, salt=COMPARISON_RECEIPT_SALT,
            max_age=COMPARISON_RECEIPT_MAX_AGE,
        )
    except signing.BadSignature as exc:
        raise ValueError('This comparison expired or is invalid. Compare the file again.') from exc
    expected = {
        'version': 1,
        'user': str(request.user.pk),
        'file': _upload_fingerprint(upload),
        'campus': campus,
        'fallback_year': str(year or ''),
        'registry_state': _comparison_fingerprint(comparison),
    }
    if signed != expected:
        raise ValueError('The uploaded file, filters, or registry has changed. Compare the file again.')
    if not (comparison['totals']['new'] or comparison['totals']['update']):
        raise ValueError('There are no eligible new graduates or changes to import.')


def _lock_registry_imports():
    """Serialize confirmed registry imports across Gunicorn workers on PostgreSQL."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [1042026221])



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
                if item.get('status') == 'unchanged':
                    continue  # Only actionable differences are exported.
                # Neutralize CSV spreadsheet-formula injection in exported registrar text.
                safe = lambda value: "'" + str(value) if str(value).lstrip().startswith(('=', '+', '-', '@')) else str(value)
                writer.writerow([safe(item.get(k, '')) for k in ('source','name','year','campus','college','course','status','changes')])
            return response
        # Issue a short-lived signed receipt only after a successful comparison.
        receipt = _make_review_receipt(request, upload, campus, year, comparison)
        # Never bury a new or conflicting graduate among hundreds of exact matches.
        # All changes remain available through the separate comparison CSV export.
        changed = [row for row in comparison['rows'] if row.get('status') in ('update', 'review', 'skipped')]
        new = [row for row in comparison['rows'] if row.get('status') == 'new']
        # Give both review categories space in the preview, even on large rosters.
        preview = changed[:100] + new[:100]
        return JsonResponse({'ok': True, 'totals': comparison['totals'],
                             'rows': preview, 'shown': len(preview),
                             'total_rows': len(changed) + len(new), 'warnings': comparison['warnings'][:12],
                             'review_receipt': receipt})
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
        with transaction.atomic():
            _lock_registry_imports()
            # Recompare inside the same transaction. Signing only the file is not
            # enough: another import could have changed the registry after preview.
            current = compare_graduate_registry(
                upload, default_campus=campus, graduation_year_override=year
            )
            _verify_review_receipt(request, upload, campus, year, current)
            result = import_graduate_registry(
                upload, default_campus=campus, graduation_year_override=year
            )
        return JsonResponse({'ok': True, 'created': result.created, 'updated': result.updated,
                             'skipped': result.skipped, 'warnings': result.warnings[:12]})
    except (ValueError, UnicodeError) as exc:
        return JsonResponse({'ok': False, 'message': str(exc)}, status=400)
    except Exception:
        logger.exception('Registrar import failed')
        return JsonResponse({'ok': False, 'message': 'Import failed. No changes were committed.'}, status=500)
