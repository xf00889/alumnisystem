"""
Management command to verify all Python imports are listed in requirements.txt

This command scans all Python files in the project, extracts import statements,
and compares them against the packages listed in requirements.txt to identify
any missing dependencies.
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.conf import settings


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements from Python files"""
    
    def __init__(self):
        self.imports = set()
    
    def visit_Import(self, node):
        """Handle 'import module' statements"""
        for alias in node.names:
            # Get the top-level package name
            package = alias.name.split('.')[0]
            self.imports.add(package)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Handle 'from module import ...' statements"""
        if node.module:
            # Get the top-level package name
            package = node.module.split('.')[0]
            self.imports.add(package)
        self.generic_visit(node)


class Command(BaseCommand):
    help = 'Verify all Python imports are listed in requirements.txt'
    
    # Standard library modules that don't need to be in requirements.txt
    STDLIB_MODULES = {
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'concurrent',
        'contextlib', 'copy', 'csv', 'datetime', 'decimal', 'email', 'enum',
        'functools', 'hashlib', 'hmac', 'html', 'http', 'importlib', 'io', 'itertools',
        'json', 'logging', 'math', 'mimetypes', 'os', 'pathlib', 'pickle', 'platform',
        'pprint', 'random', 're', 'secrets', 'shutil', 'signal', 'socket', 'sqlite3',
        'ssl', 'string', 'struct', 'subprocess', 'sys', 'tempfile', 'textwrap',
        'threading', 'time', 'traceback', 'typing', 'unittest', 'urllib', 'uuid',
        'warnings', 'weakref', 'xml', 'zipfile', 'zoneinfo', 'smtplib', 'getpass',
        'dataclasses', 'operator', 'heapq', 'bisect', 'array', 'queue', 'sched',
    }
    
    # Django apps and local modules that don't need to be in requirements.txt
    LOCAL_MODULES = {
        'accounts', 'alumni_directory', 'alumni_groups', 'alumni_web', 'announcements',
        'cms', 'connections', 'core', 'data_consolidation', 'docs', 'donations',
        'events', 'feedback', 'groups', 'jobs', 'location_tracking', 'log_viewer',
        'mentorship', 'norsu_alumni', 'setup', 'surveys',
        # Common local module names that are relative imports
        'utils', 'models', 'forms', 'views', 'serializers', 'middleware', 'signals',
        'admin', 'urls', 'apps', 'tests', 'management', 'migrations', 'templatetags',
        'context_processors', 'decorators', 'mixins', 'validators', 'widgets',
        'backends', 'adapters', 'handlers', 'services', 'tasks', 'constants',
        'exceptions', 'permissions', 'filters', 'pagination', 'authentication',
        # App-specific modules
        'email_utils', 'email_provider', 'brevo_email', 'sendgrid_email', 
        'render_email_fallback', 'brevo_config', 'smtp_config', 'smtp_settings',
        'recaptcha_fields', 'recaptcha_widgets', 'recaptcha_utils', 'recaptcha_monitoring',
        'recaptcha_config', 'markdown_processor', 'navigation', 'export_utils',
        'fraud_detection', 'scraper_utils', 'scraper_forms', 'forms_gcash',
        'messaging_forms', 'messaging_models', 'messaging_views', 'view_handlers',
        'security', 'analytics', 'contact', 'content',
    }
    
    # Package name mappings (import name -> requirements.txt name)
    PACKAGE_MAPPINGS = {
        'PIL': 'pillow',
        'MySQLdb': 'mysqlclient',
        'psycopg2': 'psycopg2-binary',
        'yaml': 'PyYAML',
        'dateutil': 'python-dateutil',
        'slugify': 'python-slugify',
        'openid': 'python3-openid',
        'decouple': 'python-decouple',
        'jwt': 'PyJWT',
        'OpenSSL': 'pyOpenSSL',
        'bs4': 'beautifulsoup4',
        'rest_framework': 'djangorestframework',
        'phonenumber_field': 'django-phonenumber-field',
        'phonenumbers': 'phonenumbers',
        'taggit': 'django-taggit',
        'widget_tweaks': 'django-widget-tweaks',
        'crispy_forms': 'django-crispy-forms',
        'crispy_bootstrap5': 'crispy-bootstrap5',
        'allauth': 'django-allauth',
        'ckeditor': 'django-ckeditor',
        'cleanup': 'django-cleanup',
        'corsheaders': 'django-cors-headers',
        'django_countries': 'django-countries',
        'django_extensions': 'django-extensions',
        'django_filters': 'django-filter',
        'model_utils': 'django-model-utils',
        'notifications': 'django-notifications-hq',
        'django_htmx': 'django-htmx',
        'captcha': 'django-recaptcha',
        'django_ratelimit': 'django-ratelimit',
        'django_recaptcha': 'django-recaptcha',
        'csp': 'django-csp',
        'dj_database_url': 'dj-database-url',
        'django_q': 'django-q',
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about all imports',
        )
        parser.add_argument(
            '--exclude-tests',
            action='store_true',
            help='Exclude test files from scanning',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        exclude_tests = options['exclude_tests']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Dependency Verification Report'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        
        # Get project root
        project_root = Path(settings.BASE_DIR)
        
        # Scan all Python files
        self.stdout.write('Scanning Python files...')
        all_imports = self.scan_python_files(project_root, exclude_tests)
        
        # Load requirements.txt
        self.stdout.write('Loading requirements.txt...')
        requirements = self.load_requirements(project_root / 'requirements.txt')
        
        # Filter imports
        third_party_imports = self.filter_imports(all_imports)
        
        # Compare
        missing_deps = self.find_missing_dependencies(third_party_imports, requirements)
        
        # Report results
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('-' * 70))
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write(self.style.SUCCESS('-' * 70))
        self.stdout.write(f'Total imports found: {len(all_imports)}')
        self.stdout.write(f'Third-party imports: {len(third_party_imports)}')
        self.stdout.write(f'Requirements listed: {len(requirements)}')
        self.stdout.write('')
        
        if missing_deps:
            self.stdout.write(self.style.ERROR(f'Missing dependencies: {len(missing_deps)}'))
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('The following packages are imported but not in requirements.txt:'))
            for dep in sorted(missing_deps):
                self.stdout.write(self.style.ERROR(f'  - {dep}'))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Action required: Add these packages to requirements.txt'))
        else:
            self.stdout.write(self.style.SUCCESS('[OK] All dependencies are listed in requirements.txt'))
        
        if verbose:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('-' * 70))
            self.stdout.write(self.style.SUCCESS('All Third-Party Imports'))
            self.stdout.write(self.style.SUCCESS('-' * 70))
            for imp in sorted(third_party_imports):
                mapped = self.map_import_to_package(imp)
                if mapped in requirements:
                    self.stdout.write(f'  [OK] {imp} -> {mapped}')
                else:
                    self.stdout.write(self.style.ERROR(f'  [MISSING] {imp} -> {mapped}'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
    
    def scan_python_files(self, root_path, exclude_tests=False):
        """Scan all Python files and extract imports"""
        imports = set()
        file_count = 0
        
        for py_file in root_path.rglob('*.py'):
            # Skip virtual environments and migrations
            if any(part in py_file.parts for part in ['venv', 'env', '.venv', 'migrations', '__pycache__']):
                continue
            
            # Skip test files if requested
            if exclude_tests and ('test' in py_file.name or 'tests' in py_file.parts):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the file and extract imports
                tree = ast.parse(content, filename=str(py_file))
                visitor = ImportVisitor()
                visitor.visit(tree)
                imports.update(visitor.imports)
                file_count += 1
                
            except (SyntaxError, UnicodeDecodeError) as e:
                # Skip files that can't be parsed
                pass
        
        self.stdout.write(f'Scanned {file_count} Python files')
        return imports
    
    def load_requirements(self, requirements_path):
        """Load and parse requirements.txt"""
        requirements = set()
        
        if not requirements_path.exists():
            self.stdout.write(self.style.ERROR(f'requirements.txt not found at {requirements_path}'))
            return requirements
        
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Extract package name (before ==, >=, etc.)
                match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                if match:
                    package = match.group(1).lower()
                    requirements.add(package)
        
        return requirements
    
    def filter_imports(self, all_imports):
        """Filter out standard library and local modules"""
        third_party = set()
        
        for imp in all_imports:
            # Skip standard library
            if imp in self.STDLIB_MODULES:
                continue
            
            # Skip local modules
            if imp in self.LOCAL_MODULES:
                continue
            
            third_party.add(imp)
        
        return third_party
    
    def map_import_to_package(self, import_name):
        """Map import name to requirements.txt package name"""
        # Check if there's a known mapping
        if import_name in self.PACKAGE_MAPPINGS:
            return self.PACKAGE_MAPPINGS[import_name].lower()
        
        # Otherwise, use the import name as-is
        return import_name.lower()
    
    def find_missing_dependencies(self, imports, requirements):
        """Find imports that are not in requirements.txt"""
        missing = set()
        
        for imp in imports:
            package = self.map_import_to_package(imp)
            
            # Check if package is in requirements
            if package not in requirements:
                missing.add(imp)
        
        return missing
