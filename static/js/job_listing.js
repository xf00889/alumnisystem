/**
 * Job Listing Page JavaScript
 * Enhances the job listing page with interactive features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeShareFunctionality();
    initializeFilterAnimations();
    initializeJobCardInteractions();
    initializeTooltips();
    initializeSavedJobs();
    
    // Track page view for analytics
    trackPageView('job_listing');
});

/**
 * Initialize job sharing functionality
 */
function initializeShareFunctionality() {
    const shareButtons = document.querySelectorAll('.share-btn');
    const shareJobModal = new bootstrap.Modal(document.getElementById('shareJobModal'));
    const jobUrlInput = document.getElementById('jobUrl');
    const copyJobUrlBtn = document.getElementById('copyJobUrl');
    const copyMessage = document.getElementById('copyMessage');
    const shareLinkedIn = document.getElementById('shareLinkedIn');
    const shareTwitter = document.getElementById('shareTwitter');
    const shareFacebook = document.getElementById('shareFacebook');
    
    shareButtons.forEach(button => {
        button.addEventListener('click', function() {
            const jobTitle = this.getAttribute('data-job-title');
            const jobUrl = this.getAttribute('data-job-url');
            
            document.getElementById('shareJobModalLabel').textContent = `Share: ${jobTitle}`;
            jobUrlInput.value = jobUrl;
            
            // Set up social sharing links
            shareLinkedIn.href = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(jobUrl)}`;
            shareTwitter.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(`Check out this job opportunity: ${jobTitle}`)}&url=${encodeURIComponent(jobUrl)}`;
            shareFacebook.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(jobUrl)}`;
            
            shareJobModal.show();
        });
    });
    
    // Copy URL functionality
    copyJobUrlBtn.addEventListener('click', function() {
        jobUrlInput.select();
        document.execCommand('copy');
        
        copyMessage.textContent = 'URL copied to clipboard!';
        copyMessage.style.color = '#28a745';
        
        setTimeout(() => {
            copyMessage.textContent = '';
        }, 3000);
    });
}

/**
 * Initialize filter animations and interactions
 */
function initializeFilterAnimations() {
    const filterCard = document.querySelector('.filter-card');
    const filterForm = document.querySelector('.job-filters');
    
    if (filterCard && filterForm) {
        // Add subtle animation when filters change
        const formInputs = filterForm.querySelectorAll('input, select');
        formInputs.forEach(input => {
            input.addEventListener('change', function() {
                filterCard.classList.add('filter-changed');
                setTimeout(() => {
                    filterCard.classList.remove('filter-changed');
                }, 500);
            });
        });
        
        // Make filter card sticky on scroll
        let lastScrollTop = 0;
        window.addEventListener('scroll', function() {
            const st = window.pageYOffset || document.documentElement.scrollTop;
            if (st > lastScrollTop && st > 300) {
                // Scrolling down
                filterCard.classList.add('filter-card-compact');
            } else if (st < lastScrollTop) {
                // Scrolling up
                filterCard.classList.remove('filter-card-compact');
            }
            lastScrollTop = st <= 0 ? 0 : st;
        });
    }
}

/**
 * Initialize job card interactions
 */
function initializeJobCardInteractions() {
    const jobCards = document.querySelectorAll('.job-card');
    
    jobCards.forEach(card => {
        // Add hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 0.25rem 0.5rem rgba(0, 0, 0, 0.05)';
        });
        
        // Make entire card clickable (except for buttons)
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on a button or link
            if (e.target.tagName === 'BUTTON' || 
                e.target.tagName === 'A' || 
                e.target.closest('button') || 
                e.target.closest('a')) {
                return;
            }
            
            // Find the details link and navigate to it
            const detailsLink = this.querySelector('.details-btn');
            if (detailsLink && detailsLink.href) {
                window.location.href = detailsLink.href;
            }
        });
    });
    
    // Add animation to featured job cards
    const featuredCards = document.querySelectorAll('.featured-job-card');
    if (featuredCards.length > 0) {
        featuredCards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('animate-in');
        });
    }
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize saved jobs functionality
 */
function initializeSavedJobs() {
    // Get saved jobs from localStorage
    const savedJobs = getSavedJobs();
    
    // Add save job buttons if user is logged in
    const jobCards = document.querySelectorAll('.job-card');
    jobCards.forEach(card => {
        const jobId = card.getAttribute('data-job-id');
        if (jobId) {
            const actionsDiv = card.querySelector('.job-actions');
            if (actionsDiv) {
                const saveButton = document.createElement('button');
                saveButton.className = 'btn btn-outline-secondary btn-sm save-job-btn';
                saveButton.setAttribute('data-job-id', jobId);
                
                // Check if job is already saved
                const isSaved = savedJobs.includes(jobId);
                updateSaveButtonState(saveButton, isSaved);
                
                saveButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const jobId = this.getAttribute('data-job-id');
                    const isCurrentlySaved = savedJobs.includes(jobId);
                    
                    if (isCurrentlySaved) {
                        // Remove from saved jobs
                        const index = savedJobs.indexOf(jobId);
                        if (index > -1) {
                            savedJobs.splice(index, 1);
                        }
                        updateSaveButtonState(this, false);
                        ToastUtils.showInfo('Job removed from saved jobs');
                    } else {
                        // Add to saved jobs
                        savedJobs.push(jobId);
                        updateSaveButtonState(this, true);
                        ToastUtils.showSuccess('Job saved successfully');
                    }
                    
                    // Update localStorage
                    localStorage.setItem('savedJobs', JSON.stringify(savedJobs));
                });
                
                // Insert before the share button
                const shareButton = actionsDiv.querySelector('.share-btn');
                if (shareButton) {
                    actionsDiv.insertBefore(saveButton, shareButton);
                } else {
                    actionsDiv.appendChild(saveButton);
                }
            }
        }
    });
}

/**
 * Update save button state (saved/unsaved)
 */
function updateSaveButtonState(button, isSaved) {
    if (isSaved) {
        button.innerHTML = '<i class="fas fa-bookmark"></i>';
        button.setAttribute('title', 'Remove from saved jobs');
        button.classList.add('saved');
    } else {
        button.innerHTML = '<i class="far fa-bookmark"></i>';
        button.setAttribute('title', 'Save this job');
        button.classList.remove('saved');
    }
}

/**
 * Get saved jobs from localStorage
 */
function getSavedJobs() {
    const savedJobsString = localStorage.getItem('savedJobs');
    return savedJobsString ? JSON.parse(savedJobsString) : [];
}

/**
 * Track page view for analytics
 */
function trackPageView(page) {
    // This is a placeholder for actual analytics tracking
    console.log(`Page view tracked: ${page}`);
    
    // You could implement actual tracking here, e.g.:
    // if (typeof gtag === 'function') {
    //     gtag('event', 'page_view', {
    //         page_title: document.title,
    //         page_location: window.location.href,
    //         page_path: window.location.pathname
    //     });
    // }
} 