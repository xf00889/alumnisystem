/**
 * SweetAlert2 Utility Functions for Announcement Notifications
 * This file contains utility functions for displaying SweetAlert2 notifications
 * for announcement creation, updating, and deletion.
 */

/**
 * Get cookie value by name
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value or null
 */
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
 * Show loading indicator for long-running processes
 * @param {string} title - Title to display in the loading alert
 * @param {string} message - Message to display in the loading alert
 * @returns {Object} - SweetAlert2 instance that can be closed with Swal.close()
 */
function showLoadingIndicator(title, message) {
    return Swal.fire({
        title: title || 'Processing',
        html: `<div class="text-center">
                <p>${message || 'Please wait while we process your request...'}</p>
                <div class="progress mt-3" style="height: 15px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
                </div>
               </div>`,
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
}

/**
 * Show loading indicator specifically for crawling jobs
 * @param {string} source - Source of jobs being crawled
 * @param {string} category - Category of jobs being crawled (optional)
 * @returns {Object} - SweetAlert2 instance that can be closed with Swal.close()
 */
function showJobCrawlingIndicator(source, category) {
    const categoryText = category ? category : 'all categories';
    return showLoadingIndicator(
        'Crawling Jobs',
        `<p>Crawling ${categoryText} from ${source}...</p>
        <p class="small text-muted">This process may take a few minutes. Please be patient.</p>`
    );
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
        
        // Skip processing signup-related success messages
        if (messageType === 'success' && (
            messageText.includes('Registration completed successfully') ||
            messageText.includes('Account created successfully') ||
            messageText.includes('Welcome') ||
            messageText.includes('Sign up successful') ||
            messageText.includes('Account created') ||
            messageText.includes('Registration successful')
        )) {
            // Just hide the Django message without showing SweetAlert
            document.querySelector('.messages').style.display = 'none';
            return;
        }
        
        // Skip processing on signup-related pages
        const currentPath = window.location.pathname;
        if (currentPath.includes('/accounts/signup/') || 
            currentPath.includes('/accounts/post_registration/') ||
            currentPath.includes('/accounts/complete_registration/')) {
            // Just hide the Django message without showing SweetAlert
            document.querySelector('.messages').style.display = 'none';
            return;
        }
        
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
 * Enhanced form submission with SweetAlert confirmation and feedback
 * @param {HTMLFormElement} form - The form element to handle
 * @param {Object} options - Configuration options
 */
function handleFormSubmission(form, options = {}) {
    const defaultOptions = {
        confirmText: 'Are you sure you want to submit this form?',
        successText: 'Operation completed successfully!',
        errorText: 'An error occurred. Please try again.',
        showConfirmation: true,
        redirectUrl: null,
        customSuccessCallback: null,
        customErrorCallback: null
    };
    
    const config = { ...defaultOptions, ...options };
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (config.showConfirmation) {
            Swal.fire({
                ...defaultConfig,
                icon: 'question',
                title: 'Confirm Action',
                text: config.confirmText,
                showCancelButton: true,
                confirmButtonText: 'Yes, proceed',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    submitForm(form, config);
                }
            });
        } else {
            submitForm(form, config);
        }
    });
}

/**
 * Submit form with AJAX and handle response
 * @param {HTMLFormElement} form - The form element
 * @param {Object} config - Configuration options
 */
function submitForm(form, config) {
    // Show loading state
    Swal.fire({
        ...defaultConfig,
        title: 'Processing...',
        text: 'Please wait while we process your request.',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: form.method || 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                ...defaultConfig,
                icon: 'success',
                title: 'Success!',
                text: config.customSuccessCallback ? config.customSuccessCallback(data) : config.successText,
                confirmButtonText: 'OK'
            }).then(() => {
                if (config.redirectUrl) {
                    window.location.href = config.redirectUrl;
                } else if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            });
        } else {
            throw new Error(data.message || config.errorText);
        }
    })
    .catch(error => {
        Swal.fire({
            ...defaultConfig,
            icon: 'error',
            title: 'Error',
            text: config.customErrorCallback ? config.customErrorCallback(error) : error.message,
            confirmButtonText: 'OK'
        });
    });
}

/**
 * Show confirmation dialog for delete operations
 * @param {string} title - Title of the item to delete
 * @param {string} deleteUrl - URL to send delete request to
 * @param {string} redirectUrl - URL to redirect to after successful deletion
 */
function confirmDelete(title, deleteUrl, redirectUrl = null) {
    Swal.fire({
        ...defaultConfig,
        icon: 'warning',
        title: 'Confirm Deletion',
        text: `Are you sure you want to delete "${title}"? This action cannot be undone.`,
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                ...defaultConfig,
                title: 'Deleting...',
                text: 'Please wait while we delete the item.',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Send delete request
            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        ...defaultConfig,
                        icon: 'success',
                        title: 'Deleted!',
                        text: 'The item has been deleted successfully.',
                        confirmButtonText: 'OK'
                    }).then(() => {
                        if (redirectUrl) {
                            window.location.href = redirectUrl;
                        } else {
                            location.reload();
                        }
                    });
                } else {
                    throw new Error(data.message || 'Failed to delete item');
                }
            })
            .catch(error => {
                Swal.fire({
                    ...defaultConfig,
                    icon: 'error',
                    title: 'Error',
                    text: error.message,
                    confirmButtonText: 'OK'
                });
            });
        }
    });
}

/**
 * Show success message for form operations
 * @param {string} message - Success message
 * @param {string} redirectUrl - Optional redirect URL
 */
function showSuccessMessage(message, redirectUrl = null) {
    Swal.fire({
        ...defaultConfig,
        icon: 'success',
        title: 'Success!',
        text: message,
        confirmButtonText: 'OK'
    }).then(() => {
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    });
}

/**
 * Show error message for form operations
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    Swal.fire({
        ...defaultConfig,
        icon: 'error',
        title: 'Error',
        text: message,
        confirmButtonText: 'OK'
    });
}

/**
 * Show warning message
 * @param {string} message - Warning message
 */
function showWarningMessage(message) {
    Swal.fire({
        ...defaultConfig,
        icon: 'warning',
        title: 'Warning',
        text: message,
        confirmButtonText: 'OK'
    });
}

/**
 * Show info message
 * @param {string} message - Info message
 */
function showInfoMessage(message) {
    Swal.fire({
        ...defaultConfig,
        icon: 'info',
        title: 'Information',
        text: message,
        confirmButtonText: 'OK'
    });
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
            // Try to get CSRF token from different sources
            let csrfToken;
            const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfElement) {
                csrfToken = csrfElement.value;
            } else {
                // Fallback to cookie if meta tag not found
                csrfToken = getCookie('csrftoken');
            }
            
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
    showLoadingIndicator,
    showJobCrawlingIndicator,
    processDjangoMessages,
    confirmAnnouncementDeletion
};