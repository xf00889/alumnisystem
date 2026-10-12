/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--landing-events-html") && !executed["landing/events.html"]) {
executed["landing/events.html"] = true;
/* BEGIN: landing/events.html */

document.addEventListener('DOMContentLoaded', function() {
    // Set progress bar widths
    document.querySelectorAll('.progress-bar[data-width]').forEach(function(bar) {
        const width = bar.getAttribute('data-width');
        bar.style.width = width + '%';
    });
    
    // Campaign Modal
    const campaignModal = document.getElementById('campaignModal');
    
    campaignModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        
        // Extract data from button attributes
        const title = button.getAttribute('data-campaign-title');
        const description = button.getAttribute('data-campaign-description');
        const goal = button.getAttribute('data-campaign-goal');
        const current = button.getAttribute('data-campaign-current');
        const progress = button.getAttribute('data-campaign-progress');
        const status = button.getAttribute('data-campaign-status');
        const date = button.getAttribute('data-campaign-date');
        const url = button.getAttribute('data-campaign-url');
        const image = button.getAttribute('data-campaign-image');
        
        // Update modal content
        document.getElementById('campaignTitle').textContent = title;
        document.getElementById('campaignDescription').textContent = description;
        document.getElementById('campaignGoal').textContent = '₱' + goal;
        document.getElementById('campaignCurrent').textContent = '₱' + current;
        document.getElementById('campaignProgress').textContent = progress + '%';
        document.getElementById('campaignStatus').textContent = status;
        document.getElementById('campaignDate').innerHTML = '<i class="fas fa-calendar-alt me-1"></i>' + date;
        document.getElementById('campaignProgressBar').style.width = progress + '%';
        
        // Set the donate link URL
        const donateLink = document.getElementById('campaignDonateLink');
        if (url) {
            donateLink.href = url;
        } else {
            donateLink.href = 'javascript:void(0)';
        }
        
        // Handle campaign image
        if (image) {
            document.getElementById('campaignImage').src = image;
            document.getElementById('campaignImageContainer').style.display = 'block';
        } else {
            document.getElementById('campaignImageContainer').style.display = 'none';
        }
    });
    
    // Event Modal
    const eventModal = document.getElementById('eventModal');
    
    eventModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        
        // Extract data from button attributes
        const title = button.getAttribute('data-event-title');
        const description = button.getAttribute('data-event-description');
        const date = button.getAttribute('data-event-date');
        const time = button.getAttribute('data-event-time');
        const location = button.getAttribute('data-event-location');
        const status = button.getAttribute('data-event-status');
        const image = button.getAttribute('data-event-image');
        
        // Update modal content
        document.getElementById('eventTitle').textContent = title;
        document.getElementById('eventDescription').textContent = description;
        document.getElementById('eventDate').innerHTML = '<i class="fas fa-calendar-alt me-1"></i>' + date;
        document.getElementById('eventDateDetail').textContent = date;
        document.getElementById('eventTimeDetail').textContent = time;
        document.getElementById('eventStatus').textContent = status;
        
        // Handle location
        if (location && location.trim() !== '') {
            document.getElementById('eventLocationDetail').textContent = location;
            document.getElementById('eventLocationRow').style.display = 'block';
        } else {
            document.getElementById('eventLocationRow').style.display = 'none';
        }
        
        // Handle event image
        if (image) {
            document.getElementById('eventImage').src = image;
            document.getElementById('eventImageContainer').style.display = 'block';
        } else {
            document.getElementById('eventImageContainer').style.display = 'none';
        }
    });
    
    // Announcement Modal
    const announcementModal = document.getElementById('announcementModal');
    
    announcementModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        
        // Extract data from button attributes
        const title = button.getAttribute('data-announcement-title');
        const description = button.getAttribute('data-announcement-description');
        const date = button.getAttribute('data-announcement-date');
        const category = button.getAttribute('data-announcement-category');
        const priority = button.getAttribute('data-announcement-priority');
        
        // Update modal content
        document.getElementById('announcementTitle').textContent = title;
        document.getElementById('announcementDescription').textContent = description;
        document.getElementById('announcementDate').textContent = 'Posted on ' + date;
        document.getElementById('announcementCategory').textContent = category || 'General';
        document.getElementById('announcementPriority').textContent = priority || 'Medium';
    });
    
    // reCAPTCHA callbacks
    window.onRecaptchaSuccess = function(token) {
        console.log('reCAPTCHA verification successful');
    };
    
    window.onRecaptchaExpired = function() {
        console.log('reCAPTCHA token expired');
    };
    
    window.onRecaptchaError = function() {
        console.log('reCAPTCHA error occurred');
    };
    
});

/* END: landing/events.html */
}
})();
