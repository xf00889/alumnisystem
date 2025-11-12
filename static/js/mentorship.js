// Mentor Search and Request Functionality

function initMentorSearch() {
    const searchForm = document.getElementById('mentorSearchForm');
    const resultsContainer = document.getElementById('searchResults');
    const requestModal = new bootstrap.Modal(document.getElementById('mentorshipRequestModal'));
    
    // Handle search form submission
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await searchMentors();
    });
    
    // Handle mentorship request submission (guard against missing button)
    const submitRequestBtn = document.getElementById('submitRequest');
    if (submitRequestBtn) {
        submitRequestBtn.addEventListener('click', async () => {
            await submitMentorshipRequest();
            requestModal.hide();
        });
    }
    
    // Handle view toggle
    const gridViewBtn = document.getElementById('gridView');
    const listViewBtn = document.getElementById('listView');
    
    if (gridViewBtn && listViewBtn) {
        gridViewBtn.addEventListener('click', () => {
            setViewMode('grid');
            gridViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
        });
        
        listViewBtn.addEventListener('click', () => {
            setViewMode('list');
            listViewBtn.classList.add('active');
            gridViewBtn.classList.remove('active');
        });
    }
}

async function searchMentors() {
    const form = document.getElementById('mentorSearchForm');
    const resultsContainer = document.getElementById('searchResults');
    const loadingAlert = createLoadingAlert();
    
    resultsContainer.innerHTML = '';
    resultsContainer.appendChild(loadingAlert);
    
    try {
        // Get CSRF token
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const response = await fetch('/mentorship/api/mentors/?' + new URLSearchParams({
            expertise: form.expertise.value || '',
            availability: form.availability.value || '',
            experienced: form.experienced.checked || false,
            sort: form.sort.value || 'experience'
        }), {
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response');
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Search failed');
        }
        
        const data = await response.json();
        
        // Check if data is in the expected format
        if (!Array.isArray(data)) {
            displaySearchResults([]);
            return;
        }
        
        displaySearchResults(data);
        
    } catch (error) {
        console.error('Search error:', error);
        displayError('Failed to search mentors. Please try again. Error: ' + error.message);
    }
}

function displaySearchResults(mentors) {
    const resultsContainer = document.getElementById('searchResults');
    const template = document.getElementById('mentorCardTemplate');
    const resultsHeader = document.getElementById('resultsHeader');
    const resultsCount = document.getElementById('resultsCount');
    
    resultsContainer.innerHTML = '';
    
    if (!Array.isArray(mentors) || mentors.length === 0) {
        resultsHeader.classList.add('d-none');
        resultsContainer.innerHTML = `
            <div class="col-12">
                <div class="empty-state text-center py-5">
                    <div class="empty-state-icon mb-4">
                        <i class="fas fa-search"></i>
                    </div>
                    <h3 class="empty-state-title">No Mentors Found</h3>
                    <p class="empty-state-description text-muted mb-4">
                        We couldn't find any mentors matching your criteria. Try adjusting your search filters or broadening your search terms.
                    </p>
                    <div class="empty-state-action">
                        <button class="btn btn-outline-primary" onclick="document.getElementById('expertise').value = ''; document.getElementById('mentorSearchForm').dispatchEvent(new Event('submit'))">
                            <i class="fas fa-redo me-2"></i>Reset Search
                        </button>
                    </div>
                </div>
            </div>
        `;
        return;
    }
    
    // Update results count and show header
    if (resultsHeader && resultsCount) {
        resultsCount.textContent = mentors.length;
        resultsHeader.classList.remove('d-none');
    }
    
    // Get current view mode
    const viewMode = localStorage.getItem('mentorViewMode') || 'grid';
    
    // Apply view mode to container
    if (viewMode === 'list') {
        resultsContainer.classList.add('list-view');
        document.getElementById('listView').classList.add('active');
        document.getElementById('gridView').classList.remove('active');
    } else {
        resultsContainer.classList.remove('list-view');
        document.getElementById('gridView').classList.add('active');
        document.getElementById('listView').classList.remove('active');
    }
    
    mentors.forEach(mentor => {
        const card = template.content.cloneNode(true);
        
        // Fill in mentor details
        card.querySelector('.card-title').textContent = mentor.user.full_name;
        card.querySelector('.mentor-position').textContent = mentor.user.current_position || 'Mentor';
        
        // Set avatar
        const avatarImg = card.querySelector('.mentor-avatar');
        avatarImg.src = mentor.user.avatar || '/static/images/default-avatar.png';
        avatarImg.alt = `${mentor.user.full_name}'s profile picture`;
        avatarImg.onerror = function() {
            this.src = '/static/images/default-avatar.png';
        };
        
        // Add expertise tags
        const tagsContainer = card.querySelector('.tags');
        if (mentor.expertise_list && Array.isArray(mentor.expertise_list)) {
            mentor.expertise_list.forEach(expertise => {
                if (expertise && expertise.trim()) {
                    const tag = document.createElement('span');
                    tag.className = 'badge bg-light text-dark me-1 mb-1';
                    tag.textContent = expertise.trim();
                    tagsContainer.appendChild(tag);
                }
            });
        } else if (mentor.expertise_areas) {
            // Fallback to expertise_areas if expertise_list is not available
            mentor.expertise_areas.split(',').forEach(expertise => {
                if (expertise && expertise.trim()) {
                    const tag = document.createElement('span');
                    tag.className = 'badge bg-light text-dark me-1 mb-1';
                    tag.textContent = expertise.trim();
                    tagsContainer.appendChild(tag);
                }
            });
        }
        
        // Set availability badge
        const availabilityBadge = card.querySelector('.availability-badge');
        availabilityBadge.textContent = formatAvailabilityStatus(mentor.availability_status);
        availabilityBadge.className = `availability-badge ${getAvailabilityClass(mentor.availability_status)}`;
        
        // Set bio/description
        card.querySelector('.mentor-bio').textContent = mentor.mentoring_experience || 
            'Experienced mentor ready to help you achieve your career goals.';
        
        // Set up request button
        const requestBtn = card.querySelector('.request-btn');
        
        // Get current user ID from meta tag
        const currentUserId = document.querySelector('meta[name="user-id"]')?.content;
        
        if (currentUserId && mentor.user.id === parseInt(currentUserId)) {
            // This is the current user's mentor profile
            requestBtn.textContent = 'This is Your Profile';
            requestBtn.classList.remove('btn-primary');
            requestBtn.classList.add('btn-secondary');
            requestBtn.disabled = true;
        } else if (mentor.has_requested) {
            // User has already sent a request to this mentor
            requestBtn.innerHTML = '<i class="fas fa-check me-2"></i>Request Sent';
            requestBtn.classList.remove('btn-primary');
            requestBtn.classList.add('btn-secondary');
            requestBtn.disabled = true;
        } else if (mentor.accepting_mentees) {
            requestBtn.addEventListener('click', () => openRequestModal(mentor));
        } else {
            requestBtn.textContent = 'Not Accepting Mentees';
            requestBtn.classList.remove('btn-primary');
            requestBtn.classList.add('btn-secondary');
            requestBtn.disabled = true;
        }
        
        resultsContainer.appendChild(card);
    });
}

function setViewMode(mode) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (mode === 'list') {
        resultsContainer.classList.add('list-view');
    } else {
        resultsContainer.classList.remove('list-view');
    }
    
    // Save preference
    localStorage.setItem('mentorViewMode', mode);
}

