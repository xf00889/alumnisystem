/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--feedback-submit-feedback-html") && !executed["feedback/submit_feedback.html"]) {
executed["feedback/submit_feedback.html"] = true;
/* BEGIN: feedback/submit_feedback.html */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Character counter for subject
    const subjectInput = document.querySelector('#id_subject');
    const subjectCounter = document.querySelector('#subjectCounter');
    
    if (subjectInput && subjectCounter) {
        subjectInput.addEventListener('input', function() {
            const count = this.value.length;
            subjectCounter.textContent = count;
            
            if (count > 190) {
                subjectCounter.style.color = '#dc3545';
            } else {
                subjectCounter.style.color = '#6c757d';
            }
        });
    }
    
    // Attachment preview
    const attachmentInput = document.querySelector('#id_attachment');
    const attachmentPreview = document.querySelector('#attachmentPreview');
    
    if (attachmentInput && attachmentPreview) {
        attachmentInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const fileType = file.type.split('/')[0];
                if (fileType === 'image') {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        attachmentPreview.src = e.target.result;
                        attachmentPreview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                } else {
                    attachmentPreview.style.display = 'none';
                }
            } else {
                attachmentPreview.style.display = 'none';
            }
        });
    }
    
    // Form validation with SweetAlert
    const form = document.querySelector('#feedbackForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!this.checkValidity()) {
            e.stopPropagation();
            this.classList.add('was-validated');
            return;
        }
        
        // Show confirmation dialog
        Swal.fire({
            icon: 'question',
            title: 'Submit Feedback',
            text: 'Are you sure you want to submit this feedback?',
            showCancelButton: true,
            confirmButtonText: 'Yes, submit it!',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                // Show loading state
                Swal.fire({
                    title: 'Submitting Feedback...',
                    text: 'Please wait while we submit your feedback.',
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

/* END: feedback/submit_feedback.html */
}
})();
