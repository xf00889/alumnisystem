/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--announcements-public-announcement-form-html") && !executed["announcements/public_announcement_form.html"]) {
executed["announcements/public_announcement_form.html"] = true;
/* BEGIN: announcements/public_announcement_form.html */

    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('announcementForm');
        const titleField = form.querySelector('#id_title');
        
        if (titleField) {
            titleField.focus();
        }
    });

/* END: announcements/public_announcement_form.html */
}
if (document.documentElement.classList.contains("fe-page--announcements-public-announcement-list-html") && !executed["announcements/public_announcement_list.html"]) {
executed["announcements/public_announcement_list.html"] = true;
/* BEGIN: announcements/public_announcement_list.html */

    document.addEventListener('DOMContentLoaded', function() {
        // Handle category filter checkboxes
        const categoryCheckboxes = document.querySelectorAll('.category-checkbox');
        const searchForm = document.getElementById('searchForm');
        
        categoryCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                searchForm.submit();
            });
        });
    });

/* END: announcements/public_announcement_list.html */
}
})();
