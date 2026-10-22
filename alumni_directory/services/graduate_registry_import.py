"""Import registrar graduate lists without creating application user accounts.

Handles row-per-graduate CSVs and registrar lists organized by college,
program, major, and roster-number (CSV or .xlsx). No third-party XLSX runtime
package is necessary: only safe, bounded XML members are read from the ZIP.
"""
from __future__ import annotations

import csv
import io
import posixpath
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

from django.db import transaction

from alumni_directory.models import Alumni, GraduateRegistry

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_ROSTER_ROWS = 30000
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
P = '{http://schemas.openxmlformats.org/package/2006/relationships}'

CAMPUS_ALIASES = {
    'NORSU-MAIN': 'MAIN', 'NORSU-BAIS': 'BAIS1', 'NORSU-GUI': 'GUI',
    'NORSU-MAB': 'MAB', 'NORSU-BSC': 'BSC', 'NORSU-SIA': 'SIATON',
    'NORSU-PAM': 'PAM',
}
COLLEGE_ALIASES = {
    'AGRICULTURE AND FORESTRY': 'CAFF',
    'AGRICULTURE, FORESTRY AND FISHERIES': 'CAFF',
    'ARTS AND SCIENCES': 'CAS',
    'BUSINESS ADMINISTRATION': 'CBA',
    'CRIMINAL JUSTICE EDUCATION': 'CCJE',
    'INDUSTRIAL TECHNOLOGY': 'CIT',
    'TEACHER EDUCATION': 'CTE',
    'EDUCATION': 'CTE',
    'ENGINEERING': 'CEA',
    'LAW': 'COL',
    'TOURISM AND HOSPITALITY MANAGEMENT': 'CTHM',
    'NURSING, PHARMACY AND ALLIED HEALTH SCIENCES': 'CNPAHS',
}


@dataclass
class RegistryImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)

    def warn(self, location, message):
        self.skipped += 1
        if len(self.warnings) < 30:
            self.warnings.append(f'{location}: {message}')


def clean(value):
    return ' '.join(str(value if value is not None else '').split()).strip()


def _year_pair(text):
    match = re.search(r'\b(?:SY\s*)?(19\d{2}|20\d{2})\s*[-–]\s*(19\d{2}|20\d{2})\b', text, re.I)
    if match:
        first, second = map(int, match.groups())
        if second == first + 1:
            return first, second
    return None


def _college_code(label):
    key = re.sub(r'\s+', ' ', label).strip().upper()
    key = re.sub(r'^COLLEGE\s+OF\s+', '', key)
    if key in COLLEGE_ALIASES:
        return COLLEGE_ALIASES[key]
    names = {re.sub(r'^COLLEGE OF ', '', v.upper()): k for k, v in Alumni.COLLEGE_CHOICES}
    return names.get(key, '')


def _cell_value(cell, shared):
    kind = cell.get('t', '')
    if kind == 'inlineStr':
        return ''.join(n.text or '' for n in cell.iter(S+'t'))
    node = cell.find(S+'v')
    if node is None or node.text is None:
        return ''
    if kind == 's':
        try:
            return shared[int(node.text)]
        except (ValueError, IndexError):
            raise ValueError('Invalid XLSX shared-string reference')
    return node.text


