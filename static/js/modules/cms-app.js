/* Module scripts from app-owned Django templates; preserve their execution location and DOMContentLoaded timing. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--app-cms-cms-alumni-statistic-confirm-delete-html") && !executed["cms/templates/cms/alumni_statistic_confirm_delete.html"]) {
executed["cms/templates/cms/alumni_statistic_confirm_delete.html"] = true;
/* BEGIN: cms/templates/cms/alumni_statistic_confirm_delete.html */

    document.addEventListener('DOMContentLoaded', function() {
        // This script is for the dedicated delete confirmation page.
        // The SweetAlert for list view is handled by the deleteAlumniStatistic function in alumni_statistic_list.html
        // This page provides a fallback/direct confirmation if accessed directly.
    });

/* END: cms/templates/cms/alumni_statistic_confirm_delete.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-alumni-statistic-list-html") && !executed["cms/templates/cms/alumni_statistic_list.html"]) {
executed["cms/templates/cms/alumni_statistic_list.html"] = true;
/* BEGIN: cms/templates/cms/alumni_statistic_list.html */

// SweetAlert delete function for Alumni Statistics
window.deleteAlumniStatistic = function(statisticType, deleteUrl) {
    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to delete "${statisticType}". This action cannot be undone!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                title: 'Deleting...',
                text: 'Please wait while we delete the alumni statistic.',
                icon: 'info',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // Create a form to submit the delete request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = deleteUrl;
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken.value;
                form.appendChild(csrfInput);
            }
            
            document.body.appendChild(form);
            form.submit();
        }
    });
};

/* END: cms/templates/cms/alumni_statistic_list.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-contact-info-list-html") && !executed["cms/templates/cms/contact_info_list.html"]) {
executed["cms/templates/cms/contact_info_list.html"] = true;
/* BEGIN: cms/templates/cms/contact_info_list.html */

// SweetAlert delete function for contact info
window.deleteContactInfo = function(itemName, deleteUrl) {
    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to delete "${itemName}". This action cannot be undone!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                title: 'Deleting...',
                text: 'Please wait while we delete the contact information.',
                icon: 'info',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Create a form to submit the delete request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = deleteUrl;
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken.value;
                form.appendChild(csrfInput);
            }
            
            document.body.appendChild(form);
            form.submit();
        }
    });
};

/* END: cms/templates/cms/contact_info_list.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-faq-confirm-delete-html") && !executed["cms/templates/cms/faq_confirm_delete.html"]) {
executed["cms/templates/cms/faq_confirm_delete.html"] = true;
/* BEGIN: cms/templates/cms/faq_confirm_delete.html */

    document.addEventListener('DOMContentLoaded', function() {
        // This script is for the dedicated delete confirmation page.
        // The SweetAlert for list view is handled by the deleteFAQ function in faq_list.html
        // This page provides a fallback/direct confirmation if accessed directly.
    });

/* END: cms/templates/cms/faq_confirm_delete.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-faq-list-html") && !executed["cms/templates/cms/faq_list.html"]) {
executed["cms/templates/cms/faq_list.html"] = true;
/* BEGIN: cms/templates/cms/faq_list.html */

// SweetAlert delete function for FAQs
window.deleteFAQ = function(faqQuestion, deleteUrl) {
    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to delete "${faqQuestion}". This action cannot be undone!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                title: 'Deleting...',
                text: 'Please wait while we delete the FAQ.',
                icon: 'info',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // Create a form to submit the delete request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = deleteUrl;
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken.value;
                form.appendChild(csrfInput);
            }
            
            document.body.appendChild(form);
            form.submit();
        }
    });
};

/* END: cms/templates/cms/faq_list.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-feature-confirm-delete-html") && !executed["cms/templates/cms/feature_confirm_delete.html"]) {
executed["cms/templates/cms/feature_confirm_delete.html"] = true;
/* BEGIN: cms/templates/cms/feature_confirm_delete.html */

    document.addEventListener('DOMContentLoaded', function() {
        // This script is for the dedicated delete confirmation page.
        // The SweetAlert for list view is handled by the deleteFeature function in feature_list.html
        // This page provides a fallback/direct confirmation if accessed directly.
    });

/* END: cms/templates/cms/feature_confirm_delete.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-feature-list-html") && !executed["cms/templates/cms/feature_list.html"]) {
executed["cms/templates/cms/feature_list.html"] = true;
/* BEGIN: cms/templates/cms/feature_list.html */

