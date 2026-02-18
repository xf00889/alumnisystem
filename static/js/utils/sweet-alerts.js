/**
 * SweetAlert2 Utility Functions for Announcement Notifications
 * This file contains utility functions for displaying SweetAlert2 notifications
 * for announcement creation, updating, and deletion.
 * 
 * Updated: Fixed announcement button appearing on profile messages
 * Version: 2.0
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
// SweetAlert2 includes built-in accessibility features:
// - Focus trapping: Keyboard focus stays within the dialog (Requirement 9.2)
// - ARIA attributes: role="dialog", aria-modal="true", aria-labelledby, aria-describedby (Requirement 9.4)
// - Keyboard navigation: Tab/Shift+Tab cycles through interactive elements
// - Escape key support: Closes dialog when allowEscapeKey is true
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
    buttonsStyling: true,
    // Accessibility: Ensure focus management is enabled (default behavior)
    // SweetAlert2 automatically traps focus within the dialog
    // and cycles through focusable elements with Tab/Shift+Tab
    focusConfirm: true,  // Focus confirm button by default
    allowEscapeKey: true, // Allow Escape key to close (accessibility requirement)
    // Note: allowOutsideClick defaults to true, but can be overridden for specific dialogs
};

/**
 * Verify and enhance ARIA attributes for SweetAlert2 dialogs
 * 
 * This function ensures that SweetAlert2 dialogs have proper ARIA attributes for screen reader accessibility.
 * While SweetAlert2 v11 includes these by default, this function provides verification and enhancement.
 * 
 * Requirements 9.4: Dialogs must have:
 * - role="dialog" or role="alertdialog" for proper semantic meaning
 * - aria-modal="true" to indicate modal behavior
 * - aria-labelledby pointing to the title element
 * - aria-describedby pointing to the content element (optional but recommended)
 * 
 * @private
 * @returns {void}
 */
function ensureSweetAlertARIA() {
    try {
        const swalPopup = document.querySelector('.swal2-popup');
        
        if (!swalPopup) {
            return; // No dialog present
        }
        
        // Verify role attribute (should be 'dialog' or 'alertdialog')
        if (!swalPopup.hasAttribute('role')) {
            console.warn('SweetAlert2: Adding missing role="dialog" attribute');
            swalPopup.setAttribute('role', 'dialog');
        }
        
        // Verify aria-modal attribute
        if (!swalPopup.hasAttribute('aria-modal')) {
            console.warn('SweetAlert2: Adding missing aria-modal="true" attribute');
            swalPopup.setAttribute('aria-modal', 'true');
        }
        
        // Verify aria-labelledby (should point to title)
        const titleElement = swalPopup.querySelector('.swal2-title');
        if (titleElement && !swalPopup.hasAttribute('aria-labelledby')) {
            // Generate or get ID for title
            if (!titleElement.id) {
                titleElement.id = 'swal2-title-' + Date.now();
            }
            console.warn('SweetAlert2: Adding missing aria-labelledby attribute');
            swalPopup.setAttribute('aria-labelledby', titleElement.id);
        }
        
        // Verify aria-describedby (should point to content)
        const contentElement = swalPopup.querySelector('.swal2-html-container');
        if (contentElement && !swalPopup.hasAttribute('aria-describedby')) {
            // Generate or get ID for content
            if (!contentElement.id) {
                contentElement.id = 'swal2-content-' + Date.now();
            }
            console.warn('SweetAlert2: Adding missing aria-describedby attribute');
            swalPopup.setAttribute('aria-describedby', contentElement.id);
        }
        
        // Verify close button has proper accessibility
        const closeButton = swalPopup.querySelector('.swal2-close');
        if (closeButton) {
            if (!closeButton.hasAttribute('aria-label')) {
                closeButton.setAttribute('aria-label', 'Close dialog');
            }
        }
        
        // Verify buttons have proper accessibility
        const confirmButton = swalPopup.querySelector('.swal2-confirm');
        const cancelButton = swalPopup.querySelector('.swal2-cancel');
        
        if (confirmButton && !confirmButton.hasAttribute('aria-label')) {
            const buttonText = confirmButton.textContent.trim();
            if (buttonText) {
                confirmButton.setAttribute('aria-label', buttonText);
            }
        }
        
        if (cancelButton && !cancelButton.hasAttribute('aria-label')) {
            const buttonText = cancelButton.textContent.trim();
            if (buttonText) {
                cancelButton.setAttribute('aria-label', buttonText);
            }
        }
        
    } catch (error) {
        console.error('SweetAlertUtils.ensureSweetAlertARIA: Error ensuring ARIA attributes:', error);
    }
}

