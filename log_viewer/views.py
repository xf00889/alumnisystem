import logging
import os
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
import re
import csv
from collections import defaultdict
from .models import (
    AuditLog, 
    LogRetentionPolicy, 
    LogCleanupSchedule, 
    LogOperationHistory, 
    ArchiveStorageConfig
)
from .services import LogManagementService

logger = logging.getLogger(__name__)

def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@staff_member_required
def log_list(request):
    """
    Display logs in a list view with filtering and search capabilities
    """
    try:
        # Get log directory from settings or use default
        log_dir = Path(settings.BASE_DIR) / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Get log files
        log_files_info = []
        log_file_path = log_dir / 'alumni_system.log'
        error_log_file_path = log_dir / 'errors.log'
        
        # Add available log files
        if log_file_path.exists():
            log_files_info.append({
                'name': 'alumni_system.log',
                'path': str(log_file_path),
                'size': log_file_path.stat().st_size,
                'modified': datetime.fromtimestamp(log_file_path.stat().st_mtime)
            })
        
        if error_log_file_path.exists():
            log_files_info.append({
                'name': 'errors.log',
                'path': str(error_log_file_path),
                'size': error_log_file_path.stat().st_size,
                'modified': datetime.fromtimestamp(error_log_file_path.stat().st_mtime)
            })
        
        # If no log files exist, create default
        if not log_files_info:
            log_files_info.append({
                'name': 'alumni_system.log',
                'path': str(log_file_path),
                'size': 0,
                'modified': datetime.now()
            })
        
        # Get filter parameters
        selected_file = request.GET.get('log_file', 'alumni_system.log')
        log_level = request.GET.get('log_level', '')
        search_query = request.GET.get('search', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        app_filter = request.GET.get('app', '')
        
        # Read and parse log file
        log_entries = []
        current_file_path = log_dir / selected_file
        
        if current_file_path.exists():
            try:
                with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # Parse log entries (assuming format: LEVEL DATE MODULE MESSAGE)
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Parse log entry
                        entry = parse_log_entry(line)
                        if entry:
                            # Apply filters
                            if log_level and entry['level'] != log_level:
                                continue
                            
                            if search_query and search_query.lower() not in entry['message'].lower():
                                continue
                            
                            if date_from:
                                try:
                                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                                    if entry['date'] and entry['date'].date() < date_from_obj:
                                        continue
                                except ValueError:
                                    pass
                            
                            if date_to:
                                try:
                                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                                    if entry['date'] and entry['date'].date() > date_to_obj:
                                        continue
                                except ValueError:
                                    pass
                            
                            if app_filter and app_filter not in entry['module']:
                                continue
                            
                            log_entries.append(entry)
            except Exception as e:
                logger.error(f"Error reading log file: {str(e)}")
        
        # Reverse to show newest first
        log_entries.reverse()
        
        # Get statistics
        total_entries = len(log_entries)
        level_counts = defaultdict(int)
        app_counts = defaultdict(int)
        
        for entry in log_entries:
            level_counts[entry['level']] += 1
            # Extract app name from module
            module_parts = entry['module'].split('.')
            if module_parts:
                app_counts[module_parts[0]] += 1
        
        # Pagination
        paginator = Paginator(log_entries, 50)  # 50 entries per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get available log levels
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Get available apps from all entries (not just filtered)
        all_apps = set()
        if current_file_path.exists():
            try:
                with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        entry = parse_log_entry(line.strip())
                        if entry:
                            module_parts = entry['module'].split('.')
                            if module_parts:
                                all_apps.add(module_parts[0])
            except Exception:
                pass
        
        available_apps = sorted(all_apps) if all_apps else sorted(set(app_counts.keys()))
        
        # Count active filters
        active_filters = sum([
            bool(selected_file != 'alumni_system.log'),
            bool(log_level),
            bool(search_query),
            bool(date_from),
            bool(date_to),
            bool(app_filter)
        ])
        
        context = {
            'log_entries': page_obj,
            'log_files': log_files_info,
            'selected_file': selected_file,
            'log_levels': log_levels,
            'available_apps': available_apps,
            'level_counts': dict(level_counts),
            'app_counts': dict(app_counts),
            'total_entries': total_entries,
            'filters': {
                'log_level': log_level,
                'search': search_query,
                'date_from': date_from,
                'date_to': date_to,
                'app': app_filter,
            },
            'active_filters_count': active_filters,
            'has_active_filters': active_filters > 0,
        }
        
        return render(request, 'log_viewer/log_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in log_list view: {str(e)}", exc_info=True)
        return render(request, 'log_viewer/error.html', {
            'error_message': f'Error loading logs: {str(e)}'
        })

def parse_log_entry(line):
    """
    Parse a log entry line into structured data
    Supports format: LEVEL DATE TIME MODULE MESSAGE
    """
    try:
        # Pattern: LEVEL YYYY-MM-DD HH:MM:SS,mmm MODULE MESSAGE
        pattern = r'(\w+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+(\S+)\s+(.+)'
        match = re.match(pattern, line)
        
        if match:
            level, date_str, time_str, module, message = match.groups()
            
            # Combine date and time
            try:
                datetime_str = f"{date_str} {time_str.split(',')[0]}"
                entry_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                entry_date = None
            
            return {
                'level': level,
                'date': entry_date,
                'module': module,
                'message': message,
                'raw': line
            }
        
        # Fallback: Try to extract level from start
        level_pattern = r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)'
        level_match = re.match(level_pattern, line)
        
        if level_match:
            level = level_match.group(1)
            message = line[len(level):].strip()
            
            return {
                'level': level,
                'date': None,
                'module': 'unknown',
                'message': message,
                'raw': line
            }
        
        # If no pattern matches, return None
        return None
        
    except Exception as e:
        logger.error(f"Error parsing log entry: {str(e)}")
        return None

@staff_member_required
def log_detail(request, log_id):
    """
    Display detailed view of a log entry
    """
    # This would show full details of a log entry
    # For now, redirect to list
    return redirect('log_viewer:log_list')

@staff_member_required
def log_export(request):
    """
    Export filtered logs to CSV
    """
    try:
        import csv
        from django.http import HttpResponse
            
        log_dir = Path(settings.BASE_DIR) / 'logs'
        selected_file = request.GET.get('log_file', 'alumni_system.log')
        current_file_path = log_dir / selected_file
        
        # Get filters (same as log_list)
        log_level = request.GET.get('log_level', '')
        search_query = request.GET.get('search', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        app_filter = request.GET.get('app', '')
        
        # Parse logs with same filters
        log_entries = []
        if current_file_path.exists():
            with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    entry = parse_log_entry(line.strip())
                    if entry:
                        # Apply same filters as in log_list
                        if log_level and entry['level'] != log_level:
                            continue
                        if search_query and search_query.lower() not in entry['message'].lower():
                            continue
                        if date_from and entry['date']:
                            try:
                                if entry['date'].date() < datetime.strptime(date_from, '%Y-%m-%d').date():
                                    continue
                            except ValueError:
                                pass
                        if date_to and entry['date']:
                            try:
                                if entry['date'].date() > datetime.strptime(date_to, '%Y-%m-%d').date():
                                    continue
                            except ValueError:
                                pass
                        if app_filter and app_filter not in entry['module']:
                            continue
                        log_entries.append(entry)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f"logs_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['Level', 'Date', 'Time', 'Module', 'Message'])
        
        for entry in log_entries:
            date_str = entry['date'].strftime('%Y-%m-%d') if entry['date'] else ''
            time_str = entry['date'].strftime('%H:%M:%S') if entry['date'] else ''
            writer.writerow([
                entry['level'],
                date_str,
                time_str,
                entry['module'],
                entry['message']
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting logs: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def logs(request):
    """
    Unified logs page with tabs for Audit Logs and File Logs
    """
    # Get active tab from query parameter
    active_tab = request.GET.get('tab', 'audit')  # Default to audit logs
    
    # Prepare context
    context = {
        'active_tab': active_tab,
    }
    
    # If audit tab is active, get audit log data
    if active_tab == 'audit':
        # Reuse audit_log_list logic
        try:
            # Get filter parameters
            action_filter = request.GET.get('action', '')
            app_filter = request.GET.get('app', '')
            model_filter = request.GET.get('model', '')
            user_filter = request.GET.get('user', '')
            search_query = request.GET.get('search', '').strip()
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            
            # Start with all audit logs
            audit_logs = AuditLog.objects.select_related('user', 'content_type').all()
            
            # Apply filters
            if action_filter:
                audit_logs = audit_logs.filter(action=action_filter)
            if app_filter:
                audit_logs = audit_logs.filter(app_label=app_filter)
            if model_filter:
                audit_logs = audit_logs.filter(model_name=model_filter)
            if user_filter:
                audit_logs = audit_logs.filter(username__icontains=user_filter)
            if search_query:
                audit_logs = audit_logs.filter(
                    Q(message__icontains=search_query) |
                    Q(username__icontains=search_query) |
                    Q(model_name__icontains=search_query) |
                    Q(app_label__icontains=search_query)
                )
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                    audit_logs = audit_logs.filter(timestamp__date__gte=date_from_obj)
                except ValueError:
                    pass
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                    audit_logs = audit_logs.filter(timestamp__date__lte=date_to_obj)
                except ValueError:
                    pass
            
            # Get statistics
            total_count = audit_logs.count()
            action_counts = audit_logs.values('action').annotate(count=Count('id')).order_by('-count')
            app_counts = audit_logs.values('app_label').annotate(count=Count('id')).order_by('-count')
            
            # Pagination
            paginator = Paginator(audit_logs, 50)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Get available filters
            available_actions = AuditLog.objects.values_list('action', flat=True).distinct().order_by('action')
            available_apps = AuditLog.objects.values_list('app_label', flat=True).distinct().order_by('app_label')
            available_models = AuditLog.objects.values_list('model_name', flat=True).distinct().order_by('model_name')
            
            context.update({
                'audit_logs': page_obj,
                'total_count': total_count,
                'action_counts': dict(action_counts),
                'app_counts': dict(app_counts),
                'available_actions': available_actions,
                'available_apps': available_apps,
                'available_models': available_models,
                'filters': {
                    'action': action_filter,
                    'app': app_filter,
                    'model': model_filter,
                    'user': user_filter,
                    'search': search_query,
                    'date_from': date_from,
                    'date_to': date_to,
                },
            })
        except Exception as e:
            logger.error(f"Error loading audit logs: {str(e)}", exc_info=True)
            context['audit_error'] = str(e)
    
    # If file tab is active, get file log data
    elif active_tab == 'file':
        # Reuse log_list logic
        try:
            # Get log directory from settings or use default
            log_dir = Path(settings.BASE_DIR) / 'logs'
            log_dir.mkdir(exist_ok=True)
            
            # Get log files
            log_files_info = []
            log_file_path = log_dir / 'alumni_system.log'
            error_log_file_path = log_dir / 'errors.log'
            
            # Add available log files
            if log_file_path.exists():
                log_files_info.append({
                    'name': 'alumni_system.log',
                    'path': str(log_file_path),
                    'size': log_file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(log_file_path.stat().st_mtime)
                })
            
            if error_log_file_path.exists():
                log_files_info.append({
                    'name': 'errors.log',
                    'path': str(error_log_file_path),
                    'size': error_log_file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(error_log_file_path.stat().st_mtime)
                })
            
            # If no log files exist, create default
            if not log_files_info:
                log_files_info.append({
                    'name': 'alumni_system.log',
                    'path': str(log_file_path),
                    'size': 0,
                    'modified': datetime.now()
                })
            
            # Get filter parameters
            selected_file = request.GET.get('log_file', 'alumni_system.log')
            log_level = request.GET.get('log_level', '')
            search_query = request.GET.get('search', '').strip()
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            app_filter = request.GET.get('app', '')
            
            # Read and parse log file
            log_entries = []
            current_file_path = log_dir / selected_file
            
            if current_file_path.exists():
                try:
                    with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                        # Parse log entries
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            entry = parse_log_entry(line)
                            if entry:
                                # Apply filters
                                if log_level and entry['level'] != log_level:
                                    continue
                                if search_query and search_query.lower() not in entry['message'].lower():
                                    continue
                                if date_from:
                                    try:
                                        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                                        if entry['date'] and entry['date'].date() < date_from_obj:
                                            continue
                                    except ValueError:
                                        pass
                                if date_to:
                                    try:
                                        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                                        if entry['date'] and entry['date'].date() > date_to_obj:
                                            continue
                                    except ValueError:
                                        pass
                                if app_filter and app_filter not in entry['module']:
                                    continue
                                
                                log_entries.append(entry)
                except Exception as e:
                    logger.error(f"Error reading log file: {str(e)}")
            
            # Reverse to show newest first
            log_entries.reverse()
            
            # Get statistics
            total_entries = len(log_entries)
            level_counts = defaultdict(int)
            app_counts = defaultdict(int)
            
            for entry in log_entries:
                level_counts[entry['level']] += 1
                module_parts = entry['module'].split('.')
                if module_parts:
                    app_counts[module_parts[0]] += 1
            
            # Pagination
            paginator = Paginator(log_entries, 50)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Get available log levels
            log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            
            # Get available apps from all entries
            all_apps = set()
            if current_file_path.exists():
                try:
                    with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            entry = parse_log_entry(line.strip())
                            if entry:
                                module_parts = entry['module'].split('.')
                                if module_parts:
                                    all_apps.add(module_parts[0])
                except Exception:
                    pass
            
            available_apps_file = sorted(all_apps) if all_apps else sorted(set(app_counts.keys()))
            
            # Count active filters
            active_filters = sum([
                bool(selected_file != 'alumni_system.log'),
                bool(log_level),
                bool(search_query),
                bool(date_from),
                bool(date_to),
                bool(app_filter)
            ])
            
            context.update({
                'log_entries': page_obj,
                'log_files': log_files_info,
                'selected_file': selected_file,
                'log_levels': log_levels,
                'available_apps_file': available_apps_file,
                'level_counts': dict(level_counts),
                'app_counts': dict(app_counts),
                'total_entries': total_entries,
                'filters': {
                    'log_level': log_level,
                    'search': search_query,
                    'date_from': date_from,
                    'date_to': date_to,
                    'app': app_filter,
                },
                'active_filters_count': active_filters,
                'has_active_filters': active_filters > 0,
            })
        except Exception as e:
            logger.error(f"Error loading file logs: {str(e)}", exc_info=True)
            context['file_error'] = str(e)
    
    return render(request, 'log_viewer/logs.html', context)


@staff_member_required
def audit_log_list(request):
    """
    Display all CRUD operations (audit logs) in a list view with filtering
    """
    try:
        # Get filter parameters
        action_filter = request.GET.get('action', '')
        app_filter = request.GET.get('app', '')
        model_filter = request.GET.get('model', '')
        user_filter = request.GET.get('user', '')
        search_query = request.GET.get('search', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Start with all audit logs
        audit_logs = AuditLog.objects.select_related('user', 'content_type').all()
        
        # Apply filters
        if action_filter:
            audit_logs = audit_logs.filter(action=action_filter)
        
        if app_filter:
            audit_logs = audit_logs.filter(app_label=app_filter)
        
        if model_filter:
            audit_logs = audit_logs.filter(model_name=model_filter)
        
        if user_filter:
            audit_logs = audit_logs.filter(username__icontains=user_filter)
        
        if search_query:
            audit_logs = audit_logs.filter(
                Q(message__icontains=search_query) |
                Q(username__icontains=search_query) |
                Q(model_name__icontains=search_query) |
                Q(app_label__icontains=search_query)
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                audit_logs = audit_logs.filter(timestamp__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                audit_logs = audit_logs.filter(timestamp__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Get statistics
        total_count = audit_logs.count()
        action_counts = audit_logs.values('action').annotate(count=Count('id')).order_by('-count')
        app_counts = audit_logs.values('app_label').annotate(count=Count('id')).order_by('-count')
        model_counts = audit_logs.values('model_name').annotate(count=Count('id')).order_by('-count')[:10]
        
        # Pagination
        paginator = Paginator(audit_logs, 50)  # 50 entries per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get available filters
        available_actions = AuditLog.objects.values_list('action', flat=True).distinct().order_by('action')
        available_apps = AuditLog.objects.values_list('app_label', flat=True).distinct().order_by('app_label')
        available_models = AuditLog.objects.values_list('model_name', flat=True).distinct().order_by('model_name')
        
        # Count active filters
        active_filters = sum([
            bool(action_filter),
            bool(app_filter),
            bool(model_filter),
            bool(user_filter),
            bool(search_query),
            bool(date_from),
            bool(date_to),
        ])
        
        context = {
            'audit_logs': page_obj,
            'total_count': total_count,
            'action_counts': dict(action_counts),
            'app_counts': dict(app_counts),
            'model_counts': dict(model_counts),
            'available_actions': available_actions,
            'available_apps': available_apps,
            'available_models': available_models,
            'filters': {
                'action': action_filter,
                'app': app_filter,
                'model': model_filter,
                'user': user_filter,
                'search': search_query,
                'date_from': date_from,
                'date_to': date_to,
            },
            'active_filters_count': active_filters,
            'has_active_filters': active_filters > 0,
        }
        
        return render(request, 'log_viewer/audit_log_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in audit_log_list view: {str(e)}", exc_info=True)
        return render(request, 'log_viewer/error.html', {
            'error_message': f'Error loading audit logs: {str(e)}'
        })


@staff_member_required
def audit_log_detail(request, log_id):
    """
    Display detailed view of an audit log entry
    """
    try:
        audit_log = get_object_or_404(AuditLog.objects.select_related('user', 'content_type'), id=log_id)
        
        context = {
            'audit_log': audit_log,
        }
        
        return render(request, 'log_viewer/audit_log_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in audit_log_detail view: {str(e)}", exc_info=True)
        return render(request, 'log_viewer/error.html', {
            'error_message': f'Error loading audit log: {str(e)}'
        })


@staff_member_required
def audit_log_export(request):
    """
    Export audit logs to CSV
    """
    try:
        # Get same filters as audit_log_list
        action_filter = request.GET.get('action', '')
        app_filter = request.GET.get('app', '')
        model_filter = request.GET.get('model', '')
        user_filter = request.GET.get('user', '')
        search_query = request.GET.get('search', '').strip()
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Get filtered audit logs
        audit_logs = AuditLog.objects.select_related('user', 'content_type').all()
        
        if action_filter:
            audit_logs = audit_logs.filter(action=action_filter)
        if app_filter:
            audit_logs = audit_logs.filter(app_label=app_filter)
        if model_filter:
            audit_logs = audit_logs.filter(model_name=model_filter)
        if user_filter:
            audit_logs = audit_logs.filter(username__icontains=user_filter)
        if search_query:
            audit_logs = audit_logs.filter(
                Q(message__icontains=search_query) |
                Q(username__icontains=search_query) |
                Q(model_name__icontains=search_query)
            )
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                audit_logs = audit_logs.filter(timestamp__date__gte=date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                audit_logs = audit_logs.filter(timestamp__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f"audit_logs_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'Action', 'App', 'Model', 'Object ID', 
            'Username', 'IP Address', 'Request Path', 'Message'
        ])
        
        for log in audit_logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.action,
                log.app_label,
                log.model_name,
                log.object_id or '',
                log.username or '',
                log.ip_address or '',
                log.request_path or '',
                log.message[:200],  # Limit message length
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting audit logs: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def log_management_dashboard(request):
    """
    Main dashboard for log management configuration and monitoring
    """
    try:
        # Get or create retention policies
        audit_policy, _ = LogRetentionPolicy.objects.get_or_create(
            log_type='audit',
            defaults={
                'retention_days': 90,
                'enabled': False,
                'export_before_delete': True,
                'export_format': 'csv'
            }
        )
        
        file_policy, _ = LogRetentionPolicy.objects.get_or_create(
            log_type='file',
            defaults={
                'retention_days': 30,
                'enabled': False,
                'export_before_delete': True,
                'export_format': 'csv'
            }
        )
        
        # Get or create cleanup schedule
        schedule = LogCleanupSchedule.objects.first()
        
        # Get or create storage config
        storage_config, _ = ArchiveStorageConfig.objects.get_or_create(
            defaults={
                'max_storage_gb': 10.0,
                'warning_threshold_percent': 80,
                'critical_threshold_percent': 95,
                'current_size_gb': 0.0
            }
        )
        
        # Get recent operations (last 10)
        recent_operations = LogOperationHistory.objects.all()[:10]
        
        # Calculate storage usage percentage
        storage_usage_percent = storage_config.usage_percent
        
        # Determine storage status for color coding
        storage_status = storage_config.status
        
        context = {
            'audit_policy': audit_policy,
            'file_policy': file_policy,
            'schedule': schedule,
            'recent_operations': recent_operations,
            'storage_config': storage_config,
            'storage_usage_percent': storage_usage_percent,
            'storage_status': storage_status,
        }
        
        return render(request, 'log_viewer/management_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in log_management_dashboard view: {str(e)}", exc_info=True)
        return render(request, 'log_viewer/error.html', {
            'error_message': f'Error loading log management dashboard: {str(e)}'
        })


@staff_member_required
@staff_member_required
@require_POST
def manual_cleanup_trigger(request):
    """
    Manually trigger log cleanup operation.
    
    This endpoint allows staff members to trigger a manual cleanup operation
    outside of the scheduled times. The operation will apply the same retention
    policies as scheduled cleanup.
    
    Returns:
        JsonResponse with success status, message, and operation metrics
    """
    try:
        logger.info(f"Manual cleanup triggered by user: {request.user.username}")
        
        # Instantiate the log management service
        service = LogManagementService()
        
        # Execute cleanup with manual operation type
        operation = service.execute_cleanup(
            triggered_by=request.user,
            operation_type='manual'
        )
        
        # Prepare response based on operation status
        if operation.status == 'success':
            message = f'Cleanup completed successfully. Processed {operation.total_processed} log entries, deleted {operation.total_deleted}, created {operation.archives_created} archives.'
            return JsonResponse({
                'success': True,
                'message': message,
                'operation_id': operation.id,
                'metrics': {
                    'total_processed': operation.total_processed,
                    'total_deleted': operation.total_deleted,
                    'archives_created': operation.archives_created,
                    'audit_logs_processed': operation.audit_logs_processed,
                    'audit_logs_deleted': operation.audit_logs_deleted,
                    'file_logs_processed': operation.file_logs_processed,
                    'file_logs_deleted': operation.file_logs_deleted,
                }
            })
        elif operation.status == 'partial':
            message = f'Cleanup completed with warnings. Processed {operation.total_processed} log entries, deleted {operation.total_deleted}. Some operations may have failed.'
            return JsonResponse({
                'success': True,
                'message': message,
                'operation_id': operation.id,
                'warning': True,
                'metrics': {
                    'total_processed': operation.total_processed,
                    'total_deleted': operation.total_deleted,
                    'archives_created': operation.archives_created,
                }
            })
        else:
            # Failed status
            error_msg = operation.error_message or 'Unknown error occurred during cleanup'
            return JsonResponse({
                'success': False,
                'message': f'Cleanup failed: {error_msg}',
                'operation_id': operation.id,
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in manual_cleanup_trigger: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error triggering cleanup: {str(e)}'
        }, status=500)


@staff_member_required
def unified_dashboard(request):
    """
    Unified log management dashboard with inline editing capabilities
    """
    try:
        # Get or create retention policies
        audit_policy, _ = LogRetentionPolicy.objects.get_or_create(
            log_type='audit',
            defaults={
                'retention_days': 90,
                'enabled': False,
                'export_before_delete': True,
                'export_format': 'csv',
                'archive_path': 'logs/archives/audit'
            }
        )
        
        file_policy, _ = LogRetentionPolicy.objects.get_or_create(
            log_type='file',
            defaults={
                'retention_days': 30,
                'enabled': False,
                'export_before_delete': True,
                'export_format': 'csv',
                'archive_path': 'logs/archives/file'
            }
        )
        
        # Get or create cleanup schedule
        schedule = LogCleanupSchedule.objects.first()
        
        # Get or create storage config
        storage_config, _ = ArchiveStorageConfig.objects.get_or_create(
            defaults={
                'max_storage_gb': 10.0,
                'warning_threshold_percent': 80,
                'critical_threshold_percent': 95,
                'current_size_gb': 0.0
            }
        )
        
        # Calculate storage usage percentage
        storage_usage_percent = storage_config.usage_percent
        
        # Determine storage status for color coding
        storage_status = storage_config.status
        
        context = {
            'audit_policy': audit_policy,
            'file_policy': file_policy,
            'schedule': schedule,
            'storage_config': storage_config,
            'storage_usage_percent': storage_usage_percent,
            'storage_status': storage_status,
        }
        
        return render(request, 'log_viewer/unified_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in unified_dashboard view: {str(e)}", exc_info=True)
        return render(request, 'log_viewer/error.html', {
            'error_message': f'Error loading unified dashboard: {str(e)}'
        })


@staff_member_required
@require_POST
def save_retention_policy(request):
    """
    Save retention policy configuration via AJAX
    """
    try:
        import json
        data = json.loads(request.body)
        
        log_type = data.get('log_type')
        if log_type not in ['audit', 'file']:
            return JsonResponse({
                'success': False,
                'message': 'Invalid log type'
            }, status=400)
        
        # Get or create the policy
        policy, created = LogRetentionPolicy.objects.get_or_create(
            log_type=log_type,
            defaults={
                'retention_days': 90 if log_type == 'audit' else 30,
                'enabled': False,
                'export_before_delete': True,
                'export_format': 'csv'
            }
        )
        
        # Validate retention days
        retention_days = int(data.get('retention_days', policy.retention_days))
        if retention_days < 1 or retention_days > 3650:
            return JsonResponse({
                'success': False,
                'message': 'Retention days must be between 1 and 3650'
            }, status=400)
        
        # Update policy fields
        policy.enabled = data.get('enabled', policy.enabled)
        policy.retention_days = retention_days
        policy.export_format = data.get('export_format', policy.export_format)
        policy.archive_path = data.get('archive_path', policy.archive_path)
        policy.export_before_delete = data.get('export_before_delete', policy.export_before_delete)
        
        policy.save()
        
        logger.info(f"Retention policy for {log_type} logs updated by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'{log_type.capitalize()} log retention policy saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving retention policy: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@staff_member_required
@require_POST
def save_cleanup_schedule(request):
    """
    Save cleanup schedule configuration via AJAX
    """
    try:
        import json
        from datetime import time as dt_time
        
        data = json.loads(request.body)
        
        # Get or create schedule
        schedule = LogCleanupSchedule.objects.first()
        if not schedule:
            schedule = LogCleanupSchedule.objects.create(
                enabled=False,
                frequency='daily',
                execution_time=dt_time(2, 0)
            )
        
        # Update schedule fields
        schedule.enabled = data.get('enabled', schedule.enabled)
        schedule.frequency = data.get('frequency', schedule.frequency)
        
        # Parse execution time
        execution_time_str = data.get('execution_time')
        if execution_time_str:
            hour, minute = map(int, execution_time_str.split(':'))
            schedule.execution_time = dt_time(hour, minute)
        
        # Handle conditional fields
        if schedule.frequency == 'weekly':
            schedule.day_of_week = data.get('day_of_week')
            schedule.day_of_month = None
        elif schedule.frequency == 'monthly':
            day_of_month = data.get('day_of_month')
            if day_of_month:
                day_of_month = int(day_of_month)
                if day_of_month < 1 or day_of_month > 28:
                    return JsonResponse({
                        'success': False,
                        'message': 'Day of month must be between 1 and 28'
                    }, status=400)
                schedule.day_of_month = day_of_month
            schedule.day_of_week = None
        else:  # daily
            schedule.day_of_week = None
            schedule.day_of_month = None
        
        # Calculate next run time
        service = LogManagementService()
        next_run = service.calculate_next_run_time(schedule)
        
        # Handle timezone awareness based on USE_TZ setting
        if next_run:
            if settings.USE_TZ:
                # Ensure timezone aware
                if timezone.is_naive(next_run):
                    schedule.next_run = timezone.make_aware(next_run)
                else:
                    schedule.next_run = next_run
            else:
                # Ensure timezone naive
                if timezone.is_aware(next_run):
                    schedule.next_run = timezone.make_naive(next_run)
                else:
                    schedule.next_run = next_run
        else:
            schedule.next_run = next_run
        
        schedule.save()
        
        logger.info(f"Cleanup schedule updated by {request.user.username}")
        
        # Format next run time for response
        next_run_formatted = schedule.next_run.strftime('%B %d, %Y at %I:%M %p') if schedule.next_run else None
        
        return JsonResponse({
            'success': True,
            'message': 'Cleanup schedule saved successfully',
            'next_run': next_run_formatted
        })
        
    except Exception as e:
        logger.error(f"Error saving cleanup schedule: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@staff_member_required
@require_POST
def save_storage_config(request):
    """
    Save archive storage configuration via AJAX
    """
    try:
        import json
        from decimal import Decimal
        
        data = json.loads(request.body)
        
        # Get or create storage config
        storage_config, created = ArchiveStorageConfig.objects.get_or_create(
            defaults={
                'max_storage_gb': 10.0,
                'warning_threshold_percent': 80,
                'critical_threshold_percent': 95,
                'current_size_gb': 0.0
            }
        )
        
        # Validate thresholds
        warning_threshold = int(data.get('warning_threshold_percent', storage_config.warning_threshold_percent))
        critical_threshold = int(data.get('critical_threshold_percent', storage_config.critical_threshold_percent))
        
        if warning_threshold < 1 or warning_threshold > 100:
            return JsonResponse({
                'success': False,
                'message': 'Warning threshold must be between 1 and 100'
            }, status=400)
        
        if critical_threshold < 1 or critical_threshold > 100:
            return JsonResponse({
                'success': False,
                'message': 'Critical threshold must be between 1 and 100'
            }, status=400)
        
        if critical_threshold <= warning_threshold:
            return JsonResponse({
                'success': False,
                'message': 'Critical threshold must be greater than warning threshold'
            }, status=400)
        
        # Update storage config
        storage_config.max_storage_gb = Decimal(str(data.get('max_storage_gb', storage_config.max_storage_gb)))
        storage_config.warning_threshold_percent = warning_threshold
        storage_config.critical_threshold_percent = critical_threshold
        
        storage_config.save()
        
        logger.info(f"Storage configuration updated by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Storage configuration saved successfully',
            'storage_usage_percent': float(storage_config.usage_percent),
            'current_size_gb': float(storage_config.current_size_gb),
            'max_storage_gb': float(storage_config.max_storage_gb),
            'status': storage_config.status
        })
        
    except Exception as e:
        logger.error(f"Error saving storage config: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@staff_member_required
@require_POST
def recalculate_storage(request):
    """
    Recalculate archive storage size via AJAX
    """
    try:
        # Get storage config
        storage_config = ArchiveStorageConfig.objects.first()
        if not storage_config:
            return JsonResponse({
                'success': False,
                'message': 'Storage configuration not found'
            }, status=404)
        
        # Recalculate storage size
        service = LogManagementService()
        service.check_storage_limits()
        
        # Refresh from database
        storage_config.refresh_from_db()
        
        logger.info(f"Storage size recalculated by {request.user.username}: {storage_config.current_size_gb} GB")
        
        return JsonResponse({
            'success': True,
            'message': 'Storage size recalculated successfully',
            'current_size_gb': float(storage_config.current_size_gb),
            'max_storage_gb': float(storage_config.max_storage_gb),
            'storage_usage_percent': float(storage_config.usage_percent),
            'status': storage_config.status
        })
        
    except Exception as e:
        logger.error(f"Error recalculating storage: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@staff_member_required
def filter_operations(request):
    """
    Filter and paginate operation history via AJAX
    """
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        operation_type_filter = request.GET.get('operation_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        page = int(request.GET.get('page', 1))
        per_page = 50
        
        # Start with all operations
        operations = LogOperationHistory.objects.all()
        
        # Apply filters
        if status_filter:
            operations = operations.filter(status=status_filter)
        
        if operation_type_filter:
            operations = operations.filter(operation_type=operation_type_filter)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                operations = operations.filter(started_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                operations = operations.filter(started_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Order by most recent first
        operations = operations.order_by('-started_at')
        
        # Get total count
        total_count = operations.count()
        
        # Paginate
        paginator = Paginator(operations, per_page)
        page_obj = paginator.get_page(page)
        
        # Serialize operations
        operations_data = []
        for op in page_obj:
            operations_data.append({
                'id': op.id,
                'started_at': op.started_at.strftime('%b %d, %Y %I:%M %p'),
                'operation_type': op.get_operation_type_display(),
                'status': op.status,
                'status_display': op.get_status_display(),
                'total_processed': op.total_processed,
                'total_deleted': op.total_deleted,
                'archives_created': op.archives_created,
                'triggered_by': op.triggered_by.username if op.triggered_by else None
            })
        
        return JsonResponse({
            'success': True,
            'operations': operations_data,
            'page': page,
            'total_pages': paginator.num_pages,
            'total_count': total_count
        })
        
    except Exception as e:
        logger.error(f"Error filtering operations: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@staff_member_required
def operation_detail(request, operation_id):
    """
    Get detailed information about a specific operation via AJAX
    """
    try:
        operation = get_object_or_404(LogOperationHistory, id=operation_id)
        
        data = {
            'success': True,
            'operation': {
                'id': operation.id,
                'operation_type': operation.operation_type,
                'operation_type_display': operation.get_operation_type_display(),
                'status': operation.status,
                'status_display': operation.get_status_display(),
                'started_at': operation.started_at.strftime('%B %d, %Y at %I:%M %p'),
                'completed_at': operation.completed_at.strftime('%B %d, %Y at %I:%M %p') if operation.completed_at else None,
                'audit_logs_processed': operation.audit_logs_processed,
                'audit_logs_deleted': operation.audit_logs_deleted,
                'file_logs_processed': operation.file_logs_processed,
                'file_logs_deleted': operation.file_logs_deleted,
                'archives_created': operation.archives_created,
                'error_message': operation.error_message,
                'archive_files': operation.archive_files,
                'triggered_by': operation.triggered_by.username if operation.triggered_by else None
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error getting operation detail: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@staff_member_required
def export_operations(request):
    """
    Export operation history to CSV
    """
    try:
        # Get filter parameters (same as filter_operations)
        status_filter = request.GET.get('status', '')
        operation_type_filter = request.GET.get('operation_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Start with all operations
        operations = LogOperationHistory.objects.all()
        
        # Apply filters
        if status_filter:
            operations = operations.filter(status=status_filter)
        
        if operation_type_filter:
            operations = operations.filter(operation_type=operation_type_filter)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                operations = operations.filter(started_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                operations = operations.filter(started_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        # Order by most recent first
        operations = operations.order_by('-started_at')
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f"operation_history_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Started At', 'Completed At', 'Operation Type', 'Status',
            'Audit Logs Processed', 'Audit Logs Deleted',
            'File Logs Processed', 'File Logs Deleted',
            'Archives Created', 'Triggered By', 'Error Message'
        ])
        
        for op in operations:
            writer.writerow([
                op.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                op.completed_at.strftime('%Y-%m-%d %H:%M:%S') if op.completed_at else '',
                op.get_operation_type_display(),
                op.get_status_display(),
                op.audit_logs_processed,
                op.audit_logs_deleted,
                op.file_logs_processed,
                op.file_logs_deleted,
                op.archives_created,
                op.triggered_by.username if op.triggered_by else 'System',
                op.error_message[:200] if op.error_message else ''
            ])
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting operations: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
