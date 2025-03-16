/**
 * Skill Matching JavaScript
 * Handles all functionality for the skill matching page
 */

// Sample data for demonstration
const SAMPLE_SKILLS = [
    { id: 1, name: 'JavaScript', type: 'TECH', proficiency: 4, years: 3, isPrimary: true },
    { id: 2, name: 'Python', type: 'TECH', proficiency: 3, years: 2, isPrimary: false },
    { id: 3, name: 'Communication', type: 'SOFT', proficiency: 5, years: 5, isPrimary: true },
    { id: 4, name: 'Project Management', type: 'SOFT', proficiency: 3, years: 2, isPrimary: false }
];

const SAMPLE_RECOMMENDATIONS = [
    { id: 101, name: 'React.js', type: 'TECH' },
    { id: 102, name: 'SQL', type: 'TECH' },
    { id: 103, name: 'Leadership', type: 'SOFT' }
];

const SAMPLE_JOBS = [
    {
        id: 1,
        title: 'Frontend Developer',
        company: 'TechCorp Inc.',
        matchScore: 85,
        matchedSkills: ['JavaScript', 'HTML', 'CSS'],
        missingSkills: ['React.js', 'TypeScript'],
        location: 'San Francisco, CA',
        type: 'Full Time',
        description: 'We are looking for a skilled Frontend Developer to join our team...',
        requirements: 'At least 2 years of experience with JavaScript and modern frameworks...',
        salary: '$80,000 - $100,000'
    },
    {
        id: 2,
        title: 'Python Developer',
        company: 'DataSystems LLC',
        matchScore: 75,
        matchedSkills: ['Python', 'SQL'],
        missingSkills: ['Django', 'Flask'],
        location: 'Remote',
        type: 'Full Time',
        description: 'Join our backend team to develop scalable applications...',
        requirements: 'Strong Python skills and database knowledge required...',
        salary: '$85,000 - $110,000'
    },
    {
        id: 3,
        title: 'Project Manager',
        company: 'Innovate Solutions',
        matchScore: 70,
        matchedSkills: ['Communication', 'Project Management'],
        missingSkills: ['Agile', 'Scrum'],
        location: 'Chicago, IL',
        type: 'Full Time',
        description: 'Lead projects from conception to completion...',
        requirements: 'PMP certification preferred. At least 3 years of experience...',
        salary: '$90,000 - $120,000'
    },
    {
        id: 4,
        title: 'Junior Web Developer',
        company: 'WebWorks Studio',
        matchScore: 65,
        matchedSkills: ['JavaScript', 'HTML'],
        missingSkills: ['CSS', 'React.js'],
        location: 'Austin, TX',
        type: 'Part Time',
        description: 'Great opportunity for a junior developer to grow their skills...',
        requirements: 'Basic knowledge of web development technologies...',
        salary: '$50,000 - $65,000'
    }
];

// Main initialization function
function initSkillMatching() {
    // Initialize components
    loadUserSkills();
    loadRecommendedSkills();
    loadJobMatches();
    updateProfileCompletion();
    
    // Set up event listeners
    setupEventListeners();
}

// Load user skills from API or sample data
function loadUserSkills() {
    const skillsContainer = document.querySelector('.skills-container');
    skillsContainer.innerHTML = '';
    
    if (SAMPLE_SKILLS.length === 0) {
        skillsContainer.innerHTML = '<p class="text-muted">No skills added yet. Add your first skill to improve job matches.</p>';
        return;
    }
    
    SAMPLE_SKILLS.forEach(skill => {
        const skillElement = createSkillBadge(skill);
        skillsContainer.appendChild(skillElement);
    });
}

// Create a skill badge element
function createSkillBadge(skill) {
    const badge = document.createElement('div');
    badge.className = 'skill-badge';
    badge.dataset.id = skill.id;
    
    const nameSpan = document.createElement('span');
    nameSpan.textContent = skill.name;
    
    const levelSpan = document.createElement('span');
    levelSpan.className = 'skill-level';
    levelSpan.textContent = skill.proficiency;
    
    const removeBtn = document.createElement('span');
    removeBtn.className = 'remove-skill';
    removeBtn.innerHTML = '&times;';
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeSkill(skill.id);
    });
    
    badge.appendChild(nameSpan);
    badge.appendChild(levelSpan);
    badge.appendChild(removeBtn);
    
    return badge;
}

