"""Staff-only, cohort-based employability report (recorded hires, not census totals).

Counts an alumnus once, in the quarter of their earliest *recorded* hire
within the chosen report year and before the snapshot date. The denominator is
registered alumni profiles in the chosen graduating cohort; absent records do
not establish unemployment. No survey answers or personally identifying rows
are exposed by this aggregate report.
"""
import csv
from collections import defaultdict
from datetime import date, datetime
from zoneinfo import ZoneInfo
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from alumni_directory.models import Alumni
from core.report_periods import export_download_name, parse_report_period
from .models import EmploymentRecord
from .tracer_study import _can_view_tracer_reports


def _int_param(params, key, default, low=1900, high=2200):
    try:
        value = int(params.get(key) or default)
    except (TypeError, ValueError):
        raise ValueError(f'Choose a valid {key.replace("_", " ")}.') from None
    if not low <= value <= high:
        raise ValueError(f'Choose a valid {key.replace("_", " ")}.')
    return value


def _aggregate(cohort, hires, campus_names, college_names):
    """Pure aggregate; earliest hire per alumnus ensures no double count."""
    members = {}
    groups = defaultdict(lambda: {'graduates': 0, 'hires': [0, 0, 0, 0]})
    for pk, campus, college in cohort:
        group = (campus, college if campus == 'MAIN' else '')
        members[pk] = group
        groups[group]['graduates'] += 1
    first_hires = {}
    for alumni_id, started in hires:
        if alumni_id in members and (alumni_id not in first_hires or started < first_hires[alumni_id]):
            first_hires[alumni_id] = started
    for alumni_id, started in first_hires.items():
        groups[members[alumni_id]]['hires'][(started.month - 1) // 3] += 1
    rows = []
    for (campus, college), counts in sorted(groups.items(), key=lambda x: (x[0][0] != 'MAIN', x[0][0], x[0][1])):
        graduates = counts['graduates']
        quarters = counts['hires']
        rows.append({
            'campus': campus, 'college': college,
            'name': college_names.get(college, college or 'Unspecified') if campus == 'MAIN' else campus_names.get(campus, campus or 'Unspecified'),
            'graduates': graduates, 'hires': quarters,
            'rates': [round(100 * count / graduates, 2) if graduates else 0 for count in quarters],
            'total_hired': sum(quarters),
            'rate': round(100 * sum(quarters) / graduates, 2) if graduates else 0,
        })
    def subtotal(group_rows, label):
        people = sum(row['graduates'] for row in group_rows)
        quarters = [sum(row['hires'][i] for row in group_rows) for i in range(4)]
        total = sum(quarters)
        return {'name': label, 'graduates': people, 'hires': quarters,
                'rates': [round(100 * v / people, 2) if people else 0 for v in quarters],
                'total_hired': total, 'rate': round(100 * total / people, 2) if people else 0,
                'subtotal': True}
    mains = [row for row in rows if row['campus'] == 'MAIN']
    externals = [row for row in rows if row['campus'] != 'MAIN']
    display_rows = []
    if mains:
        display_rows.extend(mains)
        display_rows.append(subtotal(mains, 'Main campus subtotal'))
    if externals:
        display_rows.extend(externals)
        display_rows.append(subtotal(externals, 'External campuses subtotal'))
    grads = len(members)
    quarter_totals = [sum(row['hires'][i] for row in rows) for i in range(4)]
    total_hired = sum(quarter_totals)
    for row in display_rows:
        row['university_share'] = round(100 * row['total_hired'] / grads, 2) if grads else 0
    return {
        'rows': rows, 'display_rows': display_rows, 'graduates': grads, 'quarter_totals': quarter_totals,
        'total_hired': total_hired,
        'not_recorded': grads - total_hired,
        'rate': round(100 * total_hired / grads, 2) if grads else 0,
        'total_rates': [round(100 * n / grads, 2) if grads else 0 for n in quarter_totals],
    }


def _report_data(params):
    # USE_TZ=False makes timezone.now() naive and timezone.localdate() raises.
    # Use the configured university timezone independently of the host OS zone.
    today = datetime.now(ZoneInfo(settings.TIME_ZONE)).date()
    cohort_year = _int_param(params, 'cohort_year', today.year - 1)
    report_year = _int_param(params, 'report_year', params.get('year') or today.year)
    raw_as_of = params.get('as_of') or today.isoformat()
    try:
        as_of = date.fromisoformat(raw_as_of)
    except (TypeError, ValueError):
        raise ValueError('Enter a valid as-of date.') from None
    if as_of > today:
        raise ValueError('As-of date cannot be in the future.')
    if report_year > as_of.year:
        raise ValueError('Report year cannot be later than the as-of year.')
    period_params = params if params.get('period') else {'period': 'annual', 'year': report_year}
    period = parse_report_period(period_params, today=today)
    if not period.start:
        period = parse_report_period({'period':'annual', 'year':report_year}, today=today)
    if period.start.year != report_year or period.end.year != report_year:
        raise ValueError('Choose a timeframe within the selected hiring report year.')
    campus_filter = (params.get('campus') or '').strip()
    valid_campuses = dict(Alumni.CAMPUS_CHOICES)
    if campus_filter and campus_filter not in valid_campuses:
        raise ValueError('Choose a valid campus.')
    cohort_query = Alumni.objects.filter(graduation_year=cohort_year)
    if campus_filter:
        cohort_query = cohort_query.filter(campus=campus_filter)
    cohort = list(cohort_query.values_list('id', 'campus', 'college'))
    hire_end = min(as_of, period.end, date(report_year, 12, 31))
    hires = []
    if hire_end >= period.start and cohort:
        hires = list(EmploymentRecord.objects.filter(
            alumni_id__in=[row[0] for row in cohort],
            start_date__gte=period.start, start_date__lte=hire_end,
        ).values_list('alumni_id', 'start_date'))
    result = _aggregate(cohort, hires, valid_campuses, dict(Alumni.COLLEGE_CHOICES))
    result.update({
        'cohort_year': cohort_year, 'report_year': report_year, 'as_of': as_of,
        'campus_filter': campus_filter, 'campus_choices': Alumni.CAMPUS_CHOICES,
        'generation_date': today, 'period':period, 'period_kind':period.kind,
        'methodology': ('Counts registered alumni profiles only, not the complete official graduate registry. '
                        'A recorded hire is the earliest employment start date within the selected timeframe. '
                        'Each person counts once in the selected window; employment outside it and entries without start dates '
                        'are not included. Missing hire records must not be interpreted as unemployment.'),
    })
    return result


def _table_rows(report):
    for row in report['display_rows']:
        values = [row['name'], row['graduates']]
        for n, rate in zip(row['hires'], row['rates']):
            values += [n, f'{rate:.2f}%']
        yield values + [row['total_hired'], f"{row['rate']:.2f}%", f"{row['university_share']:.2f}%"]
    totals = ['UNIVERSITY TOTAL', report['graduates']]
    for n, rate in zip(report['quarter_totals'], report['total_rates']):
        totals += [n, f'{rate:.2f}%']
    yield totals + [report['total_hired'], f"{report['rate']:.2f}%", f"{report['rate']:.2f}%"]


def _export_report(report, format_name):
    period = report['period']
    base = f"employability_cohort-{report['cohort_year']}_as-of-{report['as_of'].isoformat()}"
    columns = ['Campus / College', 'Registered graduates'] + [name for q in range(1, 5) for name in (f'Hired Q{q}', f'Q{q} rate')] + ['Total hired', 'Group rate', 'Share of cohort']
    rows = list(_table_rows(report))
    if format_name == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{export_download_name(base, period, "csv")}"'
        writer = csv.writer(response)
        writer.writerow(['NORSU OFFICE OF ALUMNI AFFAIRS — GRADUATE EMPLOYABILITY REPORT'])
        writer.writerow(['Graduating cohort', report['cohort_year'], 'Hires in year', report['report_year'], 'Period', period.label, 'As of', report['as_of']])
        writer.writerow([report['methodology']])
        writer.writerow(columns)
        writer.writerows(rows)
        return response
    if format_name in ('excel', 'xlsx'):
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Employability'
        sheet.append(['NEGROS ORIENTAL STATE UNIVERSITY — OFFICE OF ALUMNI AFFAIRS'])
        sheet.append([f"GRADUATE EMPLOYABILITY REPORT | Class {report['cohort_year']} | {period.label} | As of {report['as_of']}"])
        sheet.append([report['methodology']])
        sheet.append([])
        sheet.append(columns)
        for values in rows:
            sheet.append(values)
        sheet.freeze_panes = 'C6'
        sheet.auto_filter.ref = f'A5:M{sheet.max_row}'
        sheet.column_dimensions['A'].width = 44
        for letter in 'BCDEFGHIJKLM':
            sheet.column_dimensions[letter].width = 18
        for row in (1, 2):
            sheet.cell(row=row, column=1).font = Font(bold=True, color='172541', size=13)
        sheet.row_dimensions[3].height = 45
        sheet.cell(row=3, column=1).alignment = Alignment(wrap_text=True)
        for cell in sheet[5]:
            cell.fill = PatternFill('solid', fgColor='172541')
            cell.font = Font(bold=True, color='FFFFFF')
            cell.alignment = Alignment(wrap_text=True)
        for cell in sheet[sheet.max_row]:
            cell.font = Font(bold=True)
        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{export_download_name(base, period, "xlsx")}"'
        return response
    if format_name == 'pdf':
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
        output = BytesIO()
        document = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=34, rightMargin=34, topMargin=28, bottomMargin=32)
        styles = getSampleStyleSheet()
        heading = ParagraphStyle('norsu-heading', parent=styles['Heading2'], textColor=colors.HexColor('#172541'), alignment=TA_CENTER)
        from pathlib import Path
        from django.conf import settings
        from reportlab.platypus import Image
        header_path = Path(settings.BASE_DIR) / 'static' / 'images' / 'norsu-header.png'
        elements = []
        if header_path.is_file():
            elements.append(Image(str(header_path), width=670, height=63))
        elements += [Paragraph('NEGROS ORIENTAL STATE UNIVERSITY', heading),
                    Paragraph('Office of Alumni Affairs — Graduate Employability Report', styles['Heading3']),
                    Paragraph(f"Graduating cohort {report['cohort_year']} | Reporting window {period.label} | As of {report['as_of']}", styles['Normal']),
                    Spacer(1, 12)]
        white_style = ParagraphStyle('norsu-col-header', parent=styles['Normal'], textColor=colors.white, fontSize=7)
        data = [[Paragraph(str(cell), white_style) for cell in columns]]
        for record in rows:
            data.append([Paragraph(str(cell), styles['Normal']) for cell in record])
        tbl = Table(data, colWidths=[161, 72] + [42, 42] * 4 + [61, 56, 61], repeatRows=1, hAlign='CENTER')
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#172541')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F5F2EC')]),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E7D8B9')),
            ('GRID', (0,0), (-1,-1), .4, colors.HexColor('#D5D7DB')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))
        elements += [tbl, Spacer(1, 10), Paragraph(report['methodology'], styles['Normal']),
                     Spacer(1, 12), Paragraph('Generated by NORSU Alumni Portal | Office of Alumni Affairs | Official registry reconciliation required', styles['Italic'])]
        document.build(elements)
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{export_download_name(base, period, "pdf")}"'
        return response
    raise Http404('Unsupported export format')


@login_required
@require_GET
def employability_report(request):
    if not _can_view_tracer_reports(request.user):
        raise Http404
    try:
        data = _report_data(request.GET)
    except ValueError as error:
        return render(request, 'tracer_study/employability_report.html', {
            'error': str(error), 'campus_choices': Alumni.CAMPUS_CHOICES,
            'cohort_year': request.GET.get('cohort_year', ''),
            'report_year': request.GET.get('report_year', ''),
            'as_of': request.GET.get('as_of', ''),
            'campus_filter': request.GET.get('campus', ''),
            'period_kind': request.GET.get('period') or 'annual',
        }, status=400)
    format_name = (request.GET.get('format') or '').lower()
    if format_name:
        return _export_report(data, format_name)
    return render(request, 'tracer_study/employability_report.html', data)
