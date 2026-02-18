// NORSU Alumni System - Notification Management JavaScript

// Note: csrftoken is already declared globally in base.html

class NotificationManager {
    constructor() {
        this.notificationCount = 0;
        this.notifications = [];
        this.isDropdownOpen = false;
        this.pollInterval = null;
        this.pollFrequency = 30000; // 30 seconds
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadNotifications();
        this.startPolling();
    }
    
    bindEvents() {
        // Notification dropdown toggle
        const notificationDropdown = document.getElementById('notificationDropdown');
        if (notificationDropdown) {
            notificationDropdown.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDropdown();
            });
        }
        
        // Mark all as read button
        const markAllReadBtn = document.getElementById('mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.markAllAsRead();
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.querySelector('.notification-dropdown');
            if (dropdown && !dropdown.contains(e.target)) {
                this.closeDropdown();
            }
        });
        
        // Handle dropdown shown/hidden events
        const dropdownElement = document.querySelector('.notification-dropdown .dropdown-menu');
        if (dropdownElement) {
            dropdownElement.addEventListener('shown.bs.dropdown', () => {
                this.isDropdownOpen = true;
                this.loadNotifications();
            });
            
            dropdownElement.addEventListener('hidden.bs.dropdown', () => {
                this.isDropdownOpen = false;
            });
        }
    }
    
    async loadNotifications(limit = 10, offset = 0) {
        try {
            const response = await fetch(`/api/notifications/?limit=${limit}&offset=${offset}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.notifications = data.notifications;
                this.notificationCount = data.unread_count;
                this.updateUI();
            } else {
                console.error('Failed to load notifications:', data.error);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.notificationCount = data.unread_count;
                this.updateBadge();
                
                // Update the notification in the list
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification) {
                    notification.is_read = true;
                }
                this.renderNotifications();
            } else {
                console.error('Failed to mark notification as read:', data.error);
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.notificationCount = 0;
                this.notifications.forEach(n => n.is_read = true);
                this.updateUI();
                ToastUtils.showSuccess('All notifications marked as read');
            } else {
                console.error('Failed to mark all notifications as read:', data.error);
                ToastUtils.showError('Failed to mark notifications as read');
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            ToastUtils.showError('Error marking notifications as read');
        }
    }
    
    async getUnreadCount() {
        try {
            const response = await fetch('/api/notifications/unread-count/', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.notificationCount = data.unread_count;
                this.updateBadge();
            }
        } catch (error) {
            console.error('Error getting unread count:', error);
        }
    }
    
    updateUI() {
        this.updateBadge();
        this.renderNotifications();
    }
    
    updateBadge() {
        const badge = document.getElementById('notification-count');
        if (badge) {
            if (this.notificationCount > 0) {
                badge.textContent = this.notificationCount > 99 ? '99+' : this.notificationCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    renderNotifications() {
        const notificationList = document.getElementById('notification-list');
        const noNotifications = document.getElementById('no-notifications');
        
        if (!notificationList) return;
        
        if (this.notifications.length === 0) {
            notificationList.innerHTML = '';
            if (noNotifications) {
                noNotifications.style.display = 'block';
            }
            return;
        }
        
        if (noNotifications) {
            noNotifications.style.display = 'none';
        }
        
        const notificationsHTML = this.notifications.map(notification => {
            const timeAgo = this.getTimeAgo(new Date(notification.created_at));
            const readClass = notification.is_read ? '' : 'notification-unread';
            const avatar = notification.sender?.avatar || '/static/images/default-avatar.png';
            
            return `
                <div class="notification-item ${readClass}" data-notification-id="${notification.id}">
                    <div class="d-flex align-items-start p-3 border-bottom notification-content" 
                         ${notification.action_url ? `style="cursor: pointer;" data-url="${notification.action_url}"` : ''}>
                        <div class="notification-avatar me-3">
                            <img src="${avatar}" alt="Avatar" class="rounded-circle" 
                                 style="width: 40px; height: 40px; object-fit: cover;"
                                 onerror="this.src='/static/images/default-avatar.png'">
                        </div>
                        <div class="notification-body flex-grow-1">
                            <div class="notification-title fw-semibold">${notification.title}</div>
                            <div class="notification-message text-muted small">${notification.message}</div>
                            <div class="notification-time text-muted small mt-1">
                                <i class="fas fa-clock me-1"></i>${timeAgo}
                            </div>
                        </div>
                        ${!notification.is_read ? '<div class="notification-dot bg-primary rounded-circle" style="width: 8px; height: 8px; margin-top: 6px;"></div>' : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        notificationList.innerHTML = notificationsHTML;
        
        // Bind click events for notifications
        this.bindNotificationEvents();
    }

    bindNotificationEvents() {
        const notificationItems = document.querySelectorAll('.notification-content');
        notificationItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const notificationId = parseInt(item.closest('.notification-item').dataset.notificationId);
                const url = item.dataset.url;

                // Mark as read if unread
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification && !notification.is_read) {
                    this.markAsRead(notificationId);
                }

                // Navigate to action URL if available
                if (url) {
                    window.location.href = url;
                }
            });
        });
    }

    toggleDropdown() {
        const dropdown = document.querySelector('.notification-dropdown .dropdown-menu');
        if (dropdown) {
            const bsDropdown = new bootstrap.Dropdown(document.getElementById('notificationDropdown'));
            if (this.isDropdownOpen) {
                bsDropdown.hide();
            } else {
                bsDropdown.show();
            }
        }
    }

    closeDropdown() {
        const dropdown = document.querySelector('.notification-dropdown .dropdown-menu');
        if (dropdown && this.isDropdownOpen) {
            const bsDropdown = new bootstrap.Dropdown(document.getElementById('notificationDropdown'));
            bsDropdown.hide();
        }
    }

    startPolling() {
        // Poll for new notifications every 30 seconds
        this.pollInterval = setInterval(() => {
            if (!this.isDropdownOpen) {
                this.getUnreadCount();
            }
        }, this.pollFrequency);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 604800) {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    destroy() {
        this.stopPolling();
    }
}

// Initialize notification manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof csrftoken !== 'undefined') {
        window.notificationManager = new NotificationManager();
    }
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', function() {
    if (window.notificationManager) {
        window.notificationManager.destroy();
    }
});