function formatAvailabilityStatus(status) {
    const statusMap = {
        'AVAILABLE': 'Available',
        'LIMITED': 'Limited Availability',
        'UNAVAILABLE': 'Currently Unavailable'
    };
    return statusMap[status] || status;
}

function getAvailabilityClass(status) {
    const classMap = {
        'AVAILABLE': 'bg-success',
        'LIMITED': 'bg-warning text-dark',
        'UNAVAILABLE': 'bg-danger'
    };
    return classMap[status] || 'bg-secondary';
}

function openRequestModal(mentor) {
    const modal = document.getElementById('mentorshipRequestModal');
    if (!modal) {
        // If modal is missing, show a toast and bail gracefully
        showErrorMessage('Mentorship request modal not found on this page.');
        return;
    }

    const form = document.getElementById('mentorshipRequestForm');
    const modalBody = modal.querySelector('.modal-body');
    let errorContainer = modal.querySelector('.modal-body .alert');

    // Create alert container if it doesn't exist
    if (!errorContainer && modalBody) {
        errorContainer = document.createElement('div');
        errorContainer.className = 'alert alert-info';
        modalBody.prepend(errorContainer);
    }

    // Reset form and error state
    if (form) form.reset();
    if (errorContainer) {
        errorContainer.className = 'alert alert-info';
        errorContainer.innerHTML = '<i class="fas fa-info-circle me-2"></i>Please provide details about what you\'re looking to gain from this mentorship. Be specific about your goals and what skills you\'re hoping to develop.';
    }

    // Set mentor ID (create input if missing)
    let mentorIdInput = document.getElementById('mentorId');
    if (!mentorIdInput && form) {
        mentorIdInput = document.createElement('input');
        mentorIdInput.type = 'hidden';
        mentorIdInput.id = 'mentorId';
        mentorIdInput.name = 'mentorId';
        form.prepend(mentorIdInput);
    }
    if (mentorIdInput) mentorIdInput.value = mentor.id;

    // Pre-fill skills field with mentor's expertise if available
    const skillsInput = document.getElementById('skillsSeeking');
    if (skillsInput) {
        if (mentor.expertise_list && Array.isArray(mentor.expertise_list)) {
            skillsInput.value = mentor.expertise_list.slice(0, 3).join(', ');
        } else if (mentor.expertise_areas) {
            skillsInput.value = mentor.expertise_areas.split(',').slice(0, 3).join(', ');
        }
    }

    // Add mentor name to modal title
    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = `<i class="fas fa-handshake me-2"></i>Request Mentorship from ${mentor.user.full_name}`;
    }

    new bootstrap.Modal(modal).show();
}

