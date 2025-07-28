// Connection management JavaScript

// Note: csrftoken is already declared globally in base.html

// Show toast notifications
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// Send connection request
function sendConnectionRequest(userId) {
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
            showToast(data.message, 'success');
            updateConnectionButton(userId, 'pending_sent');
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'danger');
    });
}

// Accept connection request
function acceptConnectionRequest(connectionId) {
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
            showToast(data.message, 'success');
            updateConnectionButton(userId, 'connected');
            // Update pending requests count
            updatePendingRequestsCount();
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'danger');
    });
}

// Reject connection request
function rejectConnectionRequest(connectionId) {
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
            showToast(data.message, 'success');
            updateConnectionButton(userId, 'none');
            // Update pending requests count
            updatePendingRequestsCount();
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'danger');
    });
}

// Remove connection
function removeConnection(userId) {
    if (!confirm('Are you sure you want to remove this connection?')) {
        return;
    }
    
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
            showToast(data.message, 'success');
            updateConnectionButton(userId, 'none');
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'danger');
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
        
        // Accept connection button click (from connection requests page)
        if (e.target.closest('.accept-btn')) {
            e.preventDefault();
            const button = e.target.closest('.accept-btn');
            const connectionId = button.getAttribute('data-connection-id');
            acceptConnectionRequest(connectionId);
        }
        
        // Reject connection button click (from connection requests page)
        if (e.target.closest('.reject-btn')) {
            e.preventDefault();
            const button = e.target.closest('.reject-btn');
            const connectionId = button.getAttribute('data-connection-id');
            rejectConnectionRequest(connectionId);
        }
        
        // Accept connection button click (from alumni directory/detail)
        if (e.target.closest('.accept-connection-btn')) {
            e.preventDefault();
            const button = e.target.closest('.accept-connection-btn');
            const userId = button.getAttribute('data-user-id');
            acceptConnectionRequest(userId);
        }
        
        // Reject connection button click (from alumni directory/detail)
        if (e.target.closest('.reject-connection-btn')) {
            e.preventDefault();
            const button = e.target.closest('.reject-connection-btn');
            const userId = button.getAttribute('data-user-id');
            rejectConnectionRequest(userId);
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