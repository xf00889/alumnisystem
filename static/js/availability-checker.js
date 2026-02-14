/**
 * Availability Checker for Email and Username Fields
 * 
 * Provides real-time availability checking with debounced input handling
 * and visual feedback for registration forms.
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4
 */

class AvailabilityChecker {
    /**
     * Create an AvailabilityChecker instance
     * @param {string} fieldId - The ID of the input field to monitor
     * @param {string} fieldType - The type of field ('email' or 'username')
     * @param {string} endpoint - The API endpoint URL for availability checks
     * @param {number} debounceMs - Debounce delay in milliseconds (default: 500)
     */
    constructor(fieldId, fieldType, endpoint, debounceMs = 500) {
        this.field = document.getElementById(fieldId);
        this.fieldType = fieldType;
        this.endpoint = endpoint;
        this.debounceMs = debounceMs;
        this.debounceTimer = null;
        this.statusContainer = null;
        this.csrfToken = this.getCSRFToken();
        
        if (this.field) {
            this.init();
        }
    }
    
    /**
     * Initialize the checker by setting up event listeners and status container
     */
    init() {
        // Create status container for visual feedback
        this.createStatusContainer();
        
        // Add event listeners
        this.field.addEventListener('input', () => this.handleInput());
        this.field.addEventListener('blur', () => this.handleBlur());
        this.field.addEventListener('focus', () => this.clearStatus());
    }
    
    /**
     * Create the status container element for visual feedback
     */
    createStatusContainer() {
        // Check if status container already exists
        const existingContainer = this.field.parentElement.querySelector('.availability-status');
        if (existingContainer) {
            this.statusContainer = existingContainer;
            return;
        }
        
        // Create new status container (styles defined in availability-checker.css)
        this.statusContainer = document.createElement('div');
        this.statusContainer.className = 'availability-status';
        this.statusContainer.setAttribute('role', 'status');
        this.statusContainer.setAttribute('aria-live', 'polite');
        
        // Insert after the input field
        this.field.parentElement.appendChild(this.statusContainer);
    }
    
    /**
     * Handle input events with debouncing
     */
    handleInput() {
        // Clear any existing timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        const value = this.field.value.trim();
        
        // Clear status if field is empty
        if (!value) {
            this.clearStatus();
            return;
        }
        
        // Show checking status
        this.showChecking();
        
        // Set debounce timer
        this.debounceTimer = setTimeout(() => {
            this.checkAvailability(value);
        }, this.debounceMs);
    }
    
    /**
     * Handle blur events - check immediately if there's a value
     */
    handleBlur() {
        // Clear any pending debounce
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        const value = this.field.value.trim();
        
        if (value) {
            this.checkAvailability(value);
        }
    }
    
    /**
     * Check availability via API
     * @param {string} value - The value to check
     */
    async checkAvailability(value) {
        // Basic validation before API call
        if (this.fieldType === 'email' && !this.isValidEmailFormat(value)) {
            this.clearStatus();
            return;
        }
        
        try {
            const response = await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    field: this.fieldType,
                    value: value
                })
            });
            
            // Handle rate limiting gracefully
            if (response.status === 429) {
                this.showRateLimited();
                return;
            }
            
            // Handle other errors gracefully
            if (!response.ok) {
                this.clearStatus();
                return;
            }
            
            const data = await response.json();
            
            // Handle response
            if (data.available === true) {
                this.showAvailable(data.message);
            } else if (data.available === false) {
                this.showTaken(data.message);
            } else {
                // Rate limited or other issue - clear status silently
                this.clearStatus();
            }
            
        } catch (error) {
            // Fail silently without blocking form submission (Requirement 3.4, 4.4)
            console.warn('Availability check failed:', error);
            this.clearStatus();
        }
    }
    
    /**
     * Show "checking" status with spinner
     */
    showChecking() {
        if (!this.statusContainer) return;
        
        this.statusContainer.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            <span>Checking availability...</span>
        `;
        this.statusContainer.className = 'availability-status checking fade-in';
        
        // Update input field class
        this.field.classList.remove('availability-available', 'availability-taken');
        this.field.classList.add('availability-checking');
    }
    
    /**
     * Show "available" status with green checkmark
     * @param {string} message - The message to display
     */
    showAvailable(message) {
        if (!this.statusContainer) return;
        
        this.statusContainer.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${this.escapeHtml(message)}</span>
        `;
        this.statusContainer.className = 'availability-status available fade-in';
        
        // Update input field class for visual feedback
        this.field.classList.remove('availability-checking', 'availability-taken');
        this.field.classList.add('availability-available');
        this.field.style.borderColor = '';  // Let CSS handle it
    }
    
    /**
     * Show "taken" status with red X
     * @param {string} message - The message to display
     */
    showTaken(message) {
        if (!this.statusContainer) return;
        
        this.statusContainer.innerHTML = `
            <i class="fas fa-times-circle"></i>
            <span>${this.escapeHtml(message)}</span>
        `;
        this.statusContainer.className = 'availability-status taken fade-in';
        
        // Update input field class for visual feedback
        this.field.classList.remove('availability-checking', 'availability-available');
        this.field.classList.add('availability-taken');
        this.field.style.borderColor = '';  // Let CSS handle it
    }
    
    /**
     * Show rate limited message
     */
    showRateLimited() {
        if (!this.statusContainer) return;
        
        this.statusContainer.innerHTML = `
            <i class="fas fa-clock"></i>
            <span>Please wait before checking again.</span>
        `;
        this.statusContainer.className = 'availability-status rate-limited fade-in';
        
        // Remove input field classes
        this.field.classList.remove('availability-checking', 'availability-available', 'availability-taken');
    }
    
    /**
     * Clear the status display
     */
    clearStatus() {
        if (!this.statusContainer) return;
        
        this.statusContainer.innerHTML = '';
        this.statusContainer.className = 'availability-status';
        
        // Reset input field classes and border
        this.field.classList.remove('availability-checking', 'availability-available', 'availability-taken');
        this.field.style.borderColor = '';
    }
    
    /**
     * Get CSRF token from cookies or meta tag
     * @returns {string} The CSRF token
     */
    getCSRFToken() {
        // Try to get from cookie first
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        
        if (cookieValue) {
            return cookieValue.split('=')[1];
        }
        
        // Try to get from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Try to get from hidden input
        const hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (hiddenInput) {
            return hiddenInput.value;
        }
        
        return '';
    }
    
    /**
     * Basic email format validation
     * @param {string} email - The email to validate
     * @returns {boolean} True if valid format
     */
    isValidEmailFormat(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    /**
     * Escape HTML to prevent XSS
     * @param {string} text - The text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AvailabilityChecker;
}