// Remove a skill
function removeSkill(skillId) {
    // In a real app, this would call an API
    const index = SAMPLE_SKILLS.findIndex(s => s.id === skillId);
    if (index !== -1) {
        SAMPLE_SKILLS.splice(index, 1);
        loadUserSkills();
        updateProfileCompletion();
        loadJobMatches(); // Refresh job matches
    }
}

// Load recommended skills
function loadRecommendedSkills() {
    const container = document.querySelector('.recommendations-container');
    container.innerHTML = '';
    
    if (SAMPLE_RECOMMENDATIONS.length === 0) {
        container.innerHTML = '<p class="text-muted">No recommendations available.</p>';
        return;
    }
    
    SAMPLE_RECOMMENDATIONS.forEach(skill => {
        const badge = document.createElement('div');
        badge.className = 'skill-badge';
        badge.textContent = skill.name;
        badge.addEventListener('click', () => {
            openAddSkillModal(skill.name, skill.type);
        });
        
        container.appendChild(badge);
    });
}

// Open add skill modal with pre-filled data
function openAddSkillModal(name = '', type = 'TECH') {
    const modal = new bootstrap.Modal(document.getElementById('addSkillModal'));
    
    if (name) {
        document.getElementById('skillName').value = name;
    }
    
    if (type) {
        document.getElementById('skillType').value = type;
    }
    
    modal.show();
}

// Update profile completion percentage
function updateProfileCompletion() {
    const percentage = calculateProfileCompletion();
    const percentageElement = document.querySelector('.completion-percentage');
    const progressBar = document.querySelector('.progress-bar');
    
    percentageElement.textContent = `${percentage}%`;
    progressBar.style.width = `${percentage}%`;
}

// Calculate profile completion percentage
function calculateProfileCompletion() {
    // In a real app, this would be more complex
    // For demo, we'll base it on number of skills
    const skillCount = SAMPLE_SKILLS.length;
    let percentage = 0;
    
    if (skillCount >= 10) {
        percentage = 100;
    } else if (skillCount > 0) {
        percentage = Math.min(Math.round((skillCount / 10) * 100), 100);
    }
    
    return percentage;
}

// Load job matches
function loadJobMatches() {
    const container = document.getElementById('jobMatches');
    container.innerHTML = '';
    
    if (SAMPLE_JOBS.length === 0) {
        showEmptyState(container);
        return;
    }
    
    // Get current view mode
    const viewMode = document.querySelector('.btn-group .active').dataset.view || 'card';
    container.className = viewMode === 'list' ? 'list-view' : 'row g-4';
    
    SAMPLE_JOBS.forEach(job => {
        const jobElement = createJobCard(job);
        container.appendChild(jobElement);
    });
}

// Create job card
function createJobCard(job) {
    const template = document.getElementById('jobCardTemplate');
    const clone = document.importNode(template.content, true);
    
    // Set job details
    clone.querySelector('.job-title').textContent = job.title;
    clone.querySelector('.company-name').textContent = job.company;
    clone.querySelector('.match-score').textContent = `${job.matchScore}% Match`;
    
    // Set progress bar
    const progressBar = clone.querySelector('.progress-bar');
    progressBar.style.width = `${job.matchScore}%`;
    
    // Set matched skills
    const matchedSkillsContainer = clone.querySelector('.matched-skills .tags');
    job.matchedSkills.forEach(skill => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = skill;
        matchedSkillsContainer.appendChild(tag);
    });
    
    // Set missing skills
    const missingSkillsContainer = clone.querySelector('.missing-skills .tags');
    job.missingSkills.forEach(skill => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = skill;
        missingSkillsContainer.appendChild(tag);
    });
    
    // Set location and job type
    clone.querySelector('.location-text').textContent = job.location;
    clone.querySelector('.type-text').textContent = job.type;
    
    // Set button actions
    clone.querySelector('.view-details').addEventListener('click', () => {
        showJobDetails(job);
    });
    
    clone.querySelector('.apply-now').addEventListener('click', () => {
        applyForJob(job);
    });
    
    return clone;
}

