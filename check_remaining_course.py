#!/usr/bin/env python3
"""Quick check for remaining 'Course' references in templates."""
import re
from pathlib import Path

def count_course_references():
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
    
    total_count = 0
    user_facing_count = 0
    backend_count = 0
    files_with_course = []
    
    for template_dir in template_dirs:
        dir_path = Path(template_dir)
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob('*.html'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                file_total = 0
                file_user_facing = 0
                file_backend = 0
                
                for line in lines:
                    if re.search(r'\bcourse\b|\bCourse\b', line, re.IGNORECASE):
                        file_total += 1
                        total_count += 1
                        
                        # Check if it's backend (database/form/url/js variable)
                        is_backend = (
                            re.search(r'\{\{.*\.course.*\}\}', line) or
                            re.search(r'(name|id|for)=["\']course["\']', line) or
                            re.search(r'[&?]course=', line) or
                            re.search(r'(const|let|var|\.)\s*course\s*[=:]', line) or
                            re.search(r'class=["\'][^"\']*course[^"\']*["\']', line) or
                            re.search(r'data-[a-z-]*=["\']course["\']', line) or
                            re.search(r'forEach\(\s*course\s*=>', line) or
                            re.search(r'params\.append\(["\'].*course', line)
                        )
                        
                        if is_backend:
                            file_backend += 1
                            backend_count += 1
                        else:
                            file_user_facing += 1
                            user_facing_count += 1
                
                if file_total > 0:
                    files_with_course.append({
                        'file': str(file_path),
                        'total': file_total,
                        'user_facing': file_user_facing,
                        'backend': file_backend
                    })
            
            except Exception as e:
                pass
    
    return {
        'total': total_count,
        'user_facing': user_facing_count,
        'backend': backend_count,
        'files': files_with_course
    }

if __name__ == '__main__':
    print("Checking remaining 'Course' references...")
    print("=" * 80)
    
    results = count_course_references()
    
    print(f"\nTotal 'course' references found: {results['total']}")
    print(f"  - Backend (database/forms/JS): {results['backend']}")
    print(f"  - User-facing text: {results['user_facing']}")
    print(f"\nFiles with references: {len(results['files'])}")
    
    if results['user_facing'] > 0:
        print(f"\n{'='*80}")
        print("Files with user-facing 'Course' text:")
        print(f"{'='*80}")
        for file_info in results['files']:
            if file_info['user_facing'] > 0:
                print(f"\n{file_info['file']}")
                print(f"  User-facing: {file_info['user_facing']}, Backend: {file_info['backend']}")
    else:
        print("\nAll user-facing 'Course' text has been replaced with 'Program'!")
        print("Remaining references are backend code (database fields, form names, etc.)")
