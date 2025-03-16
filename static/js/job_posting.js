/**
 * Job Posting Form JavaScript
 * Enhances the job posting form with validation, dynamic content, and improved UX
 */

document.addEventListener('DOMContentLoaded', function() {
    initJobPostingForm();
});

/**
 * Initialize the job posting form functionality
 */
function initJobPostingForm() {
    setupDocumentFormHandling();
    setupFormValidation();
    setupToggleButtons();
    setupCharacterCounters();
    setupFormattingHelp();
    setupSalaryRangeHelper();
}

/**
 * Setup document form handling (add, remove, animation)
 */
function setupDocumentFormHandling() {
    const addButton = document.getElementById('add-document');
    const totalForms = document.getElementById('id_required_documents-TOTAL_FORMS');
    const formContainer = document.getElementById('document-forms');
    
    if (!addButton || !totalForms || !formContainer) return;
    
    const emptyForm = document.querySelector('.document-requirement')?.cloneNode(true);
    if (!emptyForm) return;
    
    // Add new document form
    addButton.addEventListener('click', function() {
        const formCount = parseInt(totalForms.value);
        const newForm = emptyForm.cloneNode(true);
        
        // Update form index
        newForm.innerHTML = newForm.innerHTML.replace(/-\d+-/g, `-${formCount}-`);
        
        // Clear form values
        newForm.querySelectorAll('input:not([type=hidden]), textarea, select').forEach(input => {
            input.value = '';
        });
        
        // Update checkbox states
        newForm.querySelectorAll('input[type=checkbox]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Add animation class
        newForm.classList.add('new-form');
        
        formContainer.appendChild(newForm);
        totalForms.value = formCount + 1;
        
        // Setup character counters for new form
        setupCharacterCounters(newForm);
    });
    
    // Handle form deletion
    formContainer.addEventListener('change', function(e) {
        if (e.target.name.endsWith('-DELETE')) {
            const formDiv = e.target.closest('.document-requirement');
            if (e.target.checked) {
                formDiv.style.opacity = '0.5';
                formDiv.style.transform = 'scale(0.98)';
            } else {
                formDiv.style.opacity = '1';
                formDiv.style.transform = 'scale(1)';
            }
        }
    });
}

/**
 * Setup toggle buttons for collapsible sections
 */
function setupToggleButtons() {
    const toggleButtons = document.querySelectorAll('.toggle-btn');
    
    toggleButtons.forEach(button => {
        const targetId = button.getAttribute('data-bs-target');
        const targetElement = document.querySelector(targetId);
        const icon = button.querySelector('i');
        
        // Set initial state
        if (targetElement && !targetElement.classList.contains('show')) {
            icon.style.transform = 'rotate(-90deg)';
        }
        
        button.addEventListener('click', function() {
            if (icon) {
                if (targetElement.classList.contains('show')) {
                    icon.style.transform = 'rotate(-90deg)';
                } else {
                    icon.style.transform = 'rotate(0deg)';
                }
            }
        });
    });
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const form = document.querySelector('.job-posting-container form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        // Validate required fields
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                highlightInvalidField(field);
            } else {
                removeInvalidHighlight(field);
            }
        });
        
        // Validate job description minimum length
        const jobDescription = document.getElementById('id_job_description');
        if (jobDescription && jobDescription.value.trim().length < 100) {
            isValid = false;
            highlightInvalidField(jobDescription);
            showValidationError(jobDescription, 'Job description should be at least 100 characters');
        }
        
        if (!isValid) {
            e.preventDefault();
            showToast('Please fix the highlighted errors before submitting', 'error');
            
            // Scroll to first error
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
}

/**
 * Highlight invalid form field
 */
function highlightInvalidField(field) {
    field.classList.add('is-invalid');
    
    // Add error message if not exists
    const errorDiv = field.parentElement.querySelector('.invalid-feedback');
    if (!errorDiv) {
        const div = document.createElement('div');
        div.className = 'invalid-feedback';
        div.textContent = field.getAttribute('data-error-message') || 'This field is required';
        field.parentElement.appendChild(div);
    }
}

/**
 * Remove invalid highlight from field
 */
function removeInvalidHighlight(field) {
    field.classList.remove('is-invalid');
}

/**
 * Show validation error message
 */
function showValidationError(field, message) {
    const errorDiv = field.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.textContent = message;
    } else {
        const div = document.createElement('div');
        div.className = 'invalid-feedback';
        div.textContent = message;
        field.parentElement.appendChild(div);
    }
}

/**
 * Setup character counters for textareas
 */
function setupCharacterCounters(container = document) {
    const textareas = container.querySelectorAll('textarea');
    
    textareas.forEach(textarea => {
        // Skip if counter already exists
        if (textarea.parentElement.querySelector('.char-counter')) return;
        
        const counter = document.createElement('div');
        counter.className = 'char-counter text-muted small mt-1';
        updateCharCounter(counter, textarea.value.length);
        
        textarea.parentElement.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            updateCharCounter(counter, this.value.length);
        });
    });
}

