/**
 * Donations App JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize donation amount buttons if they exist
    const donationAmountBtns = document.querySelectorAll('.donation-amount-btn');
    const amountInput = document.querySelector('#id_amount');
    const customAmountBtn = document.querySelector('#custom-amount-btn');

    if (donationAmountBtns.length > 0 && amountInput) {
        // Handle preset amount buttons
        donationAmountBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const amount = this.dataset.amount;
                amountInput.value = amount;

                // Remove active class from all buttons
                donationAmountBtns.forEach(b => {
                    b.classList.remove('active');
                    b.classList.remove('btn-primary');
                    b.classList.add('btn-outline-primary');
                });

                // Add active class to clicked button
                this.classList.add('active');
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-primary');

                // Remove custom button active state
                if (customAmountBtn) {
                    customAmountBtn.classList.remove('active');
                    customAmountBtn.classList.remove('btn-secondary');
                    customAmountBtn.classList.add('btn-outline-secondary');
                }

                // Add visual feedback
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 150);
            });
        });

        // Handle custom amount button
        if (customAmountBtn) {
            customAmountBtn.addEventListener('click', function(e) {
                e.preventDefault();

                // Remove active state from preset buttons
                donationAmountBtns.forEach(b => {
                    b.classList.remove('active');
                    b.classList.remove('btn-primary');
                    b.classList.add('btn-outline-primary');
                });

                // Activate custom button
                this.classList.add('active');
                this.classList.remove('btn-outline-secondary');
                this.classList.add('btn-secondary');

                // Focus on amount input
                amountInput.focus();
                amountInput.select();
            });
        }

        // Handle manual input changes
        amountInput.addEventListener('input', function() {
            const currentValue = parseFloat(this.value);
            let matchFound = false;

            // Check if current value matches any preset
            donationAmountBtns.forEach(btn => {
                const btnAmount = parseFloat(btn.dataset.amount);
                if (currentValue === btnAmount) {
                    btn.click();
                    matchFound = true;
                }
            });

            // If no match, activate custom button
            if (!matchFound && customAmountBtn) {
                donationAmountBtns.forEach(b => {
                    b.classList.remove('active');
                    b.classList.remove('btn-primary');
                    b.classList.add('btn-outline-primary');
                });

                customAmountBtn.classList.add('active');
                customAmountBtn.classList.remove('btn-outline-secondary');
                customAmountBtn.classList.add('btn-secondary');
            }
        });

        // Format amount input with commas
        amountInput.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    }
    
    // Handle anonymous donation checkbox
    const anonymousCheckbox = document.querySelector('#id_is_anonymous');
    const donorNameField = document.querySelector('#id_donor_name').closest('.mb-3');
    const donorEmailField = document.querySelector('#id_donor_email').closest('.mb-3');
    
    if (anonymousCheckbox && donorNameField && donorEmailField) {
        // Function to toggle donor fields visibility
        const toggleDonorFields = () => {
            if (anonymousCheckbox.checked) {
                donorNameField.style.display = 'none';
                donorEmailField.style.display = 'none';
            } else {
                donorNameField.style.display = 'block';
                donorEmailField.style.display = 'block';
            }
        };
        
        // Initial state
        toggleDonorFields();
        
        // Listen for changes
        anonymousCheckbox.addEventListener('change', toggleDonorFields);
    }
    
    // Campaign progress animation
    const progressBars = document.querySelectorAll('.progress-bar');
    
    if (progressBars.length > 0) {
        progressBars.forEach(bar => {
            const targetWidth = bar.style.width;
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.transition = 'width 1s ease-in-out';
                bar.style.width = targetWidth;
            }, 100);
        });
    }
    
    // Handle donation status updates in dashboard
    const statusOptions = document.querySelectorAll('.status-option');
    
    if (statusOptions.length > 0) {
        statusOptions.forEach(option => {
            option.addEventListener('click', function(e) {
                e.preventDefault();
                
                const donationId = this.dataset.donationId;
                const status = this.dataset.status;
                const statusText = this.textContent.trim();
                
                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                // Send AJAX request to update status
                fetch(`/donations/donation/${donationId}/update-status/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken
                    },
                    body: `status=${status}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Update badge
                        const badge = document.querySelector(`.status-badge[data-donation-id="${donationId}"]`);
                        badge.textContent = data.new_status;
                        
                        // Update badge color
                        badge.classList.remove('bg-success', 'bg-warning', 'bg-danger', 'bg-secondary');
                        if (status === 'completed') {
                            badge.classList.add('bg-success');
                        } else if (status === 'pending') {
                            badge.classList.add('bg-warning');
                        } else if (status === 'failed') {
                            badge.classList.add('bg-danger');
                        } else {
                            badge.classList.add('bg-secondary');
                        }
                        
                        // Show success message
                        alert(data.message);
                    } else {
                        // Show error message
                        alert(`Error: ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while updating the donation status.');
                });
            });
        });
    }
}); 