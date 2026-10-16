/* Accessible initial-role selector; role validation stays on the server. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    const selector = document.getElementById('id_account_type');
    const campusFields = document.getElementById('newCoordinatorCampusFields');
    const helper = document.getElementById('accountTypeHelp');
    if (!selector || !campusFields) return;
    const descriptions = {
      standard: 'Standard user: completes the normal alumni registration.',
      alumni: 'Alumni: completes the normal alumni registration.',
      mentor: 'Mentor: requires profile completion and verification before being listed.',
      hr: 'HR: restricted Career Services workspace, without staff or system access.',
      alumni_coordinator: 'Alumni Coordinator: restricted coordinator workspace for assigned campuses only.',
      admin: 'Administrator: staff access across the administration panel. Assign only to trusted users.',
      superuser: 'Superuser: unrestricted access to the entire system. Assign with extreme care.'
    };
    function sync() {
      const isCoordinator = selector.value === 'alumni_coordinator';
      campusFields.hidden = !isCoordinator;
      campusFields.querySelectorAll('input[type="checkbox"]').forEach(input => { input.disabled = !isCoordinator; });
      if (helper) helper.textContent = descriptions[selector.value] || descriptions.standard;
    }
    selector.addEventListener('change', sync);
    sync();
  });
}());
