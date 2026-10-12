/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--accounts-edit-profile-html") && !executed["accounts/edit_profile.html"]) {
executed["accounts/edit_profile.html"] = true;
/* BEGIN: accounts/edit_profile.html */

    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('profileForm');
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show confirmation dialog
            Swal.fire({
                icon: 'question',
                title: 'Update Profile',
                text: 'Are you sure you want to update your profile?',
                showCancelButton: true,
                confirmButtonText: 'Yes, update it!',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show loading state
                    Swal.fire({
                        title: 'Updating Profile...',
                        text: 'Please wait while we save your changes.',
                        allowOutsideClick: false,
                        allowEscapeKey: false,
                        showConfirmButton: false,
                        didOpen: () => {
                            Swal.showLoading();
                        }
                    });
                    
                    // Submit the form
                    form.submit();
                }
            });
        });
    });

/* END: accounts/edit_profile.html */
}
if (document.documentElement.classList.contains("fe-page--accounts-mentor-application-form-html") && !executed["accounts/mentor_application_form.html"]) {
executed["accounts/mentor_application_form.html"] = true;
/* BEGIN: accounts/mentor_application_form.html */

    // Make functions globally available
    window.currentStep = 1;
    window.totalSteps = 3;

    window.updateStepIndicator = function(step) {
        // Update step indicators
        document.querySelectorAll('.step').forEach((stepEl, index) => {
            const stepNum = index + 1;
            if (stepNum < step) {
                stepEl.classList.add('completed');
                stepEl.classList.remove('active');
            } else if (stepNum === step) {
                stepEl.classList.add('active');
                stepEl.classList.remove('completed');
            } else {
                stepEl.classList.remove('active', 'completed');
            }
        });
    };

    window.showStep = function(step) {
        // Hide all steps
        document.querySelectorAll('.step-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Show current step
        const stepContent = document.getElementById('step' + step);
        if (stepContent) {
            stepContent.classList.add('active');
            window.currentStep = step;
            window.updateStepIndicator(step);
            
            // Scroll to top of form
            stepContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    window.nextStep = function(step) {
        // Validate current step before proceeding
        const currentStepContent = document.getElementById('step' + window.currentStep);
        const form = document.getElementById('mentorApplicationForm');
        
        if (!currentStepContent) {
            console.error('Current step content not found');
            return;
        }
        
        // Get all required fields in current step
        const requiredFields = currentStepContent.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        if (isValid) {
            window.showStep(step);
        } else {
            alert('Please fill in all required fields before proceeding.');
        }
    };

    window.previousStep = function(step) {
        window.showStep(step);
    };

    // File input validation
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            if (this.files[0]) {
                const file = this.files[0];
                const fileSize = file.size / 1024 / 1024; // Size in MB
                
                if (!file.name.toLowerCase().endsWith('.pdf')) {
                    this.value = '';
                    alert('Please upload only PDF files.');
                    this.classList.add('is-invalid');
                } else if (fileSize > 5) {
                    this.value = '';
                    alert('File size must be under 5MB.');
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                    // Show file name
                    const label = this.parentElement.querySelector('.form-label');
                    if (label) {
                        const fileName = document.createElement('small');
                        fileName.className = 'file-name text-success';
                        fileName.textContent = `✓ ${file.name}`;
                        fileName.style.display = 'block';
                        fileName.style.marginTop = '0.5rem';
                        
                        // Remove previous file name if exists
                        const prevFileName = label.parentElement.querySelector('.file-name');
                        if (prevFileName) {
                            prevFileName.remove();
                        }
                        
                        label.parentElement.appendChild(fileName);
                    }
                }
            }
        });
    });

    // Initialize step indicator
    document.addEventListener('DOMContentLoaded', function() {
        window.updateStepIndicator(1);
    });

