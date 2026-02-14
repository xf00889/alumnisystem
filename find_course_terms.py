#!/usr/bin/env python3
"""
Script to find occurrences of 'Course' or 'course' in template files.
"""
import os
import re
from pathlib import Path

def find_course_terms(root_dirs=['templates']):
    """
    Search for 'Course' or 'course' in all template files.
    
    Args:
        root_dirs: List of root directories to search (default: ['templates'])
    """
    results = []
    template_extensions = ['.html', '.txt', '.xml', '.md']
    files_scanned = 0
    files_with_matches = set()
    
    # Ensure root_dirs is a list
    if isinstance(root_dirs, str):
        root_dirs = [root_dirs]
    
    for root_dir in root_dirs:
        # Convert to Path object
        root_path = Path(root_dir)
        
        if not root_path.exists():
            print(f"Warning: Directory '{root_dir}' not found, skipping...")
            continue
        
        print(f"Scanning directory: {root_dir}")
        
        # Walk through all files
        for file_path in root_path.rglob('*'):
            # Skip directories and non-template files
            if file_path.is_dir() or file_path.suffix not in template_extensions:
                continue
            
            files_scanned += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                # Search for 'course' or 'Course' in each line
                for line_num, line in enumerate(lines, 1):
                    if re.search(r'\bcourse\b|\bCourse\b', line, re.IGNORECASE):
                        results.append({
                            'file': str(file_path),
                            'line': line_num,
                            'content': line.strip()
                        })
                        files_with_matches.add(str(file_path))
            
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    print(f"\nScanned {files_scanned} template files")
    print(f"Found matches in {len(files_with_matches)} files")
    
    return results

def print_results(results):
    """Print search results in a readable format."""
    if not results:
        print("No occurrences of 'Course' or 'course' found in template files.")
        return
    
    print(f"\nFound {len(results)} occurrence(s) of 'Course' or 'course' in template files:\n")
    print("=" * 80)
    
    current_file = None
    for result in results:
        if current_file != result['file']:
            current_file = result['file']
            print(f"\n📄 {current_file}")
            print("-" * 80)
        
        print(f"  Line {result['line']}: {result['content']}")
    
    print("\n" + "=" * 80)
    
    # Summary by file
    files = set(r['file'] for r in results)
    print(f"\nSummary: {len(results)} occurrences across {len(files)} file(s)")

def save_results_to_file(results, output_file='course_terms_report.txt'):
    """Save results to a text file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Course/course Terms Search Report\n")
        f.write("=" * 80 + "\n\n")
        
        if not results:
            f.write("No occurrences found.\n")
            return
        
        f.write(f"Found {len(results)} occurrence(s):\n\n")
        
        current_file = None
        for result in results:
            if current_file != result['file']:
                current_file = result['file']
                f.write(f"\nFile: {current_file}\n")
                f.write("-" * 80 + "\n")
            
            f.write(f"  Line {result['line']}: {result['content']}\n")
        
        files = set(r['file'] for r in results)
        f.write(f"\n\nSummary: {len(results)} occurrences across {len(files)} file(s)\n")
    
    print(f"\nResults saved to: {output_file}")

if __name__ == '__main__':
    print("Searching for 'Course' or 'course' in all template directories...")
    print("=" * 80)
    
    # Search in multiple template directories
    template_dirs = [
        'templates',
        'accounts/templates',
        'alumni_directory/templates',
        'alumni_groups/templates',
        'announcements/templates',
        'cms/templates',
        'connections/templates',
        'core/templates',
        'donations/templates',
        'events/templates',
        'feedback/templates',
        'jobs/templates',
        'location_tracking/templates',
        'mentorship/templates',
        'setup/templates',
        'surveys/templates',
        'docs/templates',
        'log_viewer/templates'
    ]
    
    results = find_course_terms(template_dirs)
    
    if results is not None:
        print_results(results)
        save_results_to_file(results)