def _xlsx_sheets(data):
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValueError('This file is not a valid Excel workbook.') from exc
    with archive:
        safe = [x for x in archive.infolist() if not x.is_dir()]
        if any(x.file_size > MAX_UNCOMPRESSED_BYTES for x in safe) or sum(x.file_size for x in safe) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError('The Excel workbook expands beyond the permitted size.')
        members = set(archive.namelist())
        if 'xl/workbook.xml' not in members or 'xl/_rels/workbook.xml.rels' not in members:
            raise ValueError('Excel workbook metadata is missing.')
        shared = []
        if 'xl/sharedStrings.xml' in members:
            document = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            shared = [''.join(item.itertext()) for item in document.findall(S+'si')]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'): r.get('Target', '') for r in relationships.findall(P+'Relationship')}
        found_sheet = False
        for sheet in workbook.findall('.//'+S+'sheet'):
            label = clean(sheet.get('name'))[:100]
            target = targets.get(sheet.get(R+'id'), '')
            path = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl', target))
            if not path.startswith('xl/worksheets/') or path not in members:
                continue
            found_sheet = True
            root = ET.fromstring(archive.read(path))
            rows = []
            for ix, row in enumerate(root.findall('.//'+S+'sheetData/'+S+'row'), 1):
                row_number = int(row.get('r', ix))
                if len(rows) > MAX_ROSTER_ROWS:
                    raise ValueError('Excel workbook contains too many rows.')
                values = [''] * 16
                for cell in row.findall(S+'c'):
                    match = re.match(r'([A-Z]+)', cell.get('r', ''))
                    if not match:
                        continue
                    col = 0
                    for char in match.group(1):
                        col = col * 26 + ord(char) - 64
                    if 1 <= col <= len(values):
                        values[col - 1] = _cell_value(cell, shared)
                rows.append((row_number, values))
            yield label, rows
        if not found_sheet:
            raise ValueError('Excel workbook has no readable worksheets.')


def _csv_rows(data):
    try:
        decoded = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        decoded = data.decode('cp1252')
    return [(i, row) for i, row in enumerate(csv.reader(io.StringIO(decoded, newline="")), 1)]


def _structured_rows(rows, filename, default_campus, fallback_year, result):
    nonempty = [(n, r) for n, r in rows if any(clean(c) for c in r)]
    if not nonempty:
        return None
    head = [clean(c).lower().replace(' ', '').replace('_','').replace('-', '') for c in nonempty[0][1]]
    if not (('fullname' in head or ('firstname' in head and 'lastname' in head)) and ('year' in head or 'year1' in head or 'graduationyear' in head)):
        return None
    output = []
    for n, row in nonempty[1:]:
        cells = {head[i]: clean(row[i]) for i in range(min(len(head), len(row)))}
        if not any(cells.values()):
            continue
        full = cells.get('fullname','')
        given = cells.get('firstname','')
        family = cells.get('lastname','')
        if full and not (given and family):
            if ',' in full:
                family, given = (clean(x) for x in full.split(',', 1))
            else:
                tokens = full.split()
                if len(tokens) >= 2:
                    given, family = ' '.join(tokens[:-1]), tokens[-1]
        output.append({
            'first_name': given, 'last_name': family,
            'middle_name': cells.get('middlename',''), 'suffix': cells.get('suffix',''),
            'graduation_year': cells.get('year1') or cells.get('year') or cells.get('graduationyear') or fallback_year,
            'course': cells.get('coursegrad') or cells.get('course') or cells.get('program',''),
            'major': cells.get('major',''), 'college': cells.get('college',''),
            'campus': cells.get('campus') or default_campus,
            'email': cells.get('emailaddress') or cells.get('email',''),
            'source_sheet': '', 'source_row': n,
        })
    return output


