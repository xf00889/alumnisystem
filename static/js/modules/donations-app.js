/* Module scripts from app-owned Django templates; preserve their execution location and DOMContentLoaded timing. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--app-donations-donations-gcash-config-form-html") && !executed["donations/templates/donations/gcash_config_form.html"]) {
executed["donations/templates/donations/gcash_config_form.html"] = true;
/* BEGIN: donations/templates/donations/gcash_config_form.html */

          if (typeof window.previewImage === 'undefined') {
            window.previewImage = function(input, previewId, imgId, placeholderId) {
              const file = input.files[0];
              const previewWrapper = document.getElementById(previewId);
              const placeholder = document.getElementById(placeholderId);
              
              if (file) {
                if (file.size > 5 * 1024 * 1024) {
                  Swal.fire({
                    title: 'File Too Large',
                    text: 'File size must be less than 5MB',
                    icon: 'error',
                    confirmButtonColor: '#2b3c6b'
                  });
                  input.value = '';
                  return;
                }
                
                if (!file.type.startsWith('image/')) {
                  Swal.fire({
                    title: 'Invalid File Type',
                    text: 'Please select an image file',
                    icon: 'error',
                    confirmButtonColor: '#2b3c6b'
                  });
                  input.value = '';
                  return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                  if (placeholder) {
                    placeholder.style.display = 'none';
                  }
                  
                  let img = document.getElementById(imgId);
                  if (!img) {
                    img = document.createElement('img');
                    img.id = imgId;
                    img.className = 'preview-image';
                    img.alt = 'Preview';
                    previewWrapper.appendChild(img);
                  }
                  
                  img.src = e.target.result;
                  
                  let overlay = previewWrapper.querySelector('.image-overlay');
                  if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.className = 'image-overlay';
                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className = 'btn-remove-image';
                    removeBtn.innerHTML = '<i class="fas fa-trash"></i> Remove';
                    removeBtn.onclick = function() {
                      window.clearImage(input.id, previewId);
                    };
                    overlay.appendChild(removeBtn);
                    previewWrapper.appendChild(overlay);
                  }
                  
                  const clearCheckbox = document.getElementById(input.id + '-clear');
                  if (clearCheckbox) {
                    clearCheckbox.checked = false;
                  }
                };
                reader.readAsDataURL(file);
              }
            };
          }
          
          if (typeof window.clearImage === 'undefined') {
            window.clearImage = function(inputId, previewId) {
              const input = document.getElementById(inputId);
              const previewWrapper = document.getElementById(previewId);
              const img = previewWrapper.querySelector('.preview-image');
              const placeholder = previewWrapper.querySelector('.image-placeholder');
              const overlay = previewWrapper.querySelector('.image-overlay');
              
              if (input) {
                input.value = '';
              }
              
              const clearCheckbox = document.getElementById(inputId + '-clear');
              if (clearCheckbox) {
                clearCheckbox.checked = true;
              }
              
              if (img) {
                img.remove();
              }
              
              if (overlay) {
                overlay.remove();
              }
              
              if (!placeholder) {
                const newPlaceholder = document.createElement('div');
                newPlaceholder.className = 'image-placeholder';
                newPlaceholder.innerHTML = '<i class="fas fa-qrcode"></i><p>No QR code image</p>';
                previewWrapper.appendChild(newPlaceholder);
              } else {
                placeholder.style.display = 'flex';
              }
            };
          }
          
