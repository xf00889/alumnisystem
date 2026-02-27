// Connection management JavaScript

// Get CSRF token helper function
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

// Get CSRF token from DOM or cookie
function getCSRFToken() {
    // First try to get from DOM (works even with HttpOnly cookies)
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenInput && tokenInput.value) {
        return tokenInput.value;
    }
    
    // Fallback to cookie (only works if CSRF_COOKIE_HTTPONLY = False)
    return getCookie('csrftoken');
}

// Toast notifications now handled by ToastUtils (toast-notifications.js)

// Send connection request
function sendConnectionRequest(userId) {
    const csrftoken = getCSRFToken();
    fetch(`/connections/send-request/${userId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastUtils.showSuccess(data.message);
            updateConnectionButton(userId, 'pending_sent');
        } else {
            ToastUtils.showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ToastUtils.showError('An error occurred. Please try again.');
    });
}

// Accept connection request
function acceptConnectionRequest(connectionId) {
    const csrftoken = getCSRFToken();
    fetch(`/connections/accept/${connectionId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastUtils.showSuccess(data.message);
            updateConnectionButton(data.user_id, 'connected');
            // Update pending requests count
            updatePendingRequestsCount();
        } else {
            ToastUtils.showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ToastUtils.showError('An error occurred. Please try again.');
    });
}

// Reject connection request
function rejectConnectionRequest(connectionId) {
    const csrftoken = getCSRFToken();
    fetch(`/connections/reject/${connectionId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastUtils.showSuccess(data.message);
            updateConnectionButton(data.user_id, 'none');
            // Update pending requests count
            updatePendingRequestsCount();
        } else {
            ToastUtils.showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ToastUtils.showError('An error occurred. Please try again.');
    });
}

// Remove connection
function removeConnection(userId) {
    if (!confirm('Are you sure you want to remove this connection?')) {
        return;
    }
    
    const csrftoken = getCSRFToken();
    fetch(`/connections/remove/${userId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastUtils.showSuccess(data.message);
            // Refresh the page after a short delay to show the toast
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            ToastUtils.showError(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        ToastUtils.showError('An error occurred. Please try again.');
    });
}

// Update connection button based on status
function updateConnectionButton(userId, status) {
    const buttons = document.querySelectorAll(`[data-user-id="${userId}"]`);
    
    buttons.forEach(button => {
        const parent = button.closest('.card-actions, .contact-actions, .btn-group');
        if (!parent) return;
        
        // Remove existing connection buttons
        parent.querySelectorAll('.connect-btn, .accept-connection-btn, .reject-connection-btn, .remove-connection-btn').forEach(btn => {
            if (btn !== button) btn.remove();
        });
        
        switch (status) {
            case 'none':
                button.className = 'btn btn-outline-success btn-sm connect-btn';
                button.innerHTML = '<i class="fas fa-user-plus me-1"></i>Connect';
                button.disabled = false;
                break;
            case 'pending_sent':
                button.className = 'btn btn-outline-warning btn-sm';
                button.innerHTML = '<i class="fas fa-clock me-1"></i>Pending';
                button.disabled = true;
                break;
            case 'pending_received':
                button.className = 'btn btn-success btn-sm accept-connection-btn';
                button.innerHTML = '<i class="fas fa-check me-1"></i>Accept';
                button.disabled = false;
                break;
            case 'connected':
                button.className = 'btn btn-success btn-sm';
                button.innerHTML = '<i class="fas fa-comments me-1"></i>Message';
                button.disabled = false;
                // Convert to link for messaging
                const messageUrl = `/connections/messages/${userId}/`;
                button.onclick = () => window.location.href = messageUrl;
                break;
        }
    });
}

// Update pending requests count in navigation
function updatePendingRequestsCount() {
    const csrftoken = getCSRFToken();
    fetch('/connections/pending-count/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
    .then(response => response.json())
    .then(data => {
        const badge = document.querySelector('.navbar .badge');
        if (data.count > 0) {
            if (badge) {
                badge.textContent = data.count;
            } else {
                // Create badge if it doesn't exist
                const navLink = document.querySelector('a[href*="connection_requests"]');
                if (navLink) {
                    const newBadge = document.createElement('span');
                    newBadge.className = 'badge bg-danger ms-1';
                    newBadge.textContent = data.count;
                    navLink.appendChild(newBadge);
                }
            }
        } else {
            if (badge) {
                badge.remove();
            }
        }
    })
    .catch(error => {
        console.error('Error updating pending requests count:', error);
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Connect button click
    document.addEventListener('click', function(e) {
        if (e.target.closest('.connect-btn')) {
            e.preventDefault();
            const button = e.target.closest('.connect-btn');
            const userId = button.getAttribute('data-user-id');
            sendConnectionRequest(userId);
        }
        
        // Accept connection button click (from alumni directory/detail)
        if (e.target.closest('.accept-connection-btn')) {
            e.preventDefault();
            const button = e.target.closest('.accept-connection-btn');
            const connectionId = button.getAttribute('data-connection-id');
            acceptConnectionRequest(connectionId);
        }
        
        // Reject connection button click (from alumni directory/detail)
        if (e.target.closest('.reject-connection-btn')) {
            e.preventDefault();
            const button = e.target.closest('.reject-connection-btn');
            const connectionId = button.getAttribute('data-connection-id');
            rejectConnectionRequest(connectionId);
        }
        
        // Remove connection button click
        if (e.target.closest('.remove-connection-btn')) {
            e.preventDefault();
            const button = e.target.closest('.remove-connection-btn');
            const userId = button.getAttribute('data-user-id');
            removeConnection(userId);
        }
    });
});

// Export functions for use in templates
window.sendConnectionRequest = sendConnectionRequest;
window.acceptConnectionRequest = acceptConnectionRequest;
window.rejectConnectionRequest = rejectConnectionRequest;
window.removeConnection = removeConnection;