/**
 * Show success notification when an announcement is created
 * Uses Notyf toast for non-blocking notification
 * 
 * @param {string} message - Success message to display
 * @param {string} redirectUrl - URL to redirect to after notification
 */
function showAnnouncementCreatedAlert(message, redirectUrl) {
    try {
        // Use ToastUtils for non-blocking notification
        if (typeof ToastUtils !== 'undefined' && typeof ToastUtils.showSuccess === 'function') {
            ToastUtils.showSuccess(message || 'Announcement was created successfully!');
            
            // Redirect after a short delay to allow user to see the toast
            if (redirectUrl) {
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000); // 1 second delay
            }
        } else {
            console.error('ToastUtils is not available. Please ensure toast-notifications.js is loaded.');
            // Fallback to alert if ToastUtils not available
            alert(message || 'Announcement was created successfully!');
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        }
    } catch (error) {
        console.error('SweetAlertUtils.showAnnouncementCreatedAlert: Error displaying notification:', error);
        // Fallback to alert
        alert(message || 'Announcement was created successfully!');
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    }
}

/**
 * Show success notification when an announcement is updated
 * Uses Notyf toast for non-blocking notification
 * 
 * @param {string} message - Success message to display
 * @param {string} redirectUrl - URL to redirect to after notification
 */
function showAnnouncementUpdatedAlert(message, redirectUrl) {
    try {
        // Use ToastUtils for non-blocking notification
        if (typeof ToastUtils !== 'undefined' && typeof ToastUtils.showSuccess === 'function') {
            ToastUtils.showSuccess(message || 'Announcement was updated successfully!');
            
            // Redirect after a short delay to allow user to see the toast
            if (redirectUrl) {
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000); // 1 second delay
            }
        } else {
            console.error('ToastUtils is not available. Please ensure toast-notifications.js is loaded.');
            // Fallback to alert if ToastUtils not available
            alert(message || 'Announcement was updated successfully!');
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        }
    } catch (error) {
        console.error('SweetAlertUtils.showAnnouncementUpdatedAlert: Error displaying notification:', error);
        // Fallback to alert
        alert(message || 'Announcement was updated successfully!');
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    }
}

/**
 * Show success notification when an announcement is deleted
 * Uses Notyf toast for non-blocking notification
 * 
 * @param {string} message - Success message to display
 * @param {string} redirectUrl - URL to redirect to after notification
 */
function showAnnouncementDeletedAlert(message, redirectUrl) {
    try {
        // Use ToastUtils for non-blocking notification
        if (typeof ToastUtils !== 'undefined' && typeof ToastUtils.showSuccess === 'function') {
            ToastUtils.showSuccess(message || 'Announcement was deleted successfully!');
            
            // Redirect after a short delay to allow user to see the toast
            if (redirectUrl) {
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000); // 1 second delay
            }
        } else {
            console.error('ToastUtils is not available. Please ensure toast-notifications.js is loaded.');
            // Fallback to alert if ToastUtils not available
            alert(message || 'Announcement was deleted successfully!');
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
        }
    } catch (error) {
        console.error('SweetAlertUtils.showAnnouncementDeletedAlert: Error displaying notification:', error);
        // Fallback to alert
        alert(message || 'Announcement was deleted successfully!');
        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    }
}

/**
 * Show error notification when an operation fails
 * Uses Notyf toast for non-blocking notification
 * 
 * @param {string} message - Error message to display
 */
function showErrorAlert(message) {
    try {
        // Use ToastUtils for non-blocking notification
        if (typeof ToastUtils !== 'undefined' && typeof ToastUtils.showError === 'function') {
            ToastUtils.showError(message || 'An error occurred. Please try again.');
        } else {
            console.error('ToastUtils is not available. Please ensure toast-notifications.js is loaded.');
            // Fallback to alert if ToastUtils not available
            alert('Error: ' + (message || 'An error occurred. Please try again.'));
        }
    } catch (error) {
        console.error('SweetAlertUtils.showErrorAlert: Error displaying notification:', error);
        // Fallback to alert
        alert('Error: ' + (message || 'An error occurred. Please try again.'));
    }
}

/**
 * Show loading indicator for long-running processes
 * @param {string} title - Title to display in the loading alert
 * @param {string} message - Message to display in the loading alert
 * @returns {Object} - SweetAlert2 instance that can be closed with Swal.close()
 */
