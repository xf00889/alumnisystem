/**
 * Toast Notification System
 * 
 * A lightweight toast notification system using Notyf library.
 * Replaces SweetAlert2 for non-blocking notifications.
 * 
 * This module provides a unified API for displaying toast notifications
 * and automatically processes Django messages on page load.
 * 
 * @module ToastNotifications
 * @author NORSU Alumni System
 * @version 1.0.0
 * 
 * @example
 * // Show a success toast
 * ToastUtils.showSuccess('Operation completed successfully!');
 * 
 * @example
 * // Show an error toast with custom duration
 * ToastUtils.showError('Something went wrong', { duration: 8000 });
 * 
 * @example
 * // Process Django messages automatically
 * ToastUtils.processDjangoMessages();
 */

(function() {
    'use strict';

    /**
     * Toast configuration object
     * Defines default durations, positions, and styling for each notification type
     * 
     * @constant {Object}
     * @property {Object} duration - Duration in milliseconds for each toast type
     * @property {Object} position - Default position for toasts
     * @property {boolean} dismissible - Whether toasts can be manually dismissed
     * @property {boolean} ripple - Whether to show ripple effect
     * @property {Array} types - Configuration for each toast type
     */
    const toastConfig = {
        duration: {
            success: 3000,  // 3 seconds
            error: 6000,    // 6 seconds
            warning: 4500,  // 4.5 seconds
            info: 3500      // 3.5 seconds
        },
        position: {
            x: 'right',     // 'left', 'center', 'right'
            y: 'top'        // 'top', 'center', 'bottom'
        },
        dismissible: true,
        ripple: true,
        types: [
            {
                type: 'success',
                backgroundColor: '#28a745',
                icon: {
                    className: 'notyf__icon--success',
                    tagName: 'i'
                }
            },
            {
                type: 'error',
                backgroundColor: '#dc3545',
                icon: {
                    className: 'notyf__icon--error',
                    tagName: 'i'
                }
            },
            {
                type: 'warning',
                backgroundColor: '#ffc107',
                icon: {
                    className: 'notyf__icon--warning',
                    tagName: 'i'
                }
            },
            {
                type: 'info',
                backgroundColor: '#17a2b8',
                icon: {
                    className: 'notyf__icon--info',
                    tagName: 'i'
                }
            }
        ]
    };

    /**
     * Singleton Notyf instance
     * Reused across all toast notifications to optimize performance
     * 
     * @type {Notyf|null}
     * @private
     */
    let notyfInstance = null;

    /**
     * Cache of Notyf instances for different positions
     * Allows position override by maintaining separate instances
     * 
     * @type {Object.<string, Notyf>}
     * @private
     */
    const notyfInstanceCache = {};

    /**
     * Initialize the toast notification system
     * Creates a singleton Notyf instance with custom configuration.
     * Uses lazy initialization pattern - instance is created on first use.
     * 
     * Performance Optimization (Requirement 12.5):
     * - Singleton pattern: Reuses the same Notyf instance for all subsequent calls
     * - Instance caching: Maintains separate instances for different positions
     * - Lazy initialization: Creates instance only when first needed
     * 
     * @param {Object} [positionOverride] - Optional position override {x: 'left'|'center'|'right', y: 'top'|'center'|'bottom'}
     * @returns {Notyf|null} Notyf instance or null if library not loaded
     * @throws {Error} Logs error if Notyf library is not available
     * 
     * @example
     * const notyf = ToastUtils.initToastSystem();
     * if (notyf) {
     *   notyf.success('Initialized successfully');
     * }
     */
    function initToastSystem(positionOverride = null) {
        try {
            // Check if Notyf library is available
            if (typeof Notyf === 'undefined') {
                console.error('Notyf library not loaded. Please ensure Notyf is included in your page.');
                return null;
            }

            // Performance Optimization: Return singleton instance immediately if no position override
            // This is the most common case and avoids unnecessary position key generation
            if (!positionOverride) {
                if (notyfInstance) {
                    return notyfInstance;
                }
                
                // Create default singleton instance on first use
                notyfInstance = new Notyf({
                    duration: toastConfig.duration.info,
                    position: toastConfig.position,
                    dismissible: toastConfig.dismissible,
                    ripple: toastConfig.ripple,
                    types: toastConfig.types
                });
                
                // Also cache it with the default position key
                const defaultKey = `${toastConfig.position.x}-${toastConfig.position.y}`;
                notyfInstanceCache[defaultKey] = notyfInstance;
                
                return notyfInstance;
            }

            // Handle position override case
            const position = positionOverride;
            const positionKey = `${position.x}-${position.y}`;
            
            // Return cached instance for this position if it exists
            if (notyfInstanceCache[positionKey]) {
                return notyfInstanceCache[positionKey];
            }

            // Create new Notyf instance with custom position
            const instance = new Notyf({
                duration: toastConfig.duration.info,
                position: position,
                dismissible: toastConfig.dismissible,
                ripple: toastConfig.ripple,
                types: toastConfig.types
            });

            // Cache the instance for this position
            notyfInstanceCache[positionKey] = instance;

            return instance;
        } catch (error) {
            console.error('Error initializing toast system:', error);
            return null;
        }
    }

    /**
     * Show a toast notification
     * Core function for displaying toast notifications with validation and error handling.
     * 
     * @param {string} message - The message to display (required, non-empty)
     * @param {string} [type='info'] - Type of notification: 'success', 'error', 'warning', 'info'
     * @param {Object} [options={}] - Optional configuration overrides
     * @param {number} [options.duration] - Duration in milliseconds (overrides default for type)
     * @param {boolean} [options.dismissible] - Whether toast can be manually dismissed
     * @param {Object} [options.position] - Position override {x: 'left'|'center'|'right', y: 'top'|'center'|'bottom'}
     * 
     * @returns {void}
     * 
     * @example
     * // Basic usage
     * ToastUtils.showToast('Hello World', 'success');
     * 
     * @example
     * // With custom duration
     * ToastUtils.showToast('Processing...', 'info', { duration: 5000 });
     * 
     * @example
     * // With custom position
     * ToastUtils.showToast('Bottom notification', 'warning', { 
     *   position: { x: 'center', y: 'bottom' } 
     * });
     */
    function showToast(message, type = 'info', options = {}) {
        try {
            // Validate message parameter
            if (!message || typeof message !== 'string' || message.trim() === '') {
                console.warn('ToastUtils.showToast: Invalid or empty message provided');
                return;
            }

            // Check if Notyf library is loaded
            if (typeof Notyf === 'undefined') {
                console.error('ToastUtils.showToast: Notyf library not loaded. Message:', message);
                
                // Fallback to browser alert for critical errors
                if (type === 'error') {
                    alert('Error: ' + message);
                }
                return;
            }

            // Initialize toast system if not already done (lazy initialization)
            // Requirement 13.4: Support position override by using appropriate Notyf instance
            const notyf = initToastSystem(options.position || null);
            if (!notyf) {
                console.error('ToastUtils.showToast: Failed to initialize toast system');
                return;
            }

            // Validate and normalize type
            const validTypes = ['success', 'error', 'warning', 'info'];
            if (!validTypes.includes(type)) {
                console.warn(`ToastUtils.showToast: Invalid toast type '${type}'. Defaulting to 'info'`);
                type = 'info';
            }

            // Requirement 13.2: Determine duration (use custom or default)
            // Allow duration override through options parameter
            const duration = options.duration !== undefined ? options.duration : toastConfig.duration[type];

            // Build toast configuration
            const toastOptions = {
                type: type,
                message: message.trim(),
                duration: duration,
                dismissible: options.dismissible !== undefined ? options.dismissible : toastConfig.dismissible
            };

            // Display the toast
            notyf.open(toastOptions);
            
            // Requirement 9.1: Ensure ARIA attributes are present for accessibility
            // Enhancement: Add ARIA attributes if Notyf doesn't include them by default
            setTimeout(() => ensureARIAAttributes(), 100);
            
        } catch (error) {
            // Catch and log any unexpected errors to prevent breaking the application
            console.error('ToastUtils.showToast: Error displaying toast:', error);
        }
    }

    /**
     * Ensure ARIA attributes are present on toast notifications
     * 
     * This function enhances accessibility by ensuring all toast elements have proper ARIA attributes.
     * While Notyf v3 is advertised as A11Y compatible, this function provides an additional layer
     * of assurance that all required ARIA attributes are present.
     * 
     * Requirements 9.1: Toast elements must have:
     * - role="alert" for screen reader announcement
     * - aria-live="polite" or "assertive" for live region behavior
     * - aria-atomic="true" to announce the entire content as a single unit
     * 
     * @private
     * @returns {void}
     */
    function ensureARIAAttributes() {
        try {
            // Find all toast elements
            const toastElements = document.querySelectorAll('.notyf__toast');
            
            toastElements.forEach((toast) => {
                // Ensure role="alert" is present
                if (!toast.hasAttribute('role')) {
                    toast.setAttribute('role', 'alert');
                }
                
                // Ensure aria-live is present (polite for non-critical, assertive for errors)
                if (!toast.hasAttribute('aria-live')) {
                    // Check if this is an error toast (more urgent)
                    const isError = toast.classList.contains('notyf__toast--error') || 
                                   toast.querySelector('.notyf__icon--error');
                    toast.setAttribute('aria-live', isError ? 'assertive' : 'polite');
                }
                
                // Ensure aria-atomic="true" is present
                if (!toast.hasAttribute('aria-atomic')) {
                    toast.setAttribute('aria-atomic', 'true');
                }
                
                // Ensure dismiss button has proper accessibility if present
                const dismissButton = toast.querySelector('.notyf__dismiss');
                if (dismissButton) {
                    if (!dismissButton.hasAttribute('aria-label')) {
                        dismissButton.setAttribute('aria-label', 'Dismiss notification');
                    }
                    if (!dismissButton.hasAttribute('role')) {
                        dismissButton.setAttribute('role', 'button');
                    }
                }
            });
        } catch (error) {
            console.error('ToastUtils.ensureARIAAttributes: Error ensuring ARIA attributes:', error);
        }
    }

    /**
     * Show a success toast notification
     * Convenience method for displaying success messages.
     * 
     * @param {string} message - Success message to display
     * @param {Object} [options={}] - Optional configuration overrides
     * @param {number} [options.duration] - Duration in milliseconds (default: 3000ms)
     * @param {boolean} [options.dismissible] - Whether toast can be manually dismissed
     * @param {Object} [options.position] - Position override {x: 'left'|'center'|'right', y: 'top'|'center'|'bottom'}
     * 
     * @returns {void}
     * 
     * @example
     * ToastUtils.showSuccess('Profile updated successfully!');
     * 
     * @example
     * ToastUtils.showSuccess('Saved!', { duration: 2000 });
     * 
     * @example
     * ToastUtils.showSuccess('Bottom notification', { position: { x: 'center', y: 'bottom' } });
     */
    function showSuccess(message, options = {}) {
        showToast(message, 'success', options);
    }

    /**
     * Show an error toast notification
     * Convenience method for displaying error messages.
     * 
     * @param {string} message - Error message to display
     * @param {Object} [options={}] - Optional configuration overrides
     * @param {number} [options.duration] - Duration in milliseconds (default: 6000ms)
     * @param {boolean} [options.dismissible] - Whether toast can be manually dismissed
     * @param {Object} [options.position] - Position override {x: 'left'|'center'|'right', y: 'top'|'center'|'bottom'}
     * 
     * @returns {void}
     * 
     * @example
     * ToastUtils.showError('Failed to save changes');
     * 
     * @example
     * ToastUtils.showError('Network error', { duration: 8000 });
     */
    function showError(message, options = {}) {
        showToast(message, 'error', options);
    }

    /**
     * Show a warning toast notification
     * Convenience method for displaying warning messages.
     * 
     * @param {string} message - Warning message to display
     * @param {Object} [options={}] - Optional configuration overrides
     * @param {number} [options.duration] - Duration in milliseconds (default: 4500ms)
     * @param {boolean} [options.dismissible] - Whether toast can be manually dismissed
     * @param {Object} [options.position] - Position override {x: 'left'|'center'|'right', y: 'top'|'center'|'bottom'}
     * 
     * @returns {void}
     * 
     * @example
     * ToastUtils.showWarning('This action cannot be undone');
     * 
     * @example
     * ToastUtils.showWarning('Low disk space', { duration: 6000 });
     */
    function showWarning(message, options = {}) {
        showToast(message, 'warning', options);
    }

    /**
     * Show an info toast notification
     * Convenience method for displaying informational messages.
     * 
     * @param {string} message - Info message to display
     * @param {Object} [options={}] - Optional configuration overrides
     * @param {number} [options.duration] - Duration in milliseconds (default: 3500ms)
     * @param {boolean} [options.dismissible] - Whether toast can be manually dismissed
     * @param {Object} [options.position] - Position override {x: 'left'|'center'|'right', y: 'top'|'center'|'bottom'}
     * 
     * @returns {void}
     * 
     * @example
     * ToastUtils.showInfo('New features available');
     * 
     * @example
     * ToastUtils.showInfo('Loading...', { duration: 2000 });
     */
    function showInfo(message, options = {}) {
        showToast(message, 'info', options);
    }

    /**
     * Process Django messages and convert them to toast notifications
     * 
     * Automatically reads messages from the hidden .messages container,
     * converts them to appropriate toast notifications, and removes the container.
     * Uses a guard flag (window._djangoMessagesProcessed) to prevent duplicate processing.
     * 
     * Performance Optimization (Requirement 12.4):
     * - Early exit: Immediately returns if no messages container exists
     * - Early exit: Immediately returns if no alert messages found
     * - Guard flag: Prevents duplicate processing of the same messages
     * - Minimal DOM manipulation: Only processes when messages are present
     * 
     * This function is called automatically on page load and should not be called
     * multiple times for the same page load.
     * 
     * @returns {void}
     * 
     * @example
     * // Typically called automatically, but can be invoked manually if needed
     * ToastUtils.processDjangoMessages();
     * 
     * @see {@link https://docs.djangoproject.com/en/stable/ref/contrib/messages/}
     */
    function processDjangoMessages() {
        try {
            // Guard flag: Prevent duplicate processing
            // This ensures messages are only processed once per page load
            if (window._djangoMessagesProcessed) {
                console.log('ToastUtils.processDjangoMessages: Django messages already processed, skipping duplicate call');
                return;
            }
            
            // Small delay to ensure DOM is fully ready
            // This prevents race conditions with DOM loading
            setTimeout(() => {
                try {
                    // Performance Optimization: Early exit if no messages container exists
                    // This avoids unnecessary DOM manipulation when there are no messages
                    const messagesContainer = document.querySelector('.messages');
                    
                    if (!messagesContainer) {
                        console.log('ToastUtils.processDjangoMessages: No messages container found');
                        return;
                    }
                    
                    // Set guard flag BEFORE processing to prevent race conditions
                    // This is critical for preventing duplicate processing
                    window._djangoMessagesProcessed = true;
                    
                    // Find all alert elements within the container
                    const alerts = messagesContainer.querySelectorAll('.alert');
                    
                    // Performance Optimization: Early exit if no alerts found
                    // This avoids unnecessary processing when the container is empty
                    if (alerts.length === 0) {
                        console.log('ToastUtils.processDjangoMessages: No alert messages found');
                        return;
                    }
                    
                    // Process each alert message
                    alerts.forEach((alert, index) => {
                        try {
                            // Extract message text
                            const messageText = alert.textContent.trim();
                            
                            // Skip empty messages
                            if (!messageText) {
                                console.warn(`ToastUtils.processDjangoMessages: Skipping empty message at index ${index}`);
                                return;
                            }
                            
                            // Determine message type from CSS classes
                            // Maps Django message tags to toast types
                            let type = 'info'; // Default type
                            
                            if (alert.classList.contains('alert-success')) {
                                type = 'success';
                            } else if (alert.classList.contains('alert-danger') || 
                                       alert.classList.contains('alert-error')) {
                                type = 'error';
                            } else if (alert.classList.contains('alert-warning')) {
                                type = 'warning';
                            } else if (alert.classList.contains('alert-info')) {
                                type = 'info';
                            }
                            
                            // Display the toast notification
                            showToast(messageText, type);
                            
                        } catch (error) {
                            // Log error but continue processing other messages
                            console.error(`ToastUtils.processDjangoMessages: Error processing message at index ${index}:`, error);
                        }
                    });
                    
                    // Remove messages container from DOM after processing
                    // This prevents the messages from being visible in the page
                    messagesContainer.remove();
                    
                    console.log(`ToastUtils.processDjangoMessages: Successfully processed ${alerts.length} message(s)`);
                    
                } catch (error) {
                    // Log error and reset guard flag to allow retry
                    console.error('ToastUtils.processDjangoMessages: Error in setTimeout callback:', error);
                    window._djangoMessagesProcessed = false;
                }
            }, 50); // 50ms delay to ensure DOM is ready
            
        } catch (error) {
            // Catch any unexpected errors in the outer try block
            console.error('ToastUtils.processDjangoMessages: Unexpected error:', error);
            // Reset guard flag on error to allow retry
            window._djangoMessagesProcessed = false;
        }
    }

    /**
     * Public API
     * Exported functions available via window.ToastUtils namespace
     * 
     * @namespace ToastUtils
     * @property {Function} initToastSystem - Initialize the Notyf instance
     * @property {Function} showToast - Display a toast notification
     * @property {Function} showSuccess - Display a success toast
     * @property {Function} showError - Display an error toast
     * @property {Function} showWarning - Display a warning toast
     * @property {Function} showInfo - Display an info toast
     * @property {Function} processDjangoMessages - Process Django messages as toasts
     */
    window.ToastUtils = {
        initToastSystem: initToastSystem,
        showToast: showToast,
        showSuccess: showSuccess,
        showError: showError,
        showWarning: showWarning,
        showInfo: showInfo,
        processDjangoMessages: processDjangoMessages
    };

    /**
     * Backward compatibility alias
     * Allows legacy code to call window.processDjangoMessages() directly
     * 
     * @deprecated Use ToastUtils.processDjangoMessages() instead
     * @function processDjangoMessages
     * @memberof window
     */
    window.processDjangoMessages = processDjangoMessages;

    /**
     * Process Django messages in HTMX swapped content
     * 
     * This function is called after HTMX swaps content into the page.
     * It looks for Django messages in the swapped content and converts them to toasts.
     * Unlike the main processDjangoMessages function, this does NOT use the guard flag
     * because HTMX responses may contain new messages that need to be processed.
     * 
     * Performance Optimization (Requirement 12.4):
     * - Early exit: Immediately returns if no messages container exists
     * - Early exit: Immediately returns if no alert messages found
     * - Minimal DOM manipulation: Only processes when messages are present
     * 
     * @param {HTMLElement} swappedElement - The element that was swapped by HTMX
     * @returns {void}
     * 
     * @example
     * // Called automatically by HTMX afterSwap event
     * document.addEventListener('htmx:afterSwap', function(event) {
     *   processHtmxMessages(event.detail.target);
     * });
     */
    function processHtmxMessages(swappedElement) {
        try {
            // Performance Optimization: Early exit if no messages container exists
            // This avoids unnecessary DOM manipulation when there are no messages
            const messagesContainer = swappedElement.querySelector('.messages');
            
            if (!messagesContainer) {
                return;
            }
            
            // Find all alert elements within the container
            const alerts = messagesContainer.querySelectorAll('.alert');
            
            // Performance Optimization: Early exit if no alerts found
            // This avoids unnecessary processing when the container is empty
            if (alerts.length === 0) {
                return;
            }
            
            console.log(`ToastUtils.processHtmxMessages: Processing ${alerts.length} message(s) from HTMX swap`);
            
            // Process each alert message
            alerts.forEach((alert, index) => {
                try {
                    // Extract message text
                    const messageText = alert.textContent.trim();
                    
                    // Skip empty messages
                    if (!messageText) {
                        console.warn(`ToastUtils.processHtmxMessages: Skipping empty message at index ${index}`);
                        return;
                    }
                    
                    // Determine message type from CSS classes
                    let type = 'info'; // Default type
                    
                    if (alert.classList.contains('alert-success')) {
                        type = 'success';
                    } else if (alert.classList.contains('alert-danger') || 
                               alert.classList.contains('alert-error')) {
                        type = 'error';
                    } else if (alert.classList.contains('alert-warning')) {
                        type = 'warning';
                    } else if (alert.classList.contains('alert-info')) {
                        type = 'info';
                    }
                    
                    // Display the toast notification
                    showToast(messageText, type);
                    
                } catch (error) {
                    // Log error but continue processing other messages
                    console.error(`ToastUtils.processHtmxMessages: Error processing message at index ${index}:`, error);
                }
            });
            
            // Remove messages container from DOM after processing
            messagesContainer.remove();
            
            console.log(`ToastUtils.processHtmxMessages: Successfully processed ${alerts.length} message(s) from HTMX swap`);
            
        } catch (error) {
            console.error('ToastUtils.processHtmxMessages: Error processing HTMX messages:', error);
        }
    }

    /**
     * Initialize HTMX integration
     * Sets up event listener for HTMX afterSwap events to automatically process Django messages
     * 
     * @returns {void}
     * @private
     */
    function initHtmxIntegration() {
        // Check if HTMX is loaded
        if (typeof htmx === 'undefined') {
            console.log('ToastUtils: HTMX not loaded, skipping HTMX integration');
            return;
        }
        
        // Listen for HTMX afterSwap events
        document.addEventListener('htmx:afterSwap', function(event) {
            // Process any Django messages in the swapped content
            if (event.detail && event.detail.target) {
                processHtmxMessages(event.detail.target);
            }
        });
        
        console.log('ToastUtils: HTMX integration initialized');
    }

    // Initialize HTMX integration when the script loads
    // This ensures HTMX messages are processed even if HTMX loads after this script
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initHtmxIntegration);
    } else {
        // DOM already loaded, initialize immediately
        initHtmxIntegration();
    }

})();
