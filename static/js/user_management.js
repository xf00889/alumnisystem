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

// Single and bulk status updates use the same accessible confirmation modal.
const statusDialog = { action: null, userIds: [], button: null };
function userManagementError(message) {
    if (window.ToastUtils && typeof ToastUtils.showError === 'function') {
        ToastUtils.showError(message);
    } else {
        const area = document.getElementById('statusChangeError');
        if (area) { area.textContent = message; area.hidden = false; }
        console.error('User Management:', message);
    }
}
function userManagementSuccess(message) {
    if (window.ToastUtils && typeof ToastUtils.showSuccess === 'function') ToastUtils.showSuccess(message);
}
function toggleUserStatus(userId, action, button) {
    openStatusDialog(action, [String(userId)], button || document.querySelector(`.toggle-status-btn[data-user-id="${userId}"]`));
}
function openStatusDialog(action, userIds, button) {
    if (!['enable', 'disable'].includes(action) || !userIds.length) return;
    const element = document.getElementById('userStatusConfirmModal');
    if (!element || !window.bootstrap || !bootstrap.Modal) {
        userManagementError('The confirmation dialog is not available. Please reload this page.');
        return;
    }
    statusDialog.action = action;
    statusDialog.userIds = userIds;
    statusDialog.button = button || null;
    const title = element.querySelector('#statusChangeTitle');
    const description = element.querySelector('#statusChangeDescription');
    const submit = element.querySelector('#confirmUserStatusButton');
    const input = element.querySelector('#statusChangeReason');
    const error = element.querySelector('#statusChangeError');
    title.textContent = `${action === 'disable' ? 'Disable' : 'Enable'} ${userIds.length === 1 ? 'user' : `${userIds.length} users`}`;
    description.textContent = action === 'disable'
        ? 'The selected account(s) will no longer be able to sign in. Existing sessions will be invalidated where possible.'
        : 'The selected account(s) will regain sign-in access.';
    submit.textContent = action === 'disable' ? 'Disable user' + (userIds.length > 1 ? 's' : '') : 'Enable user' + (userIds.length > 1 ? 's' : '');
    submit.classList.toggle('btn-danger', action === 'disable');
    submit.classList.toggle('btn-primary', action !== 'disable');
    submit.disabled = false;
    input.value = '';
    error.hidden = true;
    error.textContent = '';
    const modal = bootstrap.Modal.getOrCreateInstance(element);
    modal.show();
}
async function confirmStatusChange() {
    const element = document.getElementById('userStatusConfirmModal');
    const reason = element.querySelector('#statusChangeReason').value.trim();
    const error = element.querySelector('#statusChangeError');
    const button = element.querySelector('#confirmUserStatusButton');
    if (!reason || reason.length > 1000) {
        error.textContent = 'Please provide a reason (1–1000 characters).';
        error.hidden = false;
        element.querySelector('#statusChangeReason').focus();
        return;
    }
    button.disabled = true;
    button.textContent = 'Processing…';
    const isBulk = statusDialog.userIds.length !== 1 || !statusDialog.button;
    const token = getCookie('csrftoken');
    const headers = {'X-CSRFToken': token, 'X-Requested-With': 'XMLHttpRequest'};
    let endpoint, body;
    if (isBulk) {
        endpoint = element.dataset.bulkUrl;
        headers['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
        body = new URLSearchParams({ action: statusDialog.action, user_ids: JSON.stringify(statusDialog.userIds), reason });
    } else {
        endpoint = statusDialog.button.dataset.url;
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify({ action: statusDialog.action, reason });
    }
    try {
        const response = await fetch(endpoint, {method: 'POST', headers, body, credentials: 'same-origin'});
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || `Request failed (${response.status})`);
        bootstrap.Modal.getOrCreateInstance(element).hide();
        userManagementSuccess(data.message || 'Account status updated.');
        window.location.reload();
    } catch (exc) {
        error.textContent = exc.message || 'Unable to change account status.';
        error.hidden = false;
        button.disabled = false;
        button.textContent = statusDialog.action === 'disable' ? 'Disable account' : 'Enable account';
    }
}

// Manage user roles (assign/remove)
function manageUserRole(userId, role, action, reason = '', campuses = []) {
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
            reason: reason,
            campuses: campuses
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

// Bulk actions share the same reason-required status dialog.
function performBulkAction(action, userIds) {
    if (!userIds.length) { userManagementError('Select at least one user.'); return; }
    openStatusDialog(action, userIds, null);
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const submitStatus = document.getElementById('confirmUserStatusButton');
    if (submitStatus) submitStatus.addEventListener('click', confirmStatusChange);
    // Toggle status buttons
    const toggleStatusButtons = document.querySelectorAll('.toggle-status-btn');
    toggleStatusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const action = this.getAttribute('data-action');
            toggleUserStatus(userId, action, this);
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