def _roster_rows(rows, filename, sheet, default_campus, fallback_year, result):
    # A registrar roster has a number in column A, given name in B, middle in C,
    # surname in D, and (sometimes) suffix in E. College, degree and major are
    # section headings rather than repeated in each person row.
    school_year = None
    for _, values in rows[:100]:
        text = clean(values[0] if values else '')
        if 'CANDIDATES FOR GRADUATION' in text.upper() or re.search(r'\bSY\s+\d{4}', text, re.I):
            school_year = _year_pair(text)
            if school_year:
                break
    school_year = school_year or _year_pair(filename)
    final_year = school_year[1] if school_year else fallback_year
    first_year = school_year[0] if school_year else None
    current_college = ''
    program = ''
    major = ''
    output = []
    for number, values in rows:
        if len(output) > MAX_ROSTER_ROWS:
            raise ValueError('Roster exceeds the permitted number of graduates.')
        first = clean(values[0]) if values else ''
        label = first.upper()
        if label.startswith('COLLEGE'):
            current_college = _college_code(first)
            program = major = ''
            continue
        line = re.sub(r"^CONT['’]?N\s+OF\s+", '', first, flags=re.I)
        if re.match(r'^BACHELOR\s+', line, re.I):
            if re.match(r'^BACHELOR\s+', first, re.I):
                program = line
                major = ''
            else:
                # Continued page: use any major embedded in the course title.
                program = line
            match = re.search(r'\s*-\s*([A-Z][A-Za-z ]+|HRM)$', line, re.I)
            if match and match.start() > 15:
                program = clean(line[:match.start()])
                embedded_major = clean(match.group(1))
                if embedded_major.upper() == 'HRM':
                    major = 'Human Resource Management'
                elif not major or major.casefold() != embedded_major.casefold():
                    major = embedded_major
            continue
        if re.match(r'^\s*(?:MAJOR\s*(?:IN)?|AREA\s+OF\s+CONC(?:ENTRATION)?\.?|AREA OF CONCENTRATION)\s*:', first, re.I):
            major = clean(first.split(':', 1)[1])
            continue
        if not re.fullmatch(r'\*{0,2}\d+', first):
            continue
        given = clean(values[1] if len(values) > 1 else '')
        middle = clean(values[2] if len(values) > 2 else '')
        family = clean(values[3] if len(values) > 3 else '')
        suffix = clean(values[4] if len(values) > 4 else '')
        if not (given and family and current_college and program):
            result.warn(f'{sheet or filename} row {number}', 'Name or college/program heading is missing')
            continue
        year = first_year if first.startswith('*') and not first.startswith('**') else final_year
        if not year:
            result.warn(f'{sheet or filename} row {number}', 'Graduation year cannot be identified')
            continue
        output.append({
            'first_name': given, 'middle_name': middle, 'last_name': family,
            'suffix': suffix, 'graduation_year': year,
            'course': program, 'major': major,
            'college': current_college, 'campus': default_campus,
            'email': '', 'source_sheet': sheet, 'source_row': number,
        })
    return output


def _parse_data(data, filename, default_campus, fallback_year, result):
    suffix = Path(filename).suffix.lower()
    if suffix == '.csv':
        rows = _csv_rows(data)
        structured = _structured_rows(rows, filename, default_campus, fallback_year, result)
        return structured if structured is not None else _roster_rows(rows, filename, '', default_campus, fallback_year, result)
    if suffix == '.xlsx':
        records = []
        for sheet, rows in _xlsx_sheets(data):
            structured = _structured_rows(rows, filename, default_campus, fallback_year, result)
            records.extend(structured if structured is not None else _roster_rows(rows, filename, sheet, default_campus, fallback_year, result))
        return records
    raise ValueError('Only .csv and .xlsx registrar files are supported.')


def _read_uploaded_registry(upload, *, default_campus, graduation_year_override=None):
    """Parse once with the same safety limits for preview, comparison and import."""
    filename = Path(upload.name or '').name
    if Path(filename).suffix.lower() not in ('.csv', '.xlsx'):
        raise ValueError('Only .csv and .xlsx registrar files are supported.')
    campus = CAMPUS_ALIASES.get(clean(default_campus).upper(), clean(default_campus).upper())
    if campus not in dict(Alumni.CAMPUS_CHOICES):
        raise ValueError('Select the registrar-confirmed campus before comparing or importing.')
    fallback_year = None
    if graduation_year_override not in (None, ''):
        try:
            fallback_year = int(graduation_year_override)
        except (TypeError, ValueError):
            raise ValueError('The optional year must be a four-digit graduation year.')
        if not 1940 <= fallback_year <= 2100:
            raise ValueError('Graduation year must be between 1940 and 2100.')
    if upload.size > MAX_FILE_BYTES:
        raise ValueError('File is too large (maximum 10 MB).')
    data = upload.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError('File is too large (maximum 10 MB).')
    result = RegistryImportResult()
    records = _parse_data(data, filename, campus, fallback_year, result)
    if not records:
        raise ValueError('No valid graduate rows were found. Check the file layout, academic year and college/program headings.')
    if len(records) > MAX_ROSTER_ROWS:
        raise ValueError('Too many graduates in a single file.')
    return filename, campus, records, result


