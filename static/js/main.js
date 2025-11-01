/**
 * NORSU Alumni System - Main JavaScript Module
 * Handles core functionality including CSRF setup, toasts, and utilities
 */

// Namespace for the application
window.NORSUAlumni = window.NORSUAlumni || {};

(function(app) {
    'use strict';

    // Configuration
    app.config = {
        toastDuration: 5000,
        locationUpdateInterval: 300000, // 5 minutes
        locationUpdateDelay: 3000 // 3 seconds after page load
    };

    // Utility functions
    app.utils = {
        /**
         * Get cookie value by name
         * @param {string} name - Cookie name
         * @returns {string|null} Cookie value or null
         */
        getCookie: function(name) {
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
        },

        /**
         * Debounce function to limit function calls
         * @param {Function} func - Function to debounce
         * @param {number} wait - Wait time in milliseconds
         * @returns {Function} Debounced function
         */
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Throttle function to limit function calls
         * @param {Function} func - Function to throttle
         * @param {number} limit - Time limit in milliseconds
         * @returns {Function} Throttled function
         */
        throttle: function(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        /**
         * Check if user prefers reduced motion
         * @returns {boolean} True if reduced motion is preferred
         */
        prefersReducedMotion: function() {
            return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        },

        /**
         * Generate unique ID
         * @returns {string} Unique ID
         */
        generateId: function() {
            return 'id-' + Math.random().toString(36).substr(2, 9);
        }
    };

    // CSRF Token Management
    app.csrf = {
        token: null,

        /**
         * Initialize CSRF token
         */
        init: function() {
            this.token = app.utils.getCookie('csrftoken');
            this.setupAjax();
        },

        /**
         * Setup AJAX requests with CSRF token
         */
        setupAjax: function() {
            if (typeof $ !== 'undefined') {
                $.ajaxSetup({
                    beforeSend: (xhr, settings) => {
                        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !settings.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", this.token);
                        }
                    }
                });
            }
        },

        /**
         * Get CSRF token for fetch requests
         * @returns {string} CSRF token
         */
        getToken: function() {
            return this.token;
        }
    };

    // Toast Notification System
    app.toast = {
        container: null,
        toasts: [],

        /**
         * Initialize toast system
         */
        init: function() {
            this.createContainer();
            this.initializeExistingToasts();
        },

        /**
         * Create toast container if it doesn't exist
         */
        createContainer: function() {
            this.container = document.getElementById('toast-container');
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'toast-container';
                this.container.className = 'toast-container';
                this.container.setAttribute('aria-live', 'polite');
                this.container.setAttribute('aria-atomic', 'true');
                document.body.appendChild(this.container);
            }
        },

        /**
         * Initialize existing toasts on page load
         */
        initializeExistingToasts: function() {
            const existingToasts = document.querySelectorAll('.toast');
            existingToasts.forEach(toastEl => {
                this.initializeToast(toastEl);
            });
        },

        /**
         * Initialize a single toast element
         * @param {HTMLElement} toastEl - Toast element
         */
        initializeToast: function(toastEl) {
            const toast = new bootstrap.Toast(toastEl, {
                animation: !app.utils.prefersReducedMotion(),
                autohide: true,
                delay: app.config.toastDuration
            });

            // Add to tracking array
            this.toasts.push(toast);

            // Show the toast
            toast.show();

            // Add fade-out animation
            toastEl.addEventListener('hide.bs.toast', function() {
                if (!app.utils.prefersReducedMotion()) {
                    this.style.transition = 'opacity 0.5s ease-out';
                    this.style.opacity = '0';
                }
            });

            // Remove from tracking when hidden
            toastEl.addEventListener('hidden.bs.toast', () => {
                const index = this.toasts.indexOf(toast);
                if (index > -1) {
                    this.toasts.splice(index, 1);
                }
                toastEl.remove();
            });
        },

        /**
         * Show a new toast notification
         * @param {string} message - Toast message
         * @param {string} type - Toast type (success, danger, warning, info)
         * @param {Object} options - Additional options
         */
        show: function(message, type = 'info', options = {}) {
            const toastEl = this.createToastElement(message, type, options);
            this.container.appendChild(toastEl);
            this.initializeToast(toastEl);
        },

        /**
         * Create toast element
         * @param {string} message - Toast message
         * @param {string} type - Toast type
         * @param {Object} options - Additional options
         * @returns {HTMLElement} Toast element
         */
        createToastElement: function(message, type, options) {
            const toastEl = document.createElement('div');
            toastEl.className = `toast bg-${type}`;
            toastEl.setAttribute('role', 'alert');
            toastEl.setAttribute('aria-live', 'assertive');
            toastEl.setAttribute('aria-atomic', 'true');

            const icon = this.getTypeIcon(type);
            const title = options.title || this.getTypeTitle(type);

            toastEl.innerHTML = `
                ${options.showHeader !== false ? `
                    <div class="toast-header">
                        <i class="${icon} toast-icon"></i>
                        <strong class="toast-title">${title}</strong>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                ` : ''}
                <div class="toast-body">
                    ${options.showIcon !== false && options.showHeader === false ? `<i class="${icon} toast-icon"></i>` : ''}
                    <div class="toast-message">${message}</div>
                    ${options.actions ? this.createActions(options.actions) : ''}
                </div>
            `;

            return toastEl;
        },

        /**
         * Get icon for toast type
         * @param {string} type - Toast type
         * @returns {string} Icon class
         */
        getTypeIcon: function(type) {
            const icons = {
                success: 'fas fa-check-circle',
                danger: 'fas fa-exclamation-circle',
                warning: 'fas fa-exclamation-triangle',
                info: 'fas fa-info-circle',
                primary: 'fas fa-bell'
            };
            return icons[type] || icons.info;
        },

        /**
         * Get title for toast type
         * @param {string} type - Toast type
         * @returns {string} Title
         */
        getTypeTitle: function(type) {
            const titles = {
                success: 'Success',
                danger: 'Error',
                warning: 'Warning',
                info: 'Information',
                primary: 'Notification'
            };
            return titles[type] || titles.info;
        },

        /**
         * Create action buttons for toast
         * @param {Array} actions - Array of action objects
         * @returns {string} Actions HTML
         */
        createActions: function(actions) {
            if (!actions || !actions.length) return '';
            
            const actionsHtml = actions.map(action => 
                `<button type="button" class="btn ${action.class || 'btn-outline-light'}" onclick="${action.onclick}">
                    ${action.text}
                </button>`
            ).join('');
            
            return `<div class="toast-actions">${actionsHtml}</div>`;
        }
    };

    // Bootstrap Components Initialization
    app.bootstrap = {
        /**
         * Initialize all Bootstrap components
         */
        init: function() {
            this.initTooltips();
            this.initPopovers();
        },

        /**
         * Initialize tooltips
         */
        initTooltips: function() {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl, {
                    animation: !app.utils.prefersReducedMotion()
                });
            });
        },

        /**
         * Initialize popovers
         */
        initPopovers: function() {
            const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl, {
                    animation: !app.utils.prefersReducedMotion()
                });
            });
        }
    };

    // Application Initialization
    app.init = function() {
        // Initialize core modules
        this.csrf.init();
        
        // Expose CSRF token globally for other scripts
        window.csrftoken = this.csrf.getToken();
        
        // Check if toast component is defined before initializing
        if (this.toast) {
            this.toast.init();
        } else {
            console.warn('Toast component not defined');
        }
        
        // Check if bootstrap component is defined before initializing
        if (this.bootstrap) {
            this.bootstrap.init();
        } else {
            console.warn('Bootstrap component not defined');
        }

        // Initialize location tracking for authenticated users
        if (document.querySelector('meta[name="user-id"]') && this.location) {
            console.log('Initializing location tracking via main.js');
            this.location.init();
        } else {
            if (!document.querySelector('meta[name="user-id"]')) {
                console.log('User not authenticated - skipping location tracking');
            } else if (!this.location) {
                console.warn('Location module not found - make sure location.js is loaded');
            }
        }

        // Initialize sidebar for superusers
        if (document.getElementById('sidebar') && this.sidebar) {
            this.sidebar.init();
        }

        console.log('NORSU Alumni System initialized');
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => app.init());
    } else {
        app.init();
    }

})(window.NORSUAlumni);

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.NORSUAlumni;
}