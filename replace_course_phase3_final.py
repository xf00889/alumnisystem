#!/usr/bin/env python3
"""
Phase 3 FINAL: Comprehensive replacement of ALL remaining user-facing 'Course' text.
This catches everything missed in previous phases.
"""
import re
from pathlib import Path
import shutil
from datetime import datetime

def should_skip_line(line):
    """Lines that should be completely skipped."""
    # Skip database field references
    if re.search(r'\{\{.*\.course.*\}\}', line):
        return True
    
    # Skip form field names and IDs (but NOT labels)
    if re.search(r'(name|id)=["\']course["\']', line) and 'label' not in line.lower():
        return True
    
    # Skip URL parameters
    if re.search(r'[&?]course=', line):
        return True
    
    # Skip JavaScript variable declarations
    if re.search(r'(const|let|var)\s+course\s*[=:]', line):
        return True
    
    # Skip data attributes
    if re.search(r'data-[a-z-]*=["\']course["\']', line):
        return True
    
    # Skip querySelector/getElementById
    if re.search(r'(querySelector|getElementById|getElementsByClassName)\(["\'][^"\']*course', line):
        return True
    
    # Skip params.append
    if re.search(r'params\.append\(["\'].*course', line):
        return True
    
    # Skip forEach with course variable
    if re.search(r'forEach\(\s*course\s*=>', line):
        return True
    
    # Skip template loop variables
    if re.search(r'\{%\s*for\s+course\s+in\s+', line):
        return True
    
    return False

def replace_course_in_line(line):
    """Replace 'Course' with 'Program' in user-facing text."""
    if should_skip_line(line):
        return line, False
    
    original_line = line
    
    # CRITICAL: Label with for="course" - replace the text but keep the for attribute
    # <label class="search-label" for="course">Course</label>
    line = re.sub(
        r'(<label[^>]*for=["\']course["\'][^>]*>)\s*Course\s*(</label>)',
        r'\1Program\2',
        line
    )
    
    # Generic label text
    line = re.sub(r'(<label[^>]*>)([^<]*)\bCourse\b([^<]*)(</label>)', r'\1\2Program\3\4', line)
    
    # Filter tags - "Course: value"
    line = re.sub(r'(\s+)Course:\s+', r'\1Program: ', line)
    
    # Placeholder text
    line = re.sub(r'(placeholder=["\'][^"\']*)\bcourse\b([^"\']*["\'])', r'\1program\2', line)
    line = re.sub(r'(placeholder=["\'][^"\']*)\bCourse\b([^"\']*["\'])', r'\1Program\2', line)
    
    # Search placeholders specifically
    line = re.sub(r'(placeholder=["\']Search\s+)courses(\.\.\.["\'])', r'\1programs\2', line, flags=re.IGNORECASE)
    
    # Text in paragraph, small, strong tags
    line = re.sub(r'(<(?:p|small|strong)[^>]*>[^<]*)\bcourse\b([^<]*</(?:p|small|strong)>)', r'\1program\2', line)
    line = re.sub(r'(<(?:p|small|strong)[^>]*>[^<]*)\bCourse\b([^<]*</(?:p|small|strong)>)', r'\1Program\2', line)
    
    # CSV column names in help text
    line = re.sub(r'(\bcolumns:[^<]*)\bCourse\b', r'\1Program', line)
    line = re.sub(r'(columns:[^<]*)\bCourse\b', r'\1Program', line)
    
    # JavaScript string messages
    if 'showMessage' in line or 'description =' in line:
        line = re.sub(r'(["\'])([^"\']*)\bCourse\b([^"\']*)\1', r'\1\2Program\3\1', line)
        line = re.sub(r'(["\'])([^"\']*)\bcourse\b([^"\']*)\1', r'\1\2program\3\1', line)
    
    # Emoji label patterns
    line = re.sub(r'(🎓\s+What\s+)course(\s+did you take)', r'\1program\2', line)
    line = re.sub(r'(🎓\s+)Course(\s+Name)', r'\1Program\2', line)
    
    # Landing page text patterns
    line = re.sub(r'(graduation year,\s+)course(,\s+and)', r'\1program\2', line)
    line = re.sub(r'\bcourse(,\s+location,\s+or\s+industry)', r'program\1', line)
    
    # HTML comments (optional - for developer clarity)
    if '<!--' in line and 'Course' in line:
        line = re.sub(r'(<!--[^>]*)\bCourse\b([^>]*-->)', r'\1Program\2', line)
    
    changed = (line != original_line)
    return line, changed