def _prepare_registry_row(info, campus):
    """Normalize once for both preview and commit. Returns an explanatory error when invalid."""
    try:
        year = int(info.get('graduation_year') or 0)
    except (ValueError, TypeError):
        year = 0
    first = clean(info.get('first_name'))
    last = clean(info.get('last_name'))
    course = clean(info.get('course'))
    selected = clean(info.get('campus') or campus).upper()
    selected = CAMPUS_ALIASES.get(selected, selected)
    college = clean(info.get('college'))
    if college and college not in dict(Alumni.COLLEGE_CHOICES):
        college = _college_code(college)
    if not (first and last and 1940 <= year <= 2100 and selected in dict(Alumni.CAMPUS_CHOICES)):
        return None, 'Invalid or incomplete name, year or campus'
    if any(len(val) > limit for val, limit in (
        (first,150),(last,150),(course,200),
        (clean(info.get('middle_name')),150),
        (clean(info.get('major')),200),(clean(info.get('suffix')),30),
    )):
        return None, 'A value is longer than the allowed database field'
    return {
        'first_name': first, 'last_name': last,
        'graduation_year': year, 'campus': selected, 'course': course,
        'middle_name': clean(info.get('middle_name')),
        'suffix': clean(info.get('suffix')),
        'college': college, 'major': clean(info.get('major')),
        'email': clean(info.get('email')),
        'source_sheet': clean(info.get('source_sheet'))[:100],
        'source_row': info.get('source_row'),
    }, None


def _find_registry_match(info, *, lock=False):
    queryset = GraduateRegistry.objects
    if lock:
        queryset = queryset.select_for_update()
    matches = list(queryset.filter(
        first_name__iexact=info['first_name'],
        last_name__iexact=info['last_name'],
        campus=info['campus'],
        graduation_year=info['graduation_year'],
    )[:3])
    same_course = [r for r in matches if clean(r.course).casefold() == info['course'].casefold()]
    if len(same_course) == 1:
        return same_course[0], None
    if len(matches) > 1 or len(same_course) > 1:
        return None, 'Multiple existing records share this identity; review manually'
    if len(matches) == 1:
        entry = matches[0]
        # Different nonblank degree programs can be different people with the same name.
        if clean(entry.course) and info['course'] and clean(entry.course).casefold() != info['course'].casefold():
            return None, 'Existing name/year/campus matches another program; review manually'
        return entry, None
    return None, None


def _row_changes(entry, info):
    changed = []
    for key in ('course', 'middle_name', 'suffix', 'college', 'major', 'email'):
        incoming = info.get(key, '')
        previous = clean(getattr(entry, key, ''))
        # Import never overwrites email and never erases a field with blank data.
        if not incoming or (key == 'email' and previous):
            continue
        if incoming.casefold() != previous.casefold():
            changed.append(key.replace('_', ' ').title())
    return changed


