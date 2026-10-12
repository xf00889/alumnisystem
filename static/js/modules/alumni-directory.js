/* Consolidated module JS. Runs only the template-specific initializer present on this page. */
(function () {
const executed = (window.__alumniModuleScriptExecuted ||= Object.create(null));
if (document.documentElement.classList.contains("fe-page--alumni-directory-tabular-alumni-list-html") && !executed["alumni_directory/tabular_alumni_list.html"]) {
executed["alumni_directory/tabular_alumni_list.html"] = true;
/* BEGIN: alumni_directory/tabular_alumni_list.html */

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize any needed JavaScript here
    });

/* END: alumni_directory/tabular_alumni_list.html */
}
})();