async function submitMentorshipRequest() {
    const form = document.getElementById('mentorshipRequestForm');
    const submitButton = document.getElementById('submitRequest');
    // Find an existing alert in the modal body; create one if absent
    const modal = document.getElementById('mentorshipRequestModal');
    const modalBody = modal ? modal.querySelector('.modal-body') : null;
    let errorContainer = modalBody ? modalBody.querySelector('.alert') : null;
    if (!errorContainer && modalBody) {
        errorContainer = document.createElement('div');
        errorContainer.className = 'alert alert-info';
        modalBody.prepend(errorContainer);
    }
    
    // Validate form fields
    if (!form || !submitButton) return;
    if (!form.skillsSeeking.value.trim() || !form.goals.value.trim() || !form.message.value.trim()) {
        if (errorContainer) {
            errorContainer.className = 'alert alert-danger';
            errorContainer.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Please fill out all required fields.';
        }
        return;
    }
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
    
    try {
        const csrftoken = getCookie('csrftoken');
        
        const response = await fetch('/mentorship/api/requests/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                mentor_id: form.mentorId.value,
                skills_seeking: form.skillsSeeking.value.trim(),
                goals: form.goals.value.trim(),
                message: form.message.value.trim()
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to submit request');
        }
        
        // Success handling
        const modal = bootstrap.Modal.getInstance(document.getElementById('mentorshipRequestModal'));
        modal.hide();
        
        showSuccessMessage('Mentorship request sent successfully!');
        form.reset();
        
    } catch (error) {
        console.error('Request error:', error);
        if (errorContainer) {
            errorContainer.className = 'alert alert-danger';
            errorContainer.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${error.message}`;
        } else {
            showErrorMessage(error.message);
        }
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Send Request';
    }
}

// Utility Functions

function createLoadingAlert() {
    const alert = document.createElement('div');
    alert.className = 'col-12';
    alert.innerHTML = `
        <div class="empty-state text-center py-5">
            <div class="d-flex justify-content-center mb-4">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
            <h3 class="empty-state-title">Searching for Mentors</h3>
            <p class="empty-state-description text-muted">
                Please wait while we find the best mentors for you...
            </p>
        </div>
    `;
    return alert;
}

function displayError(message) {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = `
        <div class="col-12">
            <div class="empty-state text-center py-5">
                <div class="empty-state-icon bg-danger mb-4">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3 class="empty-state-title">Search Error</h3>
                <p class="empty-state-description text-muted mb-4">
                    ${message}
                </p>
                <div class="empty-state-action">
                    <button class="btn btn-primary" onclick="document.getElementById('mentorSearchForm').dispatchEvent(new Event('submit'))">
                        <i class="fas fa-redo me-2"></i>Try Again
                    </button>
                </div>
            </div>
        </div>
    `;
}

function showSuccessMessage(message) {
    createToast('success', message);
}

function showErrorMessage(message) {
    createToast('danger', message);
}

function createToast(type, message) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}