// Show empty state when no jobs are found
function showEmptyState(container) {
    const emptyState = document.createElement('div');
    emptyState.className = 'empty-state';
    
    emptyState.innerHTML = `
        <div class="empty-state-icon">
            <i class="bi bi-search"></i>
        </div>
        <h4 class="empty-state-title">No Job Matches Found</h4>
        <p class="empty-state-description">
            We couldn't find any jobs matching your skills and preferences.
            Try adding more skills or adjusting your job preferences.
        </p>
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addSkillModal">
            Add More Skills
        </button>
    `;
    
    container.appendChild(emptyState);
}

// Show job details in modal
function showJobDetails(job) {
    const modal = new bootstrap.Modal(document.getElementById('jobDetailsModal'));
    const modalBody = document.querySelector('#jobDetailsModal .modal-body');
    const modalTitle = document.querySelector('#jobDetailsModal .modal-title');
    
    modalTitle.textContent = `${job.title} at ${job.company}`;
    
    modalBody.innerHTML = `
        <div class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">${job.title}</h5>
                <span class="badge match-score">${job.matchScore}% Match</span>
            </div>
            <p class="text-muted">${job.company}</p>
        </div>
        
        <div class="mb-4">
            <h6>Job Description</h6>
            <p>${job.description}</p>
        </div>
        
        <div class="mb-4">
            <h6>Requirements</h6>
            <p>${job.requirements}</p>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-4">
                <h6>Location</h6>
                <p><i class="bi bi-geo-alt me-2"></i>${job.location}</p>
            </div>
            <div class="col-md-4">
                <h6>Job Type</h6>
                <p><i class="bi bi-briefcase me-2"></i>${job.type}</p>
            </div>
            <div class="col-md-4">
                <h6>Salary Range</h6>
                <p><i class="bi bi-cash me-2"></i>${job.salary}</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <h6>Skills You Match</h6>
                <div class="tags mb-3">
                    ${job.matchedSkills.map(skill => `<span class="tag">${skill}</span>`).join('')}
                </div>
            </div>
            <div class="col-md-6">
                <h6>Skills to Develop</h6>
                <div class="tags">
                    ${job.missingSkills.map(skill => `<span class="tag">${skill}</span>`).join('')}
                </div>
            </div>
        </div>
    `;
    
    // Set apply button action
    document.getElementById('applyJob').onclick = () => {
        applyForJob(job);
        modal.hide();
    };
    
    modal.show();
}

// Apply for a job
function applyForJob(job) {
    // In a real app, this would call an API
    showToast(`Applied for ${job.title} at ${job.company}`, 'success');
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    
    // Create container if it doesn't exist
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
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
    
    document.querySelector('.toast-container').appendChild(toastElement);

    // Initialize and show toast
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Set up event listeners
function setupEventListeners() {
    // View toggle buttons
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active state
            document.querySelectorAll('.btn-group .btn').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            
            // Update view
            loadJobMatches();
        });
    });
    
    // Add skill form submission
    document.getElementById('saveSkill').addEventListener('click', function() {
        const form = document.getElementById('addSkillForm');
        
        // Basic validation
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        // Get form values
        const name = document.getElementById('skillName').value;
        const type = document.getElementById('skillType').value;
        const proficiency = parseInt(document.getElementById('proficiency').value);
        const years = parseInt(document.getElementById('yearsExperience').value);
        const isPrimary = document.getElementById('isPrimary').checked;
        
        // Add skill (in a real app, this would call an API)
        const newSkill = {
            id: Date.now(), // Generate a unique ID
            name,
            type,
            proficiency,
            years,
            isPrimary
        };
        
        SAMPLE_SKILLS.push(newSkill);
        
        // Reset form and close modal
        form.reset();
        bootstrap.Modal.getInstance(document.getElementById('addSkillModal')).hide();
        
        // Update UI
        loadUserSkills();
        updateProfileCompletion();
        loadJobMatches(); // Refresh job matches
        
        showToast(`Skill "${name}" added successfully`, 'success');
    });
    
    // Job preferences form submission
    document.getElementById('jobPreferencesForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // In a real app, this would call an API
        showToast('Job preferences updated successfully', 'success');
        
        // Refresh job matches
        loadJobMatches();
    });
}

// Export functions for global access
window.initSkillMatching = initSkillMatching;
window.openAddSkillModal = openAddSkillModal;