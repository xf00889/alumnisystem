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
        
        // Initialize Bootstrap components
        this.bootstrap.init();

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