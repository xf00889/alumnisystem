/**
 * SweetAlert2 Utility Functions for Announcement Notifications
 * This file contains utility functions for displaying SweetAlert2 notifications
 * for announcement creation, updating, and deletion.
 */

// Default configuration for SweetAlert notifications
const defaultConfig = {
    position: 'center',
    showConfirmButton: true,
    timer: 3000,
    timerProgressBar: true,
    customClass: {
        container: 'swal-container',
        popup: 'swal-popup',
        title: 'swal-title',
        htmlContainer: 'swal-content',
        confirmButton: 'swal-confirm-btn',
    },
    buttonsStyling: true
};

/**
 * Show success notification when an announcement is created
 * @param {string} message - Success message to display
 * @param {string} redirectUrl - URL to redirect to after dismissal
 */
function showAnnouncementCreatedAlert(message, redirectUrl) {
    Swal.fire({
        ...defaultConfig,
        icon: 'success',
        title: 'Success!',
        text: message || 'Announcement was created successfully!',
        confirmButtonText: 'View Announcements',
        confirmButtonColor: '#2b3c6b', // primary color from CSS variables
    }).then((result) => {
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    });
}

/**
 * Show success notification when an announcement is updated
 * @param {string} message - Success message to display
 * @param {string} redirectUrl - URL to redirect to after dismissal
 */
function showAnnouncementUpdatedAlert(message, redirectUrl) {
    Swal.fire({
        ...defaultConfig,
        icon: 'success',
        title: 'Success!',
        text: message || 'Announcement was updated successfully!',
        confirmButtonText: 'View Announcements',
        confirmButtonColor: '#2b3c6b', // primary color from CSS variables
    }).then((result) => {
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    });
}

/**
 * Show success notification when an announcement is deleted
 * @param {string} message - Success message to display
 * @param {string} redirectUrl - URL to redirect to after dismissal
 */
function showAnnouncementDeletedAlert(message, redirectUrl) {
    Swal.fire({
        ...defaultConfig,
        icon: 'success',
        title: 'Success!',
        text: message || 'Announcement was deleted successfully!',
        confirmButtonText: 'Return to Announcements',
        confirmButtonColor: '#2b3c6b', // primary color from CSS variables
    }).then((result) => {
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    });
}

/**
 * Show error notification when an operation fails
 * @param {string} message - Error message to display
 */
function showErrorAlert(message) {
    Swal.fire({
        ...defaultConfig,
        icon: 'error',
        title: 'Error!',
        text: message || 'An error occurred. Please try again.',
        confirmButtonText: 'OK',
        confirmButtonColor: '#e53e3e', // error color from CSS variables
        timer: 5000, // Longer timer for error messages
    });
}

/**
 * Process Django messages and display them as SweetAlert notifications
 * This function can be called on page load to convert Django messages to SweetAlert
 */
function processDjangoMessages() {
    const messages = document.querySelectorAll('.messages .alert');
    if (messages.length > 0) {
        // Process only the first message to avoid multiple alerts
        const firstMessage = messages[0];
        const messageText = firstMessage.textContent.trim();
        const messageType = firstMessage.classList.contains('alert-success') ? 'success' : 
                           firstMessage.classList.contains('alert-danger') ? 'error' :
                           firstMessage.classList.contains('alert-warning') ? 'warning' : 'info';
        
        // Hide the original Django message
        document.querySelector('.messages').style.display = 'none';
        
        // Convert to SweetAlert based on message type and content
        if (messageType === 'success') {
            if (messageText.includes('created')) {
                showAnnouncementCreatedAlert(messageText);
            } else if (messageText.includes('updated')) {
                showAnnouncementUpdatedAlert(messageText);
            } else if (messageText.includes('deleted')) {
                showAnnouncementDeletedAlert(messageText);
            } else {
                // Generic success message
                Swal.fire({
                    ...defaultConfig,
                    icon: 'success',
                    title: 'Success!',
                    text: messageText,
                });
            }
        } else if (messageType === 'error') {
            showErrorAlert(messageText);
        } else {
            // For info and warning messages
            Swal.fire({
                ...defaultConfig,
                icon: messageType,
                title: messageType.charAt(0).toUpperCase() + messageType.slice(1),
                text: messageText,
                confirmButtonText: 'OK',
            });
        }
    }
}

/**
 * Confirm deletion of an announcement
 * @param {string} title - Title of the announcement to delete
 * @param {string} deleteUrl - URL to send delete request to
 * @param {string} redirectUrl - URL to redirect to after successful deletion
 */
function confirmAnnouncementDeletion(title, deleteUrl, redirectUrl) {
    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to delete the announcement: "${title}"`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e53e3e',
        cancelButtonColor: '#718096',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true,
        focusCancel: true,
    }).then((result) => {
        if (result.isConfirmed) {
            // Send delete request
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (response.ok) {
                    return response.json().catch(() => {
                        // If not JSON, still treat as success
                        return { status: 'success', message: 'Announcement was deleted successfully.' };
                    });
                } else {
                    throw new Error('Failed to delete announcement');
                }
            })
            .then(data => {
                showAnnouncementDeletedAlert(data.message, redirectUrl);
            })
            .catch(error => {
                showErrorAlert(error.message || 'Failed to delete the announcement. Please try again.');
            });
        }
    });
}

// Export functions for use in other files
window.SweetAlertUtils = {
    showAnnouncementCreatedAlert,
    showAnnouncementUpdatedAlert,
    showAnnouncementDeletedAlert,
    showErrorAlert,
    processDjangoMessages,
    confirmAnnouncementDeletion
}; 