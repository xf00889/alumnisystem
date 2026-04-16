/**
 * Preference Modal JavaScript
 * Handles multi-step job preference configuration modal
 */

class PreferenceModal {
    constructor() {
        // Initialize step tracking
        this.currentStep = 1;
        this.totalSteps = 5;
        
        // Store modal instance
        const modalElement = document.getElementById('preferenceModal');
        if (!modalElement) {
            console.error('Preference modal element not found');
            return;
        }
        this.modal = new bootstrap.Modal(modalElement);
        
        // Initialize event listeners
        this.initializeEventListeners();
    }
    
    /**
     * Initialize all event listeners for modal interactions
     */
    initializeEventListeners() {
        // Navigation button handlers
        const nextBtn = document.getElementById('nextBtn');
        const prevBtn = document.getElementById('prevBtn');
        const saveBtn = document.getElementById('saveBtn');
        const remindLaterBtn = document.getElementById('remindLaterBtn');
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextStep());
        }
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.prevStep());
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.savePreferences());
        }
        
        if (remindLaterBtn) {
            remindLaterBtn.addEventListener('click', () => this.remindLater());
        }
        
        // Skill matching toggle handler
        const skillMatchToggle = document.getElementById('skillMatchToggle');
        if (skillMatchToggle) {
            skillMatchToggle.addEventListener('change', (e) => {
                const thresholdContainer = document.getElementById('skillThresholdContainer');
                if (thresholdContainer) {
                    if (e.target.checked) {
                        thresholdContainer.classList.remove('d-none');
                    } else {
                        thresholdContainer.classList.add('d-none');
                    }
                }
            });
        }
        
        // Threshold slider handler
        const skillThreshold = document.getElementById('skillThreshold');
        if (skillThreshold) {
            skillThreshold.addEventListener('input', (e) => {
                const thresholdValue = document.getElementById('thresholdValue');
                if (thresholdValue) {
                    thresholdValue.textContent = e.target.value;
                }
            });
        }
    }
    
    /**
     * Move to the next step if current step is valid
     */
    nextStep() {
        if (this.validateCurrentStep()) {
            this.currentStep++;
            this.updateStepDisplay();
        }
    }
    
    /**
     * Move to the previous step
     */
    prevStep() {
        this.currentStep--;
        this.updateStepDisplay();
    }
    
    /**
     * Update the display to show the current step
     */
    updateStepDisplay() {
        // Hide all steps
        const allSteps = document.querySelectorAll('.preference-step');
        allSteps.forEach(step => {
            step.classList.add('d-none');
        });
        
        // Show current step
        const currentStepElement = document.querySelector(`[data-step="${this.currentStep}"]`);
        if (currentStepElement) {
            currentStepElement.classList.remove('d-none');
        }
        
        // Update progress bar
        const progress = (this.currentStep / this.totalSteps) * 100;
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', this.currentStep);
        }
        
        // Update step indicator text
        const currentStepText = document.getElementById('currentStep');
        if (currentStepText) {
            currentStepText.textContent = this.currentStep;
        }
        
        // Update button states
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const saveBtn = document.getElementById('saveBtn');
        
        // Enable/disable previous button
        if (prevBtn) {
            prevBtn.disabled = this.currentStep === 1;
        }
        
        // Show/hide next and save buttons based on step
        if (this.currentStep === this.totalSteps) {
            if (nextBtn) nextBtn.classList.add('d-none');
            if (saveBtn) saveBtn.classList.remove('d-none');
        } else {
            if (nextBtn) nextBtn.classList.remove('d-none');
            if (saveBtn) saveBtn.classList.add('d-none');
        }
    }
    
    /**
     * Validate the current step before allowing progression
     * @returns {boolean} True if validation passes, false otherwise
     */
    validateCurrentStep() {
        // Clear any existing error messages
        this.clearErrorMessage(this.currentStep);
        
        switch (this.currentStep) {
            case 1:
                // Step 1: At least one job type must be selected
                const jobTypeCheckboxes = document.querySelectorAll('input[name="job_types"]:checked');
                if (jobTypeCheckboxes.length === 0) {
                    this.showErrorMessage(1, 'Please select at least one job type');
                    return false;
                }
                return true;
                
            case 2:
                // Step 2: Industry selection is optional, always valid
                return true;
                
            case 3:
                // Step 3: Validate location format if provided
                const locationText = document.getElementById('location_text');
                if (locationText && locationText.value.trim()) {
                    // Basic validation: check if it's not just commas or whitespace
                    const cleanedLocation = locationText.value.trim().replace(/,+/g, ',');
                    if (cleanedLocation === ',' || cleanedLocation.length < 2) {
                        this.showErrorMessage(3, 'Please enter a valid location');
                        return false;
                    }
                }
                return true;
                
            case 4:
                // Step 4: Validate salary is positive if provided
                const minimumSalary = document.getElementById('minimum_salary');
                if (minimumSalary && minimumSalary.value) {
                    const salaryValue = parseFloat(minimumSalary.value);
                    if (isNaN(salaryValue) || salaryValue < 0) {
                        this.showErrorMessage(4, 'Salary must be a positive number');
                        return false;
                    }
                }
                return true;
                
            case 5:
                // Step 5: Validate threshold is 0-100 if skill matching is enabled
                const skillMatchToggle = document.getElementById('skillMatchToggle');
                if (skillMatchToggle && skillMatchToggle.checked) {
                    const skillThreshold = document.getElementById('skillThreshold');
                    if (skillThreshold) {
                        const thresholdValue = parseInt(skillThreshold.value);
                        if (isNaN(thresholdValue) || thresholdValue < 0 || thresholdValue > 100) {
                            this.showErrorMessage(5, 'Skill match threshold must be between 0 and 100');
                            return false;
                        }
                    }
                }
                return true;
                
            default:
                return true;
        }
    }
    
    /**
     * Show error message for a specific step
     * @param {number} step - The step number
     * @param {string} message - The error message to display
     */
    showErrorMessage(step, message) {
        const errorAlert = document.getElementById(`step${step}Error`);
        const errorMessage = document.getElementById(`step${step}ErrorMessage`);
        
        if (errorAlert && errorMessage) {
            errorMessage.textContent = message;
            errorAlert.classList.remove('d-none');
        }
    }
    
    /**
     * Clear error message for a specific step
     * @param {number} step - The step number
     */
    clearErrorMessage(step) {
        const errorAlert = document.getElementById(`step${step}Error`);
        if (errorAlert) {
            errorAlert.classList.add('d-none');
        }
    }
    
    /**
     * Save preferences via AJAX
     */
    async savePreferences() {
        const form = document.getElementById('preferenceForm');
        if (!form) {
            console.error('Preference form not found');
            return;
        }
        
        // Validate final step before saving
        if (!this.validateCurrentStep()) {
            return;
        }
        
        // Create FormData from form
        const formData = new FormData(form);
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!csrfToken) {
            console.error('CSRF token not found');
            alert('Security token missing. Please refresh the page and try again.');
            return;
        }
        
        // Disable save button during request
        const saveBtn = document.getElementById('saveBtn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...';
        }
        
        try {
            const response = await fetch('/jobs/preferences/save/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken.value
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Hide modal and reload page to show filtered jobs
                    this.modal.hide();
                    window.location.reload();
                } else {
                    // Show error message from server
                    alert(data.message || 'Failed to save preferences. Please try again.');
                    if (saveBtn) {
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Save Preferences';
                    }
                }
            } else {
                // Handle HTTP error
                console.error('Server error:', response.status, response.statusText);
                alert('Failed to save preferences. Please try again.');
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Save Preferences';
                }
            }
        } catch (error) {
            // Handle network error
            console.error('Error saving preferences:', error);
            alert('An error occurred while saving. Please check your connection and try again.');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Save Preferences';
            }
        }
    }
    
    /**
     * Handle "Remind me later" action
     */
    async remindLater() {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!csrfToken) {
            console.error('CSRF token not found');
            this.modal.hide();
            return;
        }
        
        try {
            const response = await fetch('/jobs/preferences/remind-later/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken.value,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Successfully recorded reminder, hide modal
                this.modal.hide();
            } else {
                // Log error but still hide modal (non-critical operation)
                console.error('Failed to record reminder:', response.status);
                this.modal.hide();
            }
        } catch (error) {
            // Log error but still hide modal (non-critical operation)
            console.error('Error recording reminder:', error);
            this.modal.hide();
        }
    }
    
    /**
     * Show the modal
     */
    show() {
        this.modal.show();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize PreferenceModal instance
    const preferenceModal = new PreferenceModal();
    
    // Check if modal should be auto-shown
    const showModal = document.body.dataset.showPreferenceModal === 'true';
    if (showModal) {
        preferenceModal.show();
    }
    
    // Add click handlers to all "Edit Preferences" buttons
    const editButtons = document.querySelectorAll('[id^="editPreferencesBtn"]');
    editButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            preferenceModal.show();
        });
    });
});