// SweetAlert delete function for Features
window.deleteFeature = function(featureTitle, deleteUrl) {
    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to delete "${featureTitle}". This action cannot be undone!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                title: 'Deleting...',
                text: 'Please wait while we delete the feature.',
                icon: 'info',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // Create a form to submit the delete request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = deleteUrl;
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken.value;
                form.appendChild(csrfInput);
            }
            
            document.body.appendChild(form);
            form.submit();
        }
    });
};

/* END: cms/templates/cms/feature_list.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-staff-member-list-html") && !executed["cms/templates/cms/staff_member_list.html"]) {
executed["cms/templates/cms/staff_member_list.html"] = true;
/* BEGIN: cms/templates/cms/staff_member_list.html */

    // Define handleDeleteClick function immediately
    window.handleDeleteClick = function(event, itemName, itemType = 'item') {
        event.preventDefault();
        
        // Get delete URL from button's data attribute
        let deleteUrl;
        const button = event.target.closest('button');
        if (button && button.dataset.deleteUrl) {
            deleteUrl = button.dataset.deleteUrl;
        } else {
            console.error('No delete URL found');
            return;
        }
        
        // Use SweetAlert if available, otherwise fallback to confirm
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'Are you sure?',
                text: `You are about to delete "${itemName}". This action cannot be undone!`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#e53e3e',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Yes, delete it!',
                cancelButtonText: 'Cancel',
                background: '#f8f9fa',
                color: '#2d3748'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Create a form to submit the delete request
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = deleteUrl;
                    
                    // Add CSRF token
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                    if (csrfToken) {
                        const csrfInput = document.createElement('input');
                        csrfInput.type = 'hidden';
                        csrfInput.name = 'csrfmiddlewaretoken';
                        csrfInput.value = csrfToken.value;
                        form.appendChild(csrfInput);
                    } else {
                        console.error('CSRF token not found');
                        alert('Security token not found. Please refresh the page and try again.');
                        return;
                    }
                    
                    document.body.appendChild(form);
                    form.submit();
                }
            });
        } else {
            // Fallback to basic confirmation if SweetAlert is not available
            if (confirm(`Are you sure you want to delete "${itemName}"?`)) {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = deleteUrl;
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfToken) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = csrfToken.value;
                    form.appendChild(csrfInput);
                } else {
                    console.error('CSRF token not found');
                    alert('Security token not found. Please refresh the page and try again.');
                    return;
                }
                
                document.body.appendChild(form);
                form.submit();
            }
        }
    };
    
    // Verify function is available
    console.log('handleDeleteClick function defined:', typeof window.handleDeleteClick);
    
/* END: cms/templates/cms/staff_member_list.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-testimonial-confirm-delete-html") && !executed["cms/templates/cms/testimonial_confirm_delete.html"]) {
executed["cms/templates/cms/testimonial_confirm_delete.html"] = true;
/* BEGIN: cms/templates/cms/testimonial_confirm_delete.html */

    document.addEventListener('DOMContentLoaded', function() {
        // This script is for the dedicated delete confirmation page.
        // The SweetAlert for list view is handled by the deleteTestimonial function in testimonial_list.html
        // This page provides a fallback/direct confirmation if accessed directly.
    });

/* END: cms/templates/cms/testimonial_confirm_delete.html */
}
if (document.documentElement.classList.contains("fe-page--app-cms-cms-testimonial-list-html") && !executed["cms/templates/cms/testimonial_list.html"]) {
executed["cms/templates/cms/testimonial_list.html"] = true;
/* BEGIN: cms/templates/cms/testimonial_list.html */

// SweetAlert delete function for Testimonials
window.deleteTestimonial = function(testimonialName, deleteUrl) {
    Swal.fire({
        title: 'Are you sure?',
        text: `You are about to delete "${testimonialName}". This action cannot be undone!`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Show loading state
            Swal.fire({
                title: 'Deleting...',
                text: 'Please wait while we delete the testimonial.',
                icon: 'info',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // Create a form to submit the delete request
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = deleteUrl;
            
            // Add CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (csrfToken) {
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken.value;
                form.appendChild(csrfInput);
            }
            
            document.body.appendChild(form);
            form.submit();
        }
    });
};

/* END: cms/templates/cms/testimonial_list.html */
}
})();