def _reconcile_rows(records, campus, filename, result, *, commit=False):
    """Same matching policy for preview and import; writes are atomic when requested."""
    summary = {'new': 0, 'unchanged': 0, 'update': 0, 'review': 0, 'skipped': result.skipped}
    rows = []
    seen_keys = set()
    for raw in records:
        place = f"{raw.get('source_sheet') or filename} row {raw.get('source_row')}"
        info, error = _prepare_registry_row(raw, campus)
        if error:
            summary['skipped'] += 1
            if len(result.warnings) < 30: result.warnings.append(f'{place}: {error}')
            rows.append({'name': clean(raw.get('first_name')) + ' ' + clean(raw.get('last_name')), 'year': str(raw.get('graduation_year') or ''), 'campus': campus, 'course': clean(raw.get('course')), 'college': clean(raw.get('college')), 'source': place, 'status': 'skipped', 'changes': error})
            continue
        key = (info['first_name'].casefold(), info['last_name'].casefold(), info['campus'], info['graduation_year'], info['course'].casefold())
        if key in seen_keys:
            entry, ambiguity = None, 'Duplicate graduate row in the uploaded file'
        else:
            seen_keys.add(key)
            entry, ambiguity = _find_registry_match(info, lock=commit)
        changes = _row_changes(entry, info) if entry is not None else []
        if not ambiguity and entry is not None and entry.claimed_by_id and changes:
            ambiguity = 'Claimed registry record has different details; review before changing'
        if ambiguity:
            status = 'review'; detail = ambiguity
        elif entry is None:
            status = 'new'; detail = 'Not yet in Graduate Registry'
        elif changes:
            status = 'update'; detail = ', '.join(changes)
        else:
            status = 'unchanged'; detail = 'Matches registry'
        summary[status] += 1
        rows.append({
            'name': f"{info['last_name']}, {info['first_name']} {info['middle_name']}".strip(),
            'year': info['graduation_year'], 'campus': info['campus'],
            'course': info['course'], 'college': info['college'], 'source': place,
            'status': status, 'changes': detail,
            'claimed': bool(entry and entry.claimed_by_id),
        })
        if commit and status == 'new':
            GraduateRegistry.objects.create(
                first_name=info['first_name'], last_name=info['last_name'],
                campus=info['campus'], graduation_year=info['graduation_year'],
                course=info['course'], email=info['email'],
                middle_name=info['middle_name'], suffix=info['suffix'], college=info['college'], major=info['major'],
                source_filename=filename[:255],source_sheet=info['source_sheet'],source_row=info['source_row'],
            )
        elif commit and status in ('update', 'unchanged'):
            # Refresh import provenance, but never replace an already-claimed identity.
            entry.source_filename = filename[:255]
            entry.source_sheet = info['source_sheet']
            entry.source_row = info['source_row']
            if not entry.claimed_by_id:
                if info['course']: entry.course = info['course']
                for attr in ('middle_name', 'suffix', 'college', 'major'):
                    if info[attr]: setattr(entry, attr, info[attr])
                if info['email'] and not entry.email: entry.email = info['email']
            entry.save()
    return summary, rows


def compare_graduate_registry(upload, *, default_campus, graduation_year_override=None):
    """Read-only reconciliation; NEVER saves, deletes or creates registry/user records."""
    filename, campus, records, result = _read_uploaded_registry(
        upload, default_campus=default_campus, graduation_year_override=graduation_year_override
    )
    totals, rows = _reconcile_rows(records, campus, filename, result)
    return {'filename': filename, 'totals': totals, 'rows': rows, 'warnings': result.warnings}


def import_graduate_registry(upload, *, default_campus='BSC', graduation_year_override=None):
    """Atomic import preserving claims and requiring review for ambiguous records."""
    filename, campus, records, result = _read_uploaded_registry(
        upload, default_campus=default_campus, graduation_year_override=graduation_year_override
    )
    with transaction.atomic():
        totals, _ = _reconcile_rows(records, campus, filename, result, commit=True)
    result.created = totals['new']
    result.updated = totals['update'] + totals['unchanged']
    result.skipped = totals['review'] + totals['skipped']
    if totals['review'] and len(result.warnings) < 30:
        result.warnings.append(f"{totals['review']} ambiguous/claimed rows need manual review and were not imported")
    return result