function showLoadingIndicator(title, message) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.showLoadingIndicator: SweetAlert2 library not loaded');
            return null;
        }
        
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
                // Requirement 9.4: Ensure ARIA attributes are present for screen reader accessibility
                ensureSweetAlertARIA();
            }
        });
    } catch (error) {
        console.error('SweetAlertUtils.showLoadingIndicator: Error displaying loading indicator:', error);
        return null;
    }
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
 * 
 * @deprecated This function is deprecated. Use ToastUtils.processDjangoMessages() instead.
 * SweetAlert2 should only be used for confirmation dialogs, not for non-blocking notifications.
 * This function now redirects to ToastUtils for proper toast notification handling.
 * 
 * @see ToastUtils.processDjangoMessages
 */
function processDjangoMessagesAsSweetAlert() {
    try {
        // Log deprecation warning
        console.warn(
            'DEPRECATION WARNING: processDjangoMessagesAsSweetAlert() is deprecated. ' +
            'Please use ToastUtils.processDjangoMessages() instead. ' +
            'SweetAlert2 should only be used for confirmation dialogs. ' +
            'Redirecting to ToastUtils.processDjangoMessages()...'
        );
        
        // Redirect to ToastUtils if available
        if (typeof ToastUtils !== 'undefined' && typeof ToastUtils.processDjangoMessages === 'function') {
            ToastUtils.processDjangoMessages();
        } else {
            console.error(
                'ToastUtils is not available. Please ensure toast-notifications.js is loaded before sweet-alerts.js'
            );
        }
    } catch (error) {
        console.error('SweetAlertUtils.processDjangoMessagesAsSweetAlert: Error processing messages:', error);
    }
}

/**
 * Enhanced form submission with SweetAlert confirmation and feedback
 * @param {HTMLFormElement} form - The form element to handle
 * @param {Object} options - Configuration options
 */
function handleFormSubmission(form, options = {}) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.handleFormSubmission: SweetAlert2 library not loaded');
            // Fallback to standard form submission
            form.submit();
            return;
        }
        
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
    } catch (error) {
        console.error('SweetAlertUtils.handleFormSubmission: Error setting up form submission:', error);
    }
}

/**
 * Submit form with AJAX and handle response
 * @param {HTMLFormElement} form - The form element
 * @param {Object} config - Configuration options
 */
function submitForm(form, config) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.submitForm: SweetAlert2 library not loaded');
            // Fallback to standard form submission
            form.submit();
            return;
        }
        
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
        const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfElement ? csrfElement.value : getCookie('csrftoken');
        
        fetch(form.action, {
            method: form.method || 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
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
    } catch (error) {
        console.error('SweetAlertUtils.submitForm: Error submitting form:', error);
        alert('An error occurred while submitting the form. Please try again.');
    }
}

/**
 * Show confirmation dialog for delete operations
 * Uses SweetAlert2 for confirmation, then Notyf toast for success feedback
 * 
 * @param {string} title - Title of the item to delete
 * @param {string} deleteUrl - URL to send delete request to
 * @param {string} redirectUrl - URL to redirect to after successful deletion
 */
function confirmDelete(title, deleteUrl, redirectUrl = null) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.confirmDelete: SweetAlert2 library not loaded');
            // Fallback to browser confirm for critical operations
            if (confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
                // Proceed with deletion using fetch
                fetch(deleteUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('The item has been deleted successfully.');
                        if (redirectUrl) {
                            window.location.href = redirectUrl;
                        } else {
                            location.reload();
                        }
                    } else {
                        throw new Error(data.message || 'Failed to delete item');
                    }
                })
                .catch(error => {
                    alert('Error: ' + error.message);
                });
            }
            return;
        }
        
        Swal.fire({
            ...defaultConfig,
            icon: 'warning',
            title: 'Confirm Deletion',
            text: `Are you sure you want to delete "${title}"? This action cannot be undone.`,
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it!',
            cancelButtonText: 'Cancel',
            didOpen: () => {
                // Requirement 9.4: Ensure ARIA attributes are present for screen reader accessibility
                ensureSweetAlertARIA();
            }
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
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Close the loading indicator
                        Swal.close();
                        
                        // Use ToastUtils for success message (non-blocking)
                        if (typeof ToastUtils !== 'undefined' && typeof ToastUtils.showSuccess === 'function') {
                            ToastUtils.showSuccess('The item has been deleted successfully.');
                        } else {
                            // Fallback if ToastUtils not available
                            alert('The item has been deleted successfully.');
                        }
                        
                        // Redirect after a short delay
                        setTimeout(() => {
                            if (redirectUrl) {
                                window.location.href = redirectUrl;
                            } else {
                                location.reload();
                            }
                        }, 1000);
                    } else {
                        throw new Error(data.message || 'Failed to delete item');
                    }
                })
                .catch(error => {
                    // Close loading indicator and show error toast
                    Swal.close();
                    
                    if (typeof ToastUtils !== 'undefined' && typeof ToastUtils.showError === 'function') {
                        ToastUtils.showError(error.message);
                    } else {
                        // Fallback to SweetAlert2 for errors if ToastUtils not available
                        Swal.fire({
                            ...defaultConfig,
                            icon: 'error',
                            title: 'Error',
                            text: error.message,
                            confirmButtonText: 'OK'
                        });
                    }
                });
            }
        });
    } catch (error) {
        console.error('SweetAlertUtils.confirmDelete: Error in confirmation dialog:', error);
        // Fallback to browser confirm
        if (confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
            alert('An error occurred. Please try again or contact support.');
        }
    }
}

