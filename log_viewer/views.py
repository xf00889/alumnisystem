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
from datetime import datetime, timedelta
import re
import csv
from collections import defaultdict
from .models import AuditLog

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
def log_clear(request):
    """
    Clear log file (admin only)
    """
    if request.method == 'POST':
        try:
            log_file = request.POST.get('log_file')
            log_dir = Path(settings.BASE_DIR) / 'logs'
            file_path = log_dir / log_file
            
            if file_path.exists():
                # Backup old log
                backup_path = file_path.with_suffix(f'.{timezone.now().strftime("%Y%m%d_%H%M%S")}.bak')
                file_path.rename(backup_path)
                
                # Create new empty file
                file_path.touch()
                
                return JsonResponse({'success': True, 'message': 'Log file cleared successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Log file not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Error clearing log file: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


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
