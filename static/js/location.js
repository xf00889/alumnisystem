/**
 * Verified-alumni, voluntary location sharing.
 * Browser geolocation permission is NOT proof that Django saved a position.
 * Sharing is reported as ON only after the server acknowledges an update.
 */
(function (app) {
    'use strict';

    const $ = (id) => document.getElementById(id);
    const meta = (name) => document.querySelector(`meta[name="${name}"]`)?.content || '';

    const location = {
        isInitialized: false,
        isTracking: false,
        hasOptedOut: true,
        lastUpdate: null,
        pendingLocationUpdate: null,
        updateInterval: null,
        serverHasLocation: false,
        serverStatusKnown: false,
        consentKey: null,
        busy: false,
        message: '',
        state: 'off',
        requestVersion: 0,
        dismissedForVisit: false,

        getCsrfToken() {
            // The template token also works when CSRF_COOKIE_HTTPONLY is enabled.
            return app.csrf?.getToken?.() || meta('csrf-token') ||
                document.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
        },
        getConsent() {
            try { return localStorage.getItem(this.consentKey) === 'enabled'; }
            catch (_) { return false; }
        },
        setConsent(enabled) {
            try {
                if (enabled) localStorage.setItem(this.consentKey, 'enabled');
                else localStorage.removeItem(this.consentKey);
            } catch (_) { /* Private browsing may disable localStorage. */ }
            this.hasOptedOut = !enabled;
        },
        init() {
            if (this.isInitialized) return;
            this.isInitialized = true;
            if (!meta('user-id') || meta('alumni-location-eligible') !== 'true' || meta('alumni-location-control') !== 'dashboard') return;
            this.consentKey = `norsuLocationShare:${meta('user-id')}`;
            this.hasOptedOut = !this.getConsent();
            this.renderSharingControl();
            // Display the current server state; GPS is requested ONLY after
            // the alumnus explicitly clicks Share location on this dashboard.
            // A stale browser permission/denial must not auto-retry on page load.
            this.refreshServerStatus();
            // Returning to this page from the back/forward cache is a new visit.
            window.addEventListener('pageshow', (event) => {
                if (event.persisted) {
                    this.dismissedForVisit = false;
                    this.renderSharingControl();
                }
            });
            window.addEventListener('storage', (event) => {
                if (event.key === this.consentKey && event.newValue !== 'enabled') {
                    this.hasOptedOut = true;
                    this.stopTracking();
                    this.renderSharingControl();
                    this.refreshServerStatus();
                }
            });
        },
        async refreshServerStatus() {
            const url = meta('location-status-url');
            if (!url) {
                this.message = 'Unable to check saved location status. Refresh the page.';
                this.renderSharingControl();
                return;
            }
            try {
                const response = await fetch(url, {credentials: 'same-origin', cache: 'no-store'});
                if (!response.ok) throw new Error('Location status unavailable');
                const payload = await response.json();
                if (!payload.eligible) {
                    this.setConsent(false);
                    this.stopTracking();
                    this.state = 'error';
                    this.message = 'Only verified alumni can share a location.';
                }
                this.serverHasLocation = !!payload.has_active_location;
                this.serverStatusKnown = true;
                if (!this.busy && this.state !== 'error') this.state = this.serverHasLocation && !this.hasOptedOut ? 'active' : 'off';
            } catch (_) {
                this.serverStatusKnown = false;
                this.message = 'Cannot verify your saved pin right now. Check your connection.';
            }
            this.renderSharingControl();
        },
        renderSharingControl() {
            if (!this.consentKey) return;
            let container = $('alumniLocationSharing');
            if (!container) {
                container = document.createElement('aside');
                container.id = 'alumniLocationSharing';
                container.className = 'alumni-location-sharing';
                container.setAttribute('aria-label', 'Alumni location sharing');
                const dismiss = document.createElement('button');
                dismiss.type = 'button';
                dismiss.className = 'alumni-location-sharing__dismiss';
                dismiss.setAttribute('aria-label', 'Dismiss location sharing notice');
                dismiss.title = 'Dismiss for this visit';
                dismiss.textContent = '×';
                dismiss.addEventListener('click', () => {
                    // Dismisses the UI only. It never changes consent or tracking.
                    this.dismissedForVisit = true;
                    container.hidden = true;
                });
                const status = document.createElement('div');
                status.className = 'alumni-location-sharing__copy';
                const line = document.createElement('span');
                line.id = 'alumniLocationSharingStatus';
                line.setAttribute('role', 'status');
                line.setAttribute('aria-live', 'polite');
                const detail = document.createElement('small');
                detail.id = 'alumniLocationSharingDetail';
                detail.className = 'alumni-location-sharing__detail';
                status.append(line, detail);
                const actions = document.createElement('div');
                actions.className = 'alumni-location-sharing__actions';
                const button = document.createElement('button');
                button.type = 'button';
                button.id = 'alumniLocationSharingToggle';
                button.className = 'alumni-location-sharing__button';
                button.addEventListener('click', () => {
                    if (this.state === 'error' && !this.hasOptedOut) this.acquireAndShare();
                    else if (this.hasOptedOut) this.optIn();
                    else this.optOut();
                });
                const remove = document.createElement('button');
                remove.type = 'button';
                remove.id = 'alumniLocationRemoveSaved';
                remove.className = 'alumni-location-sharing__remove';
                remove.addEventListener('click', () => this.optOut());
                actions.append(button, remove);
                container.append(status, actions, dismiss);
                const mount = $('alumniLocationSharingMount');
                if (mount) mount.appendChild(container);
                else document.body.appendChild(container);
            }
            const active = this.state === 'active' && this.serverHasLocation && !this.hasOptedOut;
            const pending = this.state === 'requesting' || this.state === 'saving' || this.state === 'stopping';
            const label = this.state === 'requesting' ? 'Getting your GPS position…'
                : this.state === 'saving' ? 'Saving location to alumni map…'
                : this.state === 'stopping' ? 'Removing saved location…'
                : active ? 'Location sharing ON — saved to the alumni map.'
                : this.serverHasLocation ? 'A previously shared location is still on the alumni map.'
                : 'Location sharing OFF — no active pin confirmed.';
            $('alumniLocationSharingStatus').textContent = label;
            $('alumniLocationSharingDetail').textContent = this.message ||
                (active ? 'Staff can see your last-shared location. This is not live tracking.'
                    : 'Browser permission alone does not save a location.');
            const toggle = $('alumniLocationSharingToggle');
            toggle.textContent = this.state === 'requesting' ? 'Locating…'
                : this.state === 'saving' ? 'Saving…'
                : this.hasOptedOut ? 'Share location' : (this.state === 'error' ? 'Retry location' : 'Stop sharing');
            toggle.disabled = pending;
            const remove = $('alumniLocationRemoveSaved');
            remove.hidden = pending || !(this.serverHasLocation && this.hasOptedOut);
            remove.disabled = pending;
            remove.textContent = 'Remove saved pin';
            container.dataset.state = this.state;
            // Background GPS/status updates must not reopen a dismissed notice.
            container.hidden = this.dismissedForVisit;
        },
        requestPermission() {
            if (!this.hasOptedOut && navigator.geolocation) this.acquireAndShare();
        },
        optIn() {
            if (this.busy || !this.consentKey) return;
            if (!navigator.geolocation) {
                this.message = 'Geolocation is not supported in this browser.';
                this.state = 'error';
                this.renderSharingControl();
                return;
            }
            if (!window.isSecureContext) {
                this.message = 'Location access needs HTTPS or localhost.';
                this.state = 'error';
                this.renderSharingControl();
                return;
            }
            this.acquireAndShare();
        },
        acquireAndShare() {
            if (this.busy) return;
            const version = ++this.requestVersion;
            this.busy = true;
            this.state = 'requesting';
            this.message = 'Allow location access and wait for the GPS position.';
            this.renderSharingControl();
            navigator.geolocation.getCurrentPosition(async (position) => {
                if (version !== this.requestVersion) return;
                this.state = 'saving';
                this.message = 'GPS permission granted. Waiting for Django to save your pin.';
                this.renderSharingControl();
                const saved = await this.sendLocationUpdate(position.coords.latitude, position.coords.longitude);
                if (version !== this.requestVersion) return;
                this.busy = false;
                if (saved) {
                    this.setConsent(true);
                    this.serverHasLocation = true;
                    this.serverStatusKnown = true;
                    this.lastUpdate = {latitude: position.coords.latitude, longitude: position.coords.longitude, timestamp: Date.now()};
                    this.message = 'Your location was saved successfully. Staff may need to refresh the map.';
                    this.state = 'active';
                    this.startTracking();
                } else {
                    this.setConsent(false);
                    this.state = 'error';
                }
                this.renderSharingControl();
            }, (error) => {
                if (version !== this.requestVersion) return;
                this.busy = false;
                this.setConsent(false);
                this.onLocationError(error);
                this.state = 'error';
                this.renderSharingControl();
            }, {enableHighAccuracy: true, timeout: 20000, maximumAge: 0});
        },
        async sendLocationUpdate(latitude, longitude) {
            const url = meta('location-update-url');
            const token = this.getCsrfToken();
            if (!url || !token) {
                this.message = 'Security token unavailable. Reload the page and try again.';
                return false;
            }
            try {
                const pending = fetch(url, {
                    method: 'POST', credentials: 'same-origin',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': token},
                    body: JSON.stringify({latitude, longitude})
                });
                this.pendingLocationUpdate = pending;
                const response = await pending;
                const payload = await response.json().catch(() => ({}));
                if (!response.ok || !(payload.success || payload.status === 'success')) {
                    this.message = payload.message || (
                        response.status === 403 ? 'Your account may not be verified, or the security token has expired. Reload and try again.' :
                        response.status === 401 ? 'Your session expired. Please sign in again.' :
                        `The server rejected this location (HTTP ${response.status}).`
                    );
                    return false;
                }
                return true;
            } catch (_) {
                this.message = 'Cannot save your location. Check your internet connection and retry.';
                return false;
            } finally {
                this.pendingLocationUpdate = null;
            }
        },
        startTracking() {
            if (this.isTracking || this.hasOptedOut) return;
            this.isTracking = true;
            this.updateInterval = setInterval(() => this.getCurrentLocation(),
                app.config?.locationUpdateInterval || 300000);
        },
        stopTracking() {
            this.isTracking = false;
            if (this.updateInterval) clearInterval(this.updateInterval);
            this.updateInterval = null;
        },
        getCurrentLocation() {
            if (this.hasOptedOut || this.busy || !navigator.geolocation) return;
            navigator.geolocation.getCurrentPosition((position) => this.onLocationSuccess(position),
                (error) => this.onLocationError(error),
                {enableHighAccuracy: true, timeout: 20000, maximumAge: 60000});
        },
        async onLocationSuccess(position) {
            if (this.hasOptedOut || this.busy) return;
            const {latitude, longitude} = position.coords;
            if (this.lastUpdate && Date.now() - this.lastUpdate.timestamp < 240000 &&
                Math.abs(latitude - this.lastUpdate.latitude) < .001 &&
                Math.abs(longitude - this.lastUpdate.longitude) < .001) return;
            this.busy = true;
            const saved = await this.sendLocationUpdate(latitude, longitude);
            this.busy = false;
            if (this.hasOptedOut) return;
            if (saved) {
                this.lastUpdate = {latitude, longitude, timestamp: Date.now()};
                this.serverHasLocation = true;
                this.state = 'active';
                this.message = '';
            } else {
                this.state = 'error';
                this.stopTracking();
                this.message += ' Retry sharing to re-enable updates.';
            }
            this.renderSharingControl();
        },
        onLocationError(error) {
            const code = error?.code;
            this.message = code === 1 ? 'GPS was denied by the browser or device. Check site settings and operating-system location services, then retry.' :
                code === 2 ? 'Browser permission may be allowed, but a GPS position is unavailable. Check device location services.' :
                code === 3 ? 'The GPS request timed out. Move to an open area and retry.' :
                'Could not get your location. Please retry.';
            if (code === 1) {
                this.stopTracking();
                this.setConsent(false);
                // Brave/browser site permission can be granted while the OS or
                // geolocation provider still refuses to return coordinates.
                // Distinguish those cases instead of incorrectly blaming site permissions.
                if (navigator.permissions?.query) {
                    navigator.permissions.query({name:'geolocation'}).then(result => {
                        if (result.state === 'granted' && this.state === 'error') {
                            this.message = 'Site permission is allowed, but the browser or device could not supply GPS coordinates. Check OS Location Services, browser privacy protections, and try again.';
                            this.renderSharingControl();
                        }
                    }).catch(() => {});
                }
            }
            this.renderSharingControl();
        },
        async optOut() {
            if (this.busy) return;
            ++this.requestVersion;
            this.setConsent(false);
            this.stopTracking();
            this.busy = true;
            this.state = 'stopping';
            this.message = '';
            this.renderSharingControl();
            if (this.pendingLocationUpdate) {
                try { await this.pendingLocationUpdate; } catch (_) { /* Still attempt to revoke. */ }
            }
            const url = meta('location-stop-url');
            const token = this.getCsrfToken();
            try {
                if (!url || !token) throw new Error('Security token missing');
                const response = await fetch(url, {
                    method: 'POST', credentials: 'same-origin',
                    headers: {'X-CSRFToken': token, 'Content-Type': 'application/json'},
                    body: '{}'
                });
                if (!response.ok) throw new Error('Removal not confirmed');
                this.serverHasLocation = false;
                this.lastUpdate = null;
                this.message = 'Your previously shared pin was removed from the active map.';
                this.state = 'off';
            } catch (_) {
                this.message = 'Sharing stopped on this browser, but the saved pin may still be visible. Select Remove saved pin to retry.';
                this.state = 'error';
            }
            this.busy = false;
            this.renderSharingControl();
        },
        showLocationNotification(message) {
            this.message = message;
            this.renderSharingControl();
        },
        getStatus() {
            return {isTracking: this.isTracking, hasOptedOut: this.hasOptedOut,
                lastUpdate: this.lastUpdate, serverHasLocation: this.serverHasLocation,
                isSupported: !!navigator.geolocation};
        }
    };

    app.location = location;
    window.NORSUAlumni = window.NORSUAlumni || app;
    window.NORSUAlumni.location = location;
    window.app = window.app || {};
    window.app.location = location;
    window.optOutLocation = () => location.optOut();
    const initialize = () => location.init();
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
    else initialize();
})(window.NORSUAlumni = window.NORSUAlumni || {});