/**
 * Show success message for form operations
 * @param {string} message - Success message
 * @param {string} redirectUrl - Optional redirect URL
 */
function showSuccessMessage(message, redirectUrl = null) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.showSuccessMessage: SweetAlert2 library not loaded');
            alert(message);
            if (redirectUrl) {
                window.location.href = redirectUrl;
            }
            return;
        }
        
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
    } catch (error) {
        console.error('SweetAlertUtils.showSuccessMessage: Error displaying success message:', error);
    }
}

/**
 * Show error message for form operations
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.showErrorMessage: SweetAlert2 library not loaded');
            alert('Error: ' + message);
            return;
        }
        
        Swal.fire({
            ...defaultConfig,
            icon: 'error',
            title: 'Error',
            text: message,
            confirmButtonText: 'OK'
        });
    } catch (error) {
        console.error('SweetAlertUtils.showErrorMessage: Error displaying error message:', error);
    }
}

/**
 * Show warning message
 * @param {string} message - Warning message
 */
function showWarningMessage(message) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.showWarningMessage: SweetAlert2 library not loaded');
            alert('Warning: ' + message);
            return;
        }
        
        Swal.fire({
            ...defaultConfig,
            icon: 'warning',
            title: 'Warning',
            text: message,
            confirmButtonText: 'OK'
        });
    } catch (error) {
        console.error('SweetAlertUtils.showWarningMessage: Error displaying warning message:', error);
    }
}

/**
 * Show info message
 * @param {string} message - Info message
 */
function showInfoMessage(message) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.showInfoMessage: SweetAlert2 library not loaded');
            alert(message);
            return;
        }
        
        Swal.fire({
            ...defaultConfig,
            icon: 'info',
            title: 'Information',
            text: message,
            confirmButtonText: 'OK'
        });
    } catch (error) {
        console.error('SweetAlertUtils.showInfoMessage: Error displaying info message:', error);
    }
}

/**
 * Confirm deletion of an announcement
 * @param {string} title - Title of the announcement to delete
 * @param {string} deleteUrl - URL to send delete request to
 * @param {string} redirectUrl - URL to redirect to after successful deletion
 */
function confirmAnnouncementDeletion(title, deleteUrl, redirectUrl) {
    try {
        // Check if SweetAlert2 is loaded
        if (typeof Swal === 'undefined') {
            console.error('SweetAlertUtils.confirmAnnouncementDeletion: SweetAlert2 library not loaded');
            // Fallback to browser confirm for critical operations
            if (confirm(`Are you sure you want to delete the announcement: "${title}"?`)) {
                // Try to get CSRF token from different sources
                let csrfToken;
                const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfElement) {
                    csrfToken = csrfElement.value;
                } else {
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
            return;
        }
        
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
            didOpen: () => {
                // Requirement 9.4: Ensure ARIA attributes are present for screen reader accessibility
                ensureSweetAlertARIA();
            }
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
    } catch (error) {
        console.error('SweetAlertUtils.confirmAnnouncementDeletion: Error in confirmation dialog:', error);
        showErrorAlert('An error occurred while trying to delete the announcement. Please try again.');
    }
}

// Export functions for use in other files
window.SweetAlertUtils = {
    showAnnouncementCreatedAlert,
    showAnnouncementUpdatedAlert,
    showAnnouncementDeletedAlert,
    showErrorAlert,
    showLoadingIndicator,
    showJobCrawlingIndicator,
    processDjangoMessages: processDjangoMessagesAsSweetAlert, // Deprecated - redirects to ToastUtils
    confirmDelete,
    confirmAnnouncementDeletion
};