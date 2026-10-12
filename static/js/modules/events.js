/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--events-event-detail-html") && !executed["events/event_detail.html"]) {
executed["events/event_detail.html"] = true;
/* BEGIN: events/event_detail.html */

// RSVP Form AJAX Submission for Event Detail Page
document.addEventListener('DOMContentLoaded', function() {
    const rsvpForm = document.querySelector('.rsvp-form');
    
    if (rsvpForm) {
        rsvpForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = rsvpForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
            
            const formData = new FormData(rsvpForm);
            
            fetch(rsvpForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                // Re-enable button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                if (data.success) {
                    // Show success alert
                    Swal.fire({
                        icon: 'success',
                        title: 'RSVP Recorded!',
                        text: data.message,
                        confirmButtonText: 'OK',
                        confirmButtonColor: '#2b3c6b',
                        timer: 3000,
                        timerProgressBar: true
                    });
                } else {
                    // Show error alert
                    Swal.fire({
                        icon: 'error',
                        title: 'RSVP Failed',
                        text: data.message || 'There was an error submitting your RSVP. Please try again.',
                        confirmButtonText: 'OK',
                        confirmButtonColor: '#2b3c6b'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Re-enable button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
                
                // Show error alert
                Swal.fire({
                    icon: 'error',
                    title: 'Connection Error',
                    text: 'Unable to submit your RSVP. Please check your connection and try again.',
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#2b3c6b'
                });
            });
        });
    }
});

/* END: events/event_detail.html */
}
})();
