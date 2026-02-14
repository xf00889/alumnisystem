#!/usr/bin/env python3
"""
Script to replace 'Course' with 'Program' in template files.
Only replaces user-facing text, NOT:
- Database field references ({{ alumni.course }})
- Form field names (name="course", id="course")
- URL parameters (&course=)
- JavaScript variables (const course =)
- CSS class names (.course-selected)
"""
import os
import re
from pathlib import Path
import shutil
from datetime import datetime

def should_replace_line(line):
    """
    Determine if a line should have 'Course' replaced with 'Program'.
    Returns True only for user-facing text.
    """
    # Skip if line contains database field references
    if re.search(r'\{\{.*\.course.*\}\}', line):
        return False
    
    # Skip if line contains form field names
    if re.search(r'(name|id|for)=["\']course["\']', line):
        return False
    
    # Skip if line contains URL parameters
    if re.search(r'[&?]course=', line):
        return False
    
    # Skip if line contains JavaScript variable declarations or assignments
    if re.search(r'(const|let|var|\.)\s*course\s*[=:]', line):
        return False
    
    # Skip if line contains CSS class names
    if re.search(r'class=["\'][^"\']*course[^"\']*["\']', line):
        return False
    
    # Skip if line contains data attributes
    if re.search(r'data-[a-z-]*=["\']course["\']', line):
        return False
    
    # Skip if line is a JavaScript comment about course
    if re.search(r'//.*course', line, re.IGNORECASE):
        return False
    
    # Skip if line contains querySelector or getElementById with 'course'
    if re.search(r'(querySelector|getElementById|getElementsByClassName)\(["\'][^"\']*course', line):
        return False
    
    # Skip if line contains append or parameter names in JavaScript
    if re.search(r'(append|params\.)\(["\'].*course', line):
        return False
    
    return True

def replace_course_in_line(line):
    """
    Replace 'Course' with 'Program' in user-facing text only.
    Preserves case (Course -> Program, course -> program).
    """
    if not should_replace_line(line):
        return line, False
    
    original_line = line
    
    # Replace standalone "Course" (capital C) with "Program"
    # Only in user-facing contexts like labels, headers, placeholders
    
    # Simple text replacements in safe contexts
    # Placeholder text
    if 'placeholder=' in line:
        line = re.sub(r'placeholder=(["\'])([^"\']*)\bcourse\b([^"\']*)\1', 
                     lambda m: f'placeholder={m.group(1)}{m.group(2)}program{m.group(3)}{m.group(1)}', line)
    
    # Title and alt attributes
    if 'title=' in line or 'alt=' in line:
        line = re.sub(r'(title|alt)=(["\'])([^"\']*)\bCourse\b([^"\']*)\2', 
                     lambda m: f'{m.group(1)}={m.group(2)}{m.group(3)}Program{m.group(4)}{m.group(2)}', line)
        line = re.sub(r'(title|alt)=(["\'])([^"\']*)\bcourse\b([^"\']*)\2', 
                     lambda m: f'{m.group(1)}={m.group(2)}{m.group(3)}program{m.group(4)}{m.group(2)}', line)
    
    # Additional simple replacements for text content
    # But only if not in excluded contexts
    if '<' in line and '>' in line:
        # Replace in text between tags
        parts = re.split(r'(<[^>]+>)', line)
        for i, part in enumerate(parts):
            if not part.startswith('<'):
                # This is text content, not a tag
                if 'course' in part.lower():
                    # Check if it's in a safe context (not a variable name)
                    if not re.search(r'(const|let|var|function|\.)\s*course', part):
                        part = re.sub(r'\bCourse\b', 'Program', part)
                        part = re.sub(r'\bcourses\b', 'programs', part)
                        part = re.sub(r'\bCourses\b', 'Programs', part)
                        parts[i] = part
        line = ''.join(parts)
    
    # Handle simple cases like "> Course <" or "> Course:"
    line = re.sub(r'>\s*Course\s*<', '> Program <', line)
    line = re.sub(r'>\s*Course:', '> Program:', line)
    line = re.sub(r'>\s*Course\s*\(', '> Program (', line)
    
    changed = (line != original_line)
    return line, changed