/* END: donations/templates/donations/gcash_config_form.html */
}
if (document.documentElement.classList.contains("fe-page--app-donations-donations-gcash-manage-html") && !executed["donations/templates/donations/gcash_manage.html"]) {
executed["donations/templates/donations/gcash_manage.html"] = true;
/* BEGIN: donations/templates/donations/gcash_manage.html */

// Basic client-side validation hooks (Bootstrap)
(() => {
  'use strict';
  const forms = document.querySelectorAll('.needs-validation');
  Array.from(forms).forEach(form => {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });
})();

/* END: donations/templates/donations/gcash_manage.html */
}
if (document.documentElement.classList.contains("fe-page--app-donations-donations-upload-payment-proof-minimal-html") && !executed["donations/templates/donations/upload_payment_proof_minimal.html"]) {
executed["donations/templates/donations/upload_payment_proof_minimal.html"] = true;
/* BEGIN: donations/templates/donations/upload_payment_proof_minimal.html */

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('id_payment_proof');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const uploadBtn = document.getElementById('uploadBtn');
    const form = document.querySelector('.needs-validation');

    // File input validation and preview
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file size (5MB limit)
                if (file.size > 5 * 1024 * 1024) {
                    Swal.fire({
                        title: 'File Too Large',
                        text: 'Please select a file smaller than 5MB',
                        icon: 'error',
                        confirmButtonColor: '#2b3c6b'
                    });
                    fileInput.value = '';
                    imagePreview.style.display = 'none';
                    return;
                }

                // Check file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
                if (!allowedTypes.includes(file.type)) {
                    Swal.fire({
                        title: 'Invalid File Type',
                        text: 'Please select a JPG, PNG, or GIF image file',
                        icon: 'error',
                        confirmButtonColor: '#2b3c6b'
                    });
                    fileInput.value = '';
                    imagePreview.style.display = 'none';
                    return;
                }

                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.style.display = 'none';
            }
        });
    }

    // Form validation
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }

    // Form submission with AJAX and SweetAlert
    if (form && uploadBtn) {
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            
            console.log('Form submit event triggered');
            console.log('Form validity:', form.checkValidity());
            
            if (!form.checkValidity()) {
                console.log('Form is invalid, preventing submission');
                form.classList.add('was-validated');
                return;
            }
            
            console.log('Form is valid, submitting via AJAX');
            
            // Show loading state
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
            
            // Prepare form data
            const formData = new FormData(form);
            console.log('Form data:', formData);
            
            // Submit via AJAX
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Response is not JSON');
                }
                
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                
                if (data.success) {
                    // Show success SweetAlert
                    Swal.fire({
                        title: '🎉 Donation Submitted Successfully!',
                        html: `
                            <div class="text-center">
                                <i class="fas fa-check-circle text-success mb-3" style="font-size: 4rem;"></i>
                                <p class="mb-3">${data.message}</p>
                                <div class="alert alert-info">
                                    <strong>Thank you for your generous donation!</strong><br>
                                    Your contribution makes a real difference in our community.
                                </div>
                                <p class="text-muted small">
                                    You will receive an email confirmation once your donation is verified.<br>
                                    <strong>You will be redirected to our events page to explore more opportunities to help.</strong>
                                </p>
                            </div>
                        `,
                        icon: 'success',
                        confirmButtonText: 'View Events',
                        confirmButtonColor: '#2b3c6b',
                        allowOutsideClick: false,
                        allowEscapeKey: false,
                        showConfirmButton: true,
                        timer: null
                    }).then(() => {
                        // Redirect to confirmation page
                        if (data.redirect_url) {
                            window.location.href = data.redirect_url;
                        } else {
                            window.location.reload();
                        }
                    });
                } else {
                    // Show error SweetAlert
                    Swal.fire({
                        title: 'Upload Failed',
                        text: data.message || 'Please try again',
                        icon: 'error',
                        confirmButtonColor: '#2b3c6b'
                    });
                    
                    // Reset button
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i><span class="fw-bold">Upload Payment Proof</span><div class="small mt-1">Submit for verification</div>';
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                
                // Show error SweetAlert
                Swal.fire({
                    title: 'Upload Failed',
                    text: 'An error occurred while uploading. Please try again.',
                    icon: 'error',
                    confirmButtonColor: '#2b3c6b'
                });
                
                // Reset button
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<i class="fas fa-upload me-2"></i><span class="fw-bold">Upload Payment Proof</span><div class="small mt-1">Submit for verification</div>';
            });
        });
    }
});

/* END: donations/templates/donations/upload_payment_proof_minimal.html */
}
})();
