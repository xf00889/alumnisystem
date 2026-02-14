#!/usr/bin/env python3
"""
Phase 2: Replace remaining user-facing 'Course' with 'Program' in templates.
This handles additional cases missed in phase 1.
"""
import os
import re
from pathlib import Path
import shutil
from datetime import datetime

def should_skip_line(line):
    """
    Determine if a line should be completely skipped (no replacements).
    """
    # Skip database field references
    if re.search(r'\{\{.*\.course.*\}\}', line):
        return True
    
    # Skip form field names and IDs
    if re.search(r'(name|id|for)=["\']course["\']', line):
        return True
    
    # Skip URL parameters
    if re.search(r'[&?]course=', line):
        return True
    
    # Skip JavaScript variable declarations
    if re.search(r'(const|let|var)\s+course\s*[=:]', line):
        return True
    
    # Skip CSS class definitions
    if re.search(r'^\s*\.(course-|\.course\s)', line):
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
    
    # Skip object property access
    if re.search(r'\.course\s*[=:]', line):
        return True
    
    return False

def replace_course_in_line(line):
    """
    Replace 'Course' with 'Program' in user-facing text.
    """
    if should_skip_line(line):
        return line, False
    
    original_line = line
    
    # Pattern 1: Label text - <label...>Course</label> or <label...>Course:</label>
    line = re.sub(r'(<label[^>]*>)([^<]*)\bCourse\b([^<]*)(</label>)', 
                  r'\1\2Program\3\4', line)
    
    # Pattern 2: Filter tags - "Course: value"
    line = re.sub(r'(\s+)Course:\s+', r'\1Program: ', line)
    
    # Pattern 3: Placeholder text
    line = re.sub(r'(placeholder=["\'][^"\']*)\bcourse\b([^"\']*["\'])', 
                  r'\1program\2', line)
    
    # Pattern 4: Comments and help text
    line = re.sub(r'(<!--[^>]*)\bcourse\b([^>]*-->)', r'\1program\2', line, flags=re.IGNORECASE)
    line = re.sub(r'(<!--[^>]*)\bCourse\b([^>]*-->)', r'\1Program\2', line)
    
    # Pattern 5: Text in <p>, <small>, <strong> tags
    line = re.sub(r'(<(?:p|small|strong)[^>]*>[^<]*)\bcourse\b([^<]*</(?:p|small|strong)>)', 
                  r'\1program\2', line)
    line = re.sub(r'(<(?:p|small|strong)[^>]*>[^<]*)\bCourse\b([^<]*</(?:p|small|strong)>)', 
                  r'\1Program\2', line)
    
    # Pattern 6: CSV column names in help text
    line = re.sub(r'(\bcolumns:[^<]*)\bCourse\b', r'\1Program', line)
    
    # Pattern 7: JavaScript string messages (but not variable names)
    if 'showMessage' in line or 'description =' in line:
        line = re.sub(r'(["\'])([^"\']*)\bCourse\b([^"\']*)\1', r'\1\2Program\3\1', line)
        line = re.sub(r'(["\'])([^"\']*)\bcourse\b([^"\']*)\1', r'\1\2program\3\1', line)
    
    # Pattern 8: Placeholder for search - "Search courses..."
    line = re.sub(r'(placeholder=["\']Search\s+)courses(\.\.\.["\'])', r'\1programs\2', line)
    
    # Pattern 9: Label emoji patterns
    line = re.sub(r'(🎓\s+What\s+)course(\s+did you take)', r'\1program\2', line)
    line = re.sub(r'(🎓\s+)Course(\s+Name)', r'\1Program\2', line)
    
    changed = (line != original_line)
    return line, changed

def backup_file(file_path):
    """Create a backup of the file before modification."""
    backup_dir = Path('backups_course_to_program_phase2')
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
    template_extensions = ['.html']
    
    for template_dir in template_dirs:
        dir_path = Path(template_dir)
        
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_dir() or file_path.suffix not in template_extensions:
                continue
            
            result = process_template_file(file_path, dry_run)
            if result:
                results.append(result)
    
    return results

def print_results(results, dry_run=True):
    """Print the results."""
    if not results:
        print("\n✓ No additional changes needed!")
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
        
        for change in result['changes'][:5]:  # Show first 5 changes
            print(f"   Line {change['line_num']}:")
            print(f"   - {change['old'][:100]}")
            print(f"   + {change['new'][:100]}")
            print()
        
        if len(result['changes']) > 5:
            print(f"   ... and {len(result['changes']) - 5} more change(s)\n")
        
        total_changes += len(result['changes'])
    
    print(f"\n{'='*80}")
    print(f"Summary: {total_changes} change(s) in {len(results)} file(s)")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN. No files were modified.")
        print("   Run with --apply to make actual changes.")
    else:
        print("\n✓ Changes applied successfully!")
        print(f"   Backups saved in: backups_course_to_program_phase2/")

if __name__ == '__main__':
    import sys
    
    dry_run = '--apply' not in sys.argv
    
    print("Course to Program Replacement - Phase 2")
    print("=" * 80)
    print("Targeting remaining user-facing text instances")
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
    
    results = find_and_process_templates(template_dirs, dry_run)
    print_results(results, dry_run)