/**
 * Update character counter
 */
function updateCharCounter(counterElement, count) {
    counterElement.textContent = `${count} characters`;
    
    if (count < 50) {
        counterElement.classList.add('text-danger');
    } else if (count < 100) {
        counterElement.classList.add('text-warning');
        counterElement.classList.remove('text-danger');
    } else {
        counterElement.classList.remove('text-warning', 'text-danger');
    }
}

/**
 * Setup formatting help tooltips
 */
function setupFormattingHelp() {
    const jobDescription = document.getElementById('id_job_description');
    const requirements = document.getElementById('id_requirements');
    const responsibilities = document.getElementById('id_responsibilities');
    
    const textareas = [jobDescription, requirements, responsibilities].filter(Boolean);
    
    textareas.forEach(textarea => {
        const helpButton = document.createElement('button');
        helpButton.type = 'button';
        helpButton.className = 'btn btn-sm btn-outline-secondary formatting-help-btn';
        helpButton.innerHTML = '<i class="fas fa-question-circle"></i> Formatting Help';
        
        textarea.parentElement.appendChild(helpButton);
        
        helpButton.addEventListener('click', function() {
            showFormattingHelp(textarea);
        });
    });
}

/**
 * Show formatting help modal
 */
function showFormattingHelp(textarea) {
    // Create modal if it doesn't exist
    if (!document.getElementById('formattingHelpModal')) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'formattingHelpModal';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-hidden', 'true');
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Formatting Tips</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>You can use these formatting tips to make your job posting more readable:</p>
                        <ul>
                            <li>Use <strong>*asterisks*</strong> for bullet points at the start of lines</li>
                            <li>Leave blank lines between paragraphs</li>
                            <li>Use <strong>ALL CAPS</strong> sparingly for section headers</li>
                            <li>Keep paragraphs short and focused</li>
                        </ul>
                        <div class="mt-3">
                            <button type="button" class="btn btn-sm btn-outline-primary add-bullet-list">Add Bullet List Template</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Initialize Bootstrap modal
        const modalElement = new bootstrap.Modal(modal);
        
        // Add bullet list template button
        modal.querySelector('.add-bullet-list').addEventListener('click', function() {
            const template = "\n\n* \n* \n* \n* \n* \n";
            textarea.value += template;
            textarea.focus();
            textarea.selectionStart = textarea.value.length - template.length + 3;
            textarea.selectionEnd = textarea.selectionStart;
            
            // Update character counter
            const counter = textarea.parentElement.querySelector('.char-counter');
            if (counter) {
                updateCharCounter(counter, textarea.value.length);
            }
            
            modalElement.hide();
        });
        
        modalElement.show();
    } else {
        const modalElement = bootstrap.Modal.getInstance(document.getElementById('formattingHelpModal')) || 
                            new bootstrap.Modal(document.getElementById('formattingHelpModal'));
        modalElement.show();
    }
}

/**
 * Setup salary range helper
 */
function setupSalaryRangeHelper() {
    const salaryField = document.getElementById('id_salary_range');
    if (!salaryField) return;
    
    const helpButton = document.createElement('button');
    helpButton.type = 'button';
    helpButton.className = 'btn btn-sm btn-outline-secondary salary-helper-btn mt-1';
    helpButton.innerHTML = '<i class="fas fa-dollar-sign"></i> Salary Format Helper';
    
    salaryField.parentElement.appendChild(helpButton);
    
    helpButton.addEventListener('click', function() {
        const options = [
            'PHP 25,000 - 35,000 monthly',
            'PHP 40,000 - 60,000 monthly',
            'PHP 70,000 - 90,000 monthly',
            'PHP 300,000 - 500,000 annually',
            'PHP 500,000 - 800,000 annually',
            'PHP 1,000,000+ annually',
            'Competitive / Negotiable',
            'Based on experience'
        ];
        
        const dropdown = document.createElement('div');
        dropdown.className = 'salary-format-dropdown';
        dropdown.innerHTML = options.map(option => `<div class="salary-option">${option}</div>`).join('');
        
        salaryField.parentElement.appendChild(dropdown);
        
        // Add click event to options
        dropdown.querySelectorAll('.salary-option').forEach(option => {
            option.addEventListener('click', function() {
                salaryField.value = this.textContent;
                dropdown.remove();
            });
        });
        
        // Remove dropdown when clicking outside
        document.addEventListener('click', function removeDropdown(e) {
            if (!dropdown.contains(e.target) && e.target !== helpButton) {
                dropdown.remove();
                document.removeEventListener('click', removeDropdown);
            }
        });
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    if (!document.querySelector('.toast-container')) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const container = document.querySelector('.toast-container');
    
    // Create toast
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}`;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    container.appendChild(toastElement);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
} 