/**
 * User Management JavaScript
 * Handles AJAX interactions for user management features
 * 
 * Uses ToastUtils for all notifications (standardized notification system)
 */

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Toggle user status (enable/disable)
function toggleUserStatus(userId, action) {
    // Show confirmation dialog
    const actionText = action === 'disable' ? 'disable' : 'enable';
    const confirmMessage = `Are you sure you want to ${actionText} this user?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }

    // Get reason for status change
    let reason = '';
    if (action === 'disable') {
        reason = prompt('Please provide a reason for disabling this user:');
        if (reason === null) {
            return; // User cancelled
        }
    }

    // Show loading indicator
    const button = document.querySelector(`button[data-user-id="${userId}"][data-action="${action}"]`);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    // Make AJAX request
    fetch(`/admin-dashboard/users/${userId}/toggle/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            action: action,
            reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastUtils.showSuccess(data.message);
            // Reload page after a short delay
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            ToastUtils.showError(data.message || 'An error occurred');
            if (button) {
                button.disabled = false;
                button.innerHTML = action === 'disable' 
                    ? '<i class="fas fa-ban"></i>' 
                    : '<i class="fas fa-check-circle"></i>';
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ToastUtils.showError('An error occurred while updating user status');
        if (button) {
            button.disabled = false;
            button.innerHTML = action === 'disable' 
                ? '<i class="fas fa-ban"></i>' 
                : '<i class="fas fa-check-circle"></i>';
        }
    });
}

// Manage user roles (assign/remove)
function manageUserRole(userId, role, action, reason = '') {
    // Show loading indicator
    const applyBtn = document.getElementById('applyRoleBtn');
    if (applyBtn) {
        applyBtn.disabled = true;
        applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processing...';
    }

    // Make AJAX request
    fetch(`/admin-dashboard/users/${userId}/roles/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            role: role,
            action: action,
            reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastUtils.showSuccess(data.message);
            // Reload page after a short delay
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            ToastUtils.showError(data.message || 'An error occurred');
            if (applyBtn) {
                applyBtn.disabled = false;
                applyBtn.innerHTML = 'Apply Changes';
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ToastUtils.showError('An error occurred while managing user roles');
        if (applyBtn) {
            applyBtn.disabled = false;
            applyBtn.innerHTML = 'Apply Changes';
        }
    });
}

// Bulk actions
function performBulkAction(action, userIds) {
    if (userIds.length === 0) {
        ToastUtils.showWarning('Please select at least one user');
        return;
    }

    // Show confirmation dialog
    const actionText = action === 'disable' ? 'disable' : 'enable';
    const confirmMessage = `Are you sure you want to ${actionText} ${userIds.length} user(s)?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }

    // Get reason for bulk action
    let reason = '';
    if (action === 'disable') {
        reason = prompt('Please provide a reason for this bulk action:');
        if (reason === null) {
            return; // User cancelled
        }
    }

    // Show loading indicator
    const bulkActionsBar = document.getElementById('bulkActionsBar');
    if (bulkActionsBar) {
        bulkActionsBar.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Processing...</div>';
    }

    // Make AJAX request
    fetch('/admin-dashboard/users/bulk-action/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            action: action,
            user_ids: userIds,
            reason: reason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const successCount = data.results.success.length;
            const failCount = data.results.failed.length;
            
            let message = `Successfully ${actionText}d ${successCount} user(s)`;
            if (failCount > 0) {
                message += `. ${failCount} user(s) failed.`;
            }
            
            if (failCount > 0) {
                ToastUtils.showWarning(message);
            } else {
                ToastUtils.showSuccess(message);
            }
            
            // Reload page after a short delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            ToastUtils.showError(data.message || 'An error occurred');
            // Restore bulk actions bar
            if (bulkActionsBar) {
                window.location.reload();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ToastUtils.showError('An error occurred while performing bulk action');
        // Restore bulk actions bar
        if (bulkActionsBar) {
            window.location.reload();
        }
    });
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Toggle status buttons
    const toggleStatusButtons = document.querySelectorAll('.toggle-status-btn');
    toggleStatusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const action = this.getAttribute('data-action');
            toggleUserStatus(userId, action);
        });
    });

    // Bulk selection functionality
    const selectAllCheckbox = document.getElementById('selectAll');
    const userCheckboxes = document.querySelectorAll('.user-checkbox');
    const bulkActionsBar = document.getElementById('bulkActionsBar');
    const selectedCountSpan = document.getElementById('selectedCount');
    const bulkEnableBtn = document.getElementById('bulkEnableBtn');
    const bulkDisableBtn = document.getElementById('bulkDisableBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');

    // Select all functionality
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            userCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionsBar();
        });
    }

    // Individual checkbox change
    userCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkActionsBar();
            
            // Update select all checkbox state
            if (selectAllCheckbox) {
                const allChecked = Array.from(userCheckboxes).every(cb => cb.checked);
                const someChecked = Array.from(userCheckboxes).some(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = someChecked && !allChecked;
            }
        });
    });

    // Update bulk actions bar visibility and count
    function updateBulkActionsBar() {
        const selectedCheckboxes = document.querySelectorAll('.user-checkbox:checked');
        const count = selectedCheckboxes.length;
        
        if (bulkActionsBar) {
            if (count > 0) {
                bulkActionsBar.classList.add('show');
                if (selectedCountSpan) {
                    selectedCountSpan.textContent = count;
                }
            } else {
                bulkActionsBar.classList.remove('show');
            }
        }
    }

    // Bulk enable button
    if (bulkEnableBtn) {
        bulkEnableBtn.addEventListener('click', function() {
            const selectedCheckboxes = document.querySelectorAll('.user-checkbox:checked');
            const userIds = Array.from(selectedCheckboxes).map(cb => cb.getAttribute('data-user-id'));
            performBulkAction('enable', userIds);
        });
    }

    // Bulk disable button
    if (bulkDisableBtn) {
        bulkDisableBtn.addEventListener('click', function() {
            const selectedCheckboxes = document.querySelectorAll('.user-checkbox:checked');
            const userIds = Array.from(selectedCheckboxes).map(cb => cb.getAttribute('data-user-id'));
            performBulkAction('disable', userIds);
        });
    }

    // Clear selection button
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', function() {
            userCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            }
            updateBulkActionsBar();
        });
    }
});

// Export functions for use in templates
window.toggleUserStatus = toggleUserStatus;
window.manageUserRole = manageUserRole;
window.performBulkAction = performBulkAction;