/* END: accounts/mentor_application_form.html */
}
if (document.documentElement.classList.contains("fe-page--accounts-profile-detail-html") && !executed["accounts/profile_detail.html"]) {
executed["accounts/profile_detail.html"] = true;
/* BEGIN: accounts/profile_detail.html */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Profile detail page loaded');
    
    // Debug: Log all modals found on the page
    const allModals = document.querySelectorAll('.modal');
    console.log('Total modals found:', allModals.length);
    allModals.forEach(modal => {
        console.log('Modal ID:', modal.id);
    });
    
    // Fix for mobile modal display issues
    // Ensure modals are properly initialized and displayed on mobile devices
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function(e) {
            console.log('Modal showing:', modal.id);
            // Ensure body overflow is hidden when modal opens
            document.body.style.overflow = 'hidden';
            document.body.style.paddingRight = '0';
            
            // Force modal to be visible and above backdrop with higher z-index
            setTimeout(() => {
                modal.style.display = 'block';
                modal.style.zIndex = '10060';
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.style.zIndex = '10055';
                    console.log('Backdrop z-index set to 10055');
                }
                console.log('Modal display and z-index set to 10060');
            }, 10);
        });
        
        modal.addEventListener('shown.bs.modal', function(e) {
            console.log('Modal shown:', modal.id);
            // Ensure modal dialog is visible
            const modalDialog = modal.querySelector('.modal-dialog');
            if (modalDialog) {
                modalDialog.style.transform = 'none';
                modalDialog.style.marginTop = '1rem';
                console.log('Modal dialog transform reset');
            }
        });
        
        modal.addEventListener('hide.bs.modal', function(e) {
            console.log('Modal hiding:', modal.id);
        });
        
        modal.addEventListener('hidden.bs.modal', function(e) {
            console.log('Modal hidden:', modal.id);
            // Restore body overflow
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
    });
    
    // Debug: Test modal trigger buttons
    const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
    console.log('Total modal trigger buttons found:', modalTriggers.length);
    modalTriggers.forEach(trigger => {
        const targetModal = trigger.getAttribute('data-bs-target');
        console.log('Trigger button for modal:', targetModal);
        
        trigger.addEventListener('click', function(e) {
            console.log('Modal trigger clicked:', targetModal);
            const modalElement = document.querySelector(targetModal);
            if (modalElement) {
                console.log('Modal element found:', modalElement.id);
            } else {
                console.error('Modal element NOT found for:', targetModal);
            }
        });
    });
    
    // Django messages are handled by the global processDjangoMessages() function
    console.log('Profile detail page loaded - messages will be processed globally');


    // Handle edit form submissions specifically
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.tagName === 'FORM' && form.id) {
            console.log(`Form submitted: ${form.id}, action: ${form.action}`);
            
            // Check if this is an edit form
            if (form.id.startsWith('editEducationForm') || form.id.startsWith('editExperienceForm')) {
                console.log('Edit form detected, allowing normal submission');
                // Let the form submit normally - the Django view will handle the redirect and messages
                return true;
            }
        }
    });

    // Handle delete buttons
    document.querySelectorAll('.delete-button').forEach(button => {
        button.addEventListener('click', function() {
            deleteItemId = this.dataset.itemId;
            deleteItemType = this.dataset.itemType;
            
            // Update modal text
            const modalBody = document.querySelector('#confirmDeleteModal .modal-body');
            if (deleteItemType === 'experience') {
                modalBody.textContent = 'Are you sure you want to delete this work experience? This action cannot be undone.';
            } else if (deleteItemType === 'education') {
                modalBody.textContent = 'Are you sure you want to delete this education record? This action cannot be undone.';
            } else {
                modalBody.textContent = 'Are you sure you want to delete this item? This action cannot be undone.';
            }
        });
    });
    
    // Handle confirm delete button with SweetAlert
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (!deleteItemId || !deleteItemType) return;
            
            let url = '';
            let itemName = '';
            if (deleteItemType === 'experience') {
                url = `/accounts/update/experience/${deleteItemId}/delete/`;
                itemName = 'work experience';
            } else if (deleteItemType === 'education') {
                url = `/accounts/update/education/${deleteItemId}/delete/`;
                itemName = 'education record';
            } else {
                return;
            }
            
            // Use SweetAlert for confirmation
            Swal.fire({
                icon: 'warning',
                title: 'Confirm Deletion',
                text: `Are you sure you want to delete this ${itemName}? This action cannot be undone.`,
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, delete it!',
                cancelButtonText: 'Cancel'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Show loading state
                    Swal.fire({
                        title: 'Deleting...',
                        text: 'Please wait while we delete the item.',
                        allowOutsideClick: false,
                        allowEscapeKey: false,
                        showConfirmButton: false,
                        didOpen: () => {
                            Swal.showLoading();
                        }
                    });
                    
                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            // Close modal
                            const modalInstance = bootstrap.Modal.getInstance(document.getElementById('confirmDeleteModal'));
                            modalInstance.hide();
                            
                            // Show success message
                            Swal.fire({
                                icon: 'success',
                                title: 'Deleted!',
                                text: 'The item has been deleted successfully.',
                                confirmButtonText: 'OK'
                            }).then(() => {
                                window.location.reload();
                            });
                        } else {
                            throw new Error(data.message || 'Delete operation failed');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'Error deleting item: ' + error.message,
                            confirmButtonText: 'OK'
                        });
                    });
                }
            });
        });
    }
    
    // Initialize variables for delete functionality
    let deleteItemId = null;
    let deleteItemType = null;
});

/* END: accounts/profile_detail.html */
}
if (document.documentElement.classList.contains("fe-page--accounts-security-dashboard-html") && !executed["accounts/security_dashboard.html"]) {
executed["accounts/security_dashboard.html"] = true;
/* BEGIN: accounts/security_dashboard.html */

// No additional JavaScript needed for this page

/* END: accounts/security_dashboard.html */
}
if (document.documentElement.classList.contains("fe-page--accounts-skill-matching-html") && !executed["accounts/skill_matching.html"]) {
executed["accounts/skill_matching.html"] = true;
/* BEGIN: accounts/skill_matching.html */

    document.addEventListener('DOMContentLoaded', function() {
        initSkillMatching();
    });

/* END: accounts/skill_matching.html */
}
})();