def backup_file(file_path):
    """Create a backup of the file before modification."""
    backup_dir = Path('backups_course_to_program')
    backup_dir.mkdir(exist_ok=True)
    
    # Create subdirectory structure in backup
    relative_path = file_path.relative_to('.')
    backup_path = backup_dir / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(file_path, backup_path)
    return backup_path

def process_template_file(file_path, dry_run=True):
    """
    Process a single template file.
    
    Args:
        file_path: Path to the template file
        dry_run: If True, only show what would be changed without modifying files
    
    Returns:
        Dictionary with file statistics
    """
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
            # Backup original file
            backup_path = backup_file(file_path)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        return {
            'file': str(file_path),
            'changes': changes,
            'backup': str(backup_path) if not dry_run else None
        }
    
    return None

def find_and_process_templates(template_dirs, dry_run=True):
    """
    Find and process all template files.
    
    Args:
        template_dirs: List of directories to search
        dry_run: If True, only show what would be changed
    
    Returns:
        List of files with changes
    """
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
    """Print the results of the replacement operation."""
    if not results:
        print("\n✓ No changes needed. All templates are already using 'Program' or don't have user-facing 'Course' text.")
        return
    
    mode = "DRY RUN - No files modified" if dry_run else "FILES MODIFIED"
    print(f"\n{'='*80}")
    print(f"{mode}")
    print(f"{'='*80}\n")
    
    total_changes = 0
    
    for result in results:
        if 'error' in result:
            print(f"❌ Error processing {result['file']}: {result['error']}")
            continue
        
        print(f"\n📄 {result['file']}")
        print(f"   {len(result['changes'])} change(s)")
        
        if not dry_run and result.get('backup'):
            print(f"   Backup: {result['backup']}")
        
        print("-" * 80)
        
        for change in result['changes']:
            print(f"   Line {change['line_num']}:")
            print(f"   - {change['old']}")
            print(f"   + {change['new']}")
            print()
        
        total_changes += len(result['changes'])
    
    print(f"\n{'='*80}")
    print(f"Summary: {total_changes} change(s) in {len(results)} file(s)")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN. No files were modified.")
        print("   Run with --apply to make actual changes.")
    else:
        print("\n✓ Changes applied successfully!")
        print(f"   Backups saved in: backups_course_to_program/")

def save_report(results, dry_run=True):
    """Save detailed report to file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"course_to_program_{'dryrun' if dry_run else 'applied'}_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Course to Program Replacement Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Mode: {'DRY RUN' if dry_run else 'APPLIED'}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        if not results:
            f.write("No changes needed.\n")
            return filename
        
        for result in results:
            if 'error' in result:
                f.write(f"\nError: {result['file']}: {result['error']}\n")
                continue
            
            f.write(f"\nFile: {result['file']}\n")
            f.write(f"Changes: {len(result['changes'])}\n")
            
            if not dry_run and result.get('backup'):
                f.write(f"Backup: {result['backup']}\n")
            
            f.write("-" * 80 + "\n")
            
            for change in result['changes']:
                f.write(f"Line {change['line_num']}:\n")
                f.write(f"OLD: {change['old']}\n")
                f.write(f"NEW: {change['new']}\n\n")
    
    return filename

if __name__ == '__main__':
    import sys
    
    # Check for --apply flag
    dry_run = '--apply' not in sys.argv
    
    print("Course to Program Replacement Script")
    print("=" * 80)
    print("This script replaces 'Course' with 'Program' in template files.")
    print("It ONLY changes user-facing text, NOT:")
    print("  - Database field references ({{ alumni.course }})")
    print("  - Form field names (name='course')")
    print("  - URL parameters (&course=)")
    print("  - JavaScript variables")
    print("  - CSS class names")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified")
        print("   Review the changes, then run with --apply to make actual changes\n")
    else:
        print("\n✓ APPLY MODE - Files will be modified and backed up\n")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
    
    # Template directories to search
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
    
    print("Scanning template files...\n")
    results = find_and_process_templates(template_dirs, dry_run)
    
    print_results(results, dry_run)
    
    # Save report
    report_file = save_report(results, dry_run)
    print(f"\nDetailed report saved to: {report_file}")
