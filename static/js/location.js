/**
 * NORSU Alumni System - Location Tracking Module
 * Handles geolocation tracking and updates
 */

(function(app) {
    'use strict';

    // Location tracking module
    app.location = {
        isTracking: false,
        watchId: null,
        lastUpdate: null,
        updateInterval: null,
        hasOptedOut: false,

        /**
         * Initialize location tracking
         */
        init: function() {
            // Check if user has opted out
            this.hasOptedOut = localStorage.getItem('locationOptOut') === 'true';
            
            if (this.hasOptedOut) {
                console.log('Location tracking disabled by user preference');
                return;
            }

            // Check if geolocation is supported
            if (!navigator.geolocation) {
                console.warn('Geolocation is not supported by this browser');
                return;
            }

            // Start tracking after delay
            setTimeout(() => {
                this.requestPermission();
            }, app.config.locationUpdateDelay);
        },

        /**
         * Request geolocation permission
         */
        requestPermission: function() {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.onLocationSuccess(position);
                    this.startTracking();
                },
                (error) => {
                    this.onLocationError(error);
                },
                {
                    enableHighAccuracy: false,
                    timeout: 10000,
                    maximumAge: 300000 // 5 minutes
                }
            );
        },

        /**
         * Start continuous location tracking
         */
        startTracking: function() {
            if (this.isTracking) return;

            this.isTracking = true;
            
            // Set up periodic updates
            this.updateInterval = setInterval(() => {
                this.getCurrentLocation();
            }, app.config.locationUpdateInterval);

            console.log('Location tracking started');
        },

        /**
         * Stop location tracking
         */
        stopTracking: function() {
            if (!this.isTracking) return;

            this.isTracking = false;

            if (this.watchId) {
                navigator.geolocation.clearWatch(this.watchId);
                this.watchId = null;
            }

            if (this.updateInterval) {
                clearInterval(this.updateInterval);
                this.updateInterval = null;
            }

            console.log('Location tracking stopped');
        },

        /**
         * Get current location
         */
        getCurrentLocation: function() {
            if (!navigator.geolocation || this.hasOptedOut) return;

            navigator.geolocation.getCurrentPosition(
                (position) => this.onLocationSuccess(position),
                (error) => this.onLocationError(error),
                {
                    enableHighAccuracy: false,
                    timeout: 10000,
                    maximumAge: 300000 // 5 minutes
                }
            );
        },

        /**
         * Handle successful location retrieval
         * @param {GeolocationPosition} position - Position object
         */
        onLocationSuccess: function(position) {
            const { latitude, longitude } = position.coords;
            const timestamp = new Date().toISOString();

            // Avoid sending duplicate locations
            if (this.lastUpdate && 
                Math.abs(this.lastUpdate.latitude - latitude) < 0.001 && 
                Math.abs(this.lastUpdate.longitude - longitude) < 0.001) {
                return;
            }

            this.lastUpdate = { latitude, longitude, timestamp };
            this.sendLocationUpdate(latitude, longitude);
        },

        /**
         * Handle location error
         * @param {GeolocationPositionError} error - Error object
         */
        onLocationError: function(error) {
            let message = 'Location access denied';
            let shouldShowNotification = false;

            switch (error.code) {
                case error.PERMISSION_DENIED:
                    message = 'Location access denied. You can enable it in your browser settings.';
                    shouldShowNotification = true;
                    this.stopTracking();
                    break;
                case error.POSITION_UNAVAILABLE:
                    message = 'Location information unavailable';
                    console.warn('Location unavailable:', error.message);
                    break;
                case error.TIMEOUT:
                    message = 'Location request timed out';
                    console.warn('Location timeout:', error.message);
                    break;
                default:
                    message = 'An unknown error occurred while retrieving location';
                    console.error('Location error:', error.message);
                    break;
            }

            if (shouldShowNotification) {
                this.showLocationNotification(message, 'warning');
            }
        },

        /**
         * Send location update to server
         * @param {number} latitude - Latitude
         * @param {number} longitude - Longitude
         */
        sendLocationUpdate: function(latitude, longitude) {
            const updateUrl = document.querySelector('meta[name="location-update-url"]')?.content;
            if (!updateUrl) {
                console.error('Location update URL not found');
                return;
            }

            const data = {
                latitude: latitude,
                longitude: longitude,
                timestamp: new Date().toISOString()
            };

            // Get CSRF token from NORSUAlumni or window.csrftoken
            const csrfToken = (window.NORSUAlumni && window.NORSUAlumni.csrf && window.NORSUAlumni.csrf.getToken()) 
                || window.csrftoken 
                || (window.app && window.app.csrf && window.app.csrf.getToken())
                || null;
            
            if (!csrfToken) {
                console.error('CSRF token not available for location update');
                return;
            }
            
            fetch(updateUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data),
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success || data.status === 'success') {
                    console.log('Location updated successfully:', data.message || 'OK');
                } else {
                    console.error('Location update failed:', data.message || data.error || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error updating location:', error);
                // Don't show error to user for background updates
            });
        },

        /**
         * Show location-related notification
         * @param {string} message - Notification message
         * @param {string} type - Notification type
         */
        showLocationNotification: function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `location-notification location-notification-${type}`;
            notification.innerHTML = `
                <div class="location-notification-content">
                    <i class="fas fa-map-marker-alt location-notification-icon"></i>
                    <span class="location-notification-message">${message}</span>
                    <button class="location-notification-close" onclick="this.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="location-notification-actions">
                    <button class="btn btn-sm btn-outline-light" onclick="NORSUAlumni.location.optOut()">
                        Disable Location
                    </button>
                </div>
            `;

            // Add animation class if motion is not reduced
            if (!app.utils.prefersReducedMotion()) {
                notification.classList.add('location-notification-slide-in');
            }

            document.body.appendChild(notification);

            // Auto-remove after 10 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    if (!app.utils.prefersReducedMotion()) {
                        notification.classList.add('location-notification-slide-out');
                        setTimeout(() => notification.remove(), 300);
                    } else {
                        notification.remove();
                    }
                }
            }, 10000);
        },

        /**
         * Allow user to opt out of location tracking
         */
        optOut: function() {
            this.hasOptedOut = true;
            localStorage.setItem('locationOptOut', 'true');
            this.stopTracking();

            // Remove any existing location notifications
            const notifications = document.querySelectorAll('.location-notification');
            notifications.forEach(notification => notification.remove());

            // Show confirmation
            if (app.toast) {
                app.toast.show(
                    'Location tracking has been disabled. You can re-enable it by clearing your browser data.',
                    'info',
                    { title: 'Location Tracking Disabled' }
                );
            }

            console.log('User opted out of location tracking');
        },

        /**
         * Allow user to opt back in to location tracking
         */
        optIn: function() {
            this.hasOptedOut = false;
            localStorage.removeItem('locationOptOut');
            
            // Show confirmation
            if (app.toast) {
                app.toast.show(
                    'Location tracking has been enabled. Refresh the page to start tracking.',
                    'success',
                    { title: 'Location Tracking Enabled' }
                );
            }

            console.log('User opted in to location tracking');
        },

        /**
         * Get current tracking status
         * @returns {Object} Status object
         */
        getStatus: function() {
            return {
                isTracking: this.isTracking,
                hasOptedOut: this.hasOptedOut,
                lastUpdate: this.lastUpdate,
                isSupported: !!navigator.geolocation
            };
        }
    };

    // Attach to both app and NORSUAlumni namespaces for compatibility
    window.app = window.app || {};
    window.app.location = app.location;
    
    // Also attach to NORSUAlumni namespace (used by main.js)
    window.NORSUAlumni = window.NORSUAlumni || {};
    window.NORSUAlumni.location = app.location;

    // Expose opt-out function globally for easy access
    window.optOutLocation = function() {
        app.location.optOut();
    };

    window.optInLocation = function() {
        app.location.optIn();
    };

})(window.app || {});