def backup_file(file_path):
    """Create a backup of the file."""
    backup_dir = Path('backups_course_to_program_phase3')
    backup_dir.mkdir(exist_ok=True)
    
    relative_path = file_path.relative_to('.')
    backup_path = backup_dir / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(file_path, backup_path)
    return backup_path

def process_template_file(file_path, dry_run=True):
    """Process a single template file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        return {'error': str(e), 'file': str(file_path)}
    
    new_lines = []
    changes = []
    
    for line_num, line in enumerate(lines, 1):
        new_line, changed = replace_course_in_line(line)
        new_lines.append(new_line)
        
        if changed:
            changes.append({
                'line_num': line_num,
                'old': line.rstrip(),
                'new': new_line.rstrip()
            })
    
    if changes:
        if not dry_run:
            backup_path = backup_file(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        return {
            'file': str(file_path),
            'changes': changes,
            'backup': str(backup_path) if not dry_run else None
        }
    
    return None

def find_and_process_templates(template_dirs, dry_run=True):
    """Find and process all template files."""
    results = []
    
    for template_dir in template_dirs:
        dir_path = Path(template_dir)
        
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob('*.html'):
            result = process_template_file(file_path, dry_run)
            if result:
                results.append(result)
    
    return results

def print_results(results, dry_run=True):
    """Print the results."""
    if not results:
        print("\n✓ No additional changes needed! All user-facing 'Course' text has been replaced.")
        return
    
    mode = "DRY RUN - No files modified" if dry_run else "FILES MODIFIED"
    print(f"\n{'='*80}")
    print(f"{mode}")
    print(f"{'='*80}\n")
    
    total_changes = 0
    
    for result in results:
        if 'error' in result:
            print(f"❌ Error: {result['file']}: {result['error']}")
            continue
        
        print(f"\n📄 {result['file']}")
        print(f"   {len(result['changes'])} change(s)")
        
        if not dry_run and result.get('backup'):
            print(f"   Backup: {result['backup']}")
        
        print("-" * 80)
        
        # Show all changes (they should be few at this point)
        for change in result['changes']:
            print(f"   Line {change['line_num']}:")
            old_preview = change['old'][:120] + '...' if len(change['old']) > 120 else change['old']
            new_preview = change['new'][:120] + '...' if len(change['new']) > 120 else change['new']
            print(f"   - {old_preview}")
            print(f"   + {new_preview}")
            print()
        
        total_changes += len(result['changes'])
    
    print(f"\n{'='*80}")
    print(f"Summary: {total_changes} change(s) in {len(results)} file(s)")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN. No files were modified.")
        print("   Run with --apply to make actual changes.")
    else:
        print("\n✓ Changes applied successfully!")
        print(f"   Backups saved in: backups_course_to_program_phase3/")

if __name__ == '__main__':
    import sys
    
    dry_run = '--apply' not in sys.argv
    
    print("Course to Program Replacement - Phase 3 FINAL")
    print("=" * 80)
    print("Comprehensive scan for ALL remaining user-facing 'Course' text")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE\n")
    else:
        print("\n✓ APPLY MODE\n")
        response = input("Proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    template_dirs = [
        'templates',
        'accounts/templates',
        'cms/templates',
        'donations/templates',
        'jobs/templates',
        'location_tracking/templates',
        'mentorship/templates',
        'setup/templates',
        'surveys/templates',
        'docs/templates',
        'log_viewer/templates'
    ]
    
    print("Scanning all template files...\n")
    results = find_and_process_templates(template_dirs, dry_run)
    print_results(results, dry_run)
