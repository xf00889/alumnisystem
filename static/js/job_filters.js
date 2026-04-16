/**
 * Job Filters Management
 * Handles filter badge removal, clear all filters, show all toggle, and edit preferences
 */

class JobFilters {
    constructor() {
        this.initializeEventListeners();
    }

    /**
     * Initialize all event listeners
     */
    initializeEventListeners() {
        // Filter badge dismiss handlers
        this.initFilterBadgeDismiss();

        // Clear all filters handler
        this.initClearAllFilters();

        // Show all jobs toggle handler
        this.initShowAllToggle();

        // View all jobs button handler
        this.initViewAllJobsButton();

        // Edit preferences button handlers
        this.initEditPreferencesButtons();
    }

    /**
     * Initialize filter badge dismiss functionality
     */
    initFilterBadgeDismiss() {
        const filterBadges = document.querySelectorAll('[data-filter]');
        
        filterBadges.forEach(badge => {
            badge.addEventListener('click', async (e) => {
                e.preventDefault();
                const filterKey = badge.dataset.filter;
                
                if (!filterKey) {
                    console.error('No filter key found');
                    return;
                }

                // Show loading state
                badge.disabled = true;
                const originalContent = badge.innerHTML;
                badge.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';

                try {
                    const response = await fetch(`/jobs/preferences/remove-filter/${filterKey}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': this.getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        }
                    });

                    if (response.ok) {
                        this.showToast('Filter removed successfully', 'success');
                        // Reload page to reflect changes
                        window.location.reload();
                    } else {
                        throw new Error('Failed to remove filter');
                    }
                } catch (error) {
                    console.error('Error removing filter:', error);
                    this.showToast('Failed to remove filter. Please try again.', 'error');
                    // Restore button state
                    badge.disabled = false;
                    badge.innerHTML = originalContent;
                }
            });
        });
    }

    /**
     * Initialize clear all filters functionality
     */
    initClearAllFilters() {
        const clearAllLink = document.getElementById('clearAllFilters');
        
        if (clearAllLink) {
            clearAllLink.addEventListener('click', async (e) => {
                e.preventDefault();

                // Show confirmation dialog
                const confirmed = confirm('Are you sure you want to clear all filters? This will remove all your active filter preferences.');
                
                if (!confirmed) {
                    return;
                }

                // Show loading state
                const originalText = clearAllLink.innerHTML;
                clearAllLink.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Clearing...';

                try {
                    const response = await fetch('/jobs/preferences/clear-all/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': this.getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        }
                    });

                    if (response.ok) {
                        this.showToast('All filters cleared successfully', 'success');
                        // Navigate to clear all filters endpoint (it will redirect)
                        window.location.href = '/jobs/preferences/clear-all/';
                    } else {
                        throw new Error('Failed to clear filters');
                    }
                } catch (error) {
                    console.error('Error clearing filters:', error);
                    this.showToast('Failed to clear filters. Please try again.', 'error');
                    // Restore link state
                    clearAllLink.innerHTML = originalText;
                }
            });
        }
    }

    /**
     * Initialize show all jobs toggle functionality
     */
    initShowAllToggle() {
        const showAllToggle = document.getElementById('showAllToggle');
        
        if (showAllToggle) {
            showAllToggle.addEventListener('change', (e) => {
                const showAll = e.target.checked;
                
                // Show loading indicator
                const label = showAllToggle.nextElementSibling;
                const originalText = label ? label.textContent : '';
                if (label) {
                    label.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Loading...';
                }

                // Update URL parameter and reload
                const url = new URL(window.location.href);
                
                if (showAll) {
                    url.searchParams.set('show_all', 'true');
                } else {
                    url.searchParams.delete('show_all');
                }

                // Navigate to updated URL
                window.location.href = url.toString();
            });
        }
    }

    /**
     * Initialize view all jobs button functionality
     */
    initViewAllJobsButton() {
        const viewAllJobsBtn = document.getElementById('viewAllJobsBtn');
        
        if (viewAllJobsBtn) {
            viewAllJobsBtn.addEventListener('click', (e) => {
                e.preventDefault();

                // Show loading state
                const originalContent = viewAllJobsBtn.innerHTML;
                viewAllJobsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Loading...';
                viewAllJobsBtn.disabled = true;

                // Set show_all parameter and reload
                const url = new URL(window.location.href);
                url.searchParams.set('show_all', 'true');
                
                window.location.href = url.toString();
            });
        }
    }

    /**
     * Initialize edit preferences button functionality
     */
    initEditPreferencesButtons() {
        const editPreferencesBtns = document.querySelectorAll('[id^="editPreferencesBtn"]');
        
        editPreferencesBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();

                try {
                    // Try to use PreferenceModal from preference_modal.js
                    if (typeof window.preferenceModal !== 'undefined' && window.preferenceModal) {
                        window.preferenceModal.show();
                    } else if (typeof bootstrap !== 'undefined') {
                        // Fallback to Bootstrap modal
                        const modalElement = document.getElementById('preferenceModal');
                        if (modalElement) {
                            const modal = new bootstrap.Modal(modalElement);
                            modal.show();
                        } else {
                            console.error('Preference modal element not found');
                            this.showToast('Unable to open preferences modal', 'error');
                        }
                    } else {
                        console.error('Bootstrap not loaded');
                        this.showToast('Unable to open preferences modal', 'error');
                    }
                } catch (error) {
                    console.error('Error opening preference modal:', error);
                    this.showToast('Failed to open preferences. Please refresh the page.', 'error');
                }
            });
        });
    }

    /**
     * Get CSRF token from cookies
     * @param {string} name - Cookie name
     * @returns {string|null} Cookie value
     */
    getCookie(name) {
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

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     */
    showToast(message, type = 'info') {
        // Check if showToast function exists globally (from toast-notifications.js)
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }

        // Fallback: Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${this.getBootstrapAlertClass(type)} position-fixed top-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.style.minWidth = '250px';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close ms-2" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        document.body.appendChild(toast);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    /**
     * Convert toast type to Bootstrap alert class
     * @param {string} type - Toast type
     * @returns {string} Bootstrap alert class
     */
    getBootstrapAlertClass(type) {
        const typeMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return typeMap[type] || 'info';
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.jobFilters = new JobFilters();
});

// Export for external access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JobFilters;
}
