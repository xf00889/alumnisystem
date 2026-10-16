/** Audience-dependent entry field on the staff announcement form. */
(function () {
  'use strict';
  function init() {
    const type = document.getElementById('id_target_audience');
    const field = document.getElementById('id_target_value');
    const section = document.getElementById('announcementAudienceDetail');
    const label = document.getElementById('announcementAudienceLabel');
    const hint = document.getElementById('announcementAudienceHelp');
    if (!type || !field || !section || !label || !hint) return;

    const config = {
      BATCH: ['Graduation batch', 'e.g. 2024', 'Enter the four-digit graduation year. Only alumni from this batch are targeted.', null, 'numeric'],
      COLLEGE: ['College', 'Type the college name or code', 'Choose a NORSU college from the suggestions, e.g. College of Education or CTE.', 'announcement-colleges', 'text'],
      PROGRAM: ['Degree program', 'Type a degree name or program code', 'Choose an existing degree, e.g. Bachelor of Science in Information Technology (BSINT).', 'announcement-programs', 'text'],
      DEPARTMENT: ['Department or degree program', 'Type an existing program name or code', 'Choose the program or department the announcement is intended for.', 'announcement-programs', 'text']
    };
    function refresh(clear) {
      const settings = config[type.value];
      section.hidden = !settings;
      field.disabled = !settings;
      field.required = !!settings;
      if (clear) field.value = '';
      if (!settings) {
        field.removeAttribute('list');
        return;
      }
      label.textContent = settings[0] + ' *';
      field.placeholder = settings[1];
      hint.textContent = settings[2];
      field.setAttribute('inputmode', settings[4]);
      if (settings[3]) field.setAttribute('list', settings[3]);
      else field.removeAttribute('list');
    }
    type.addEventListener('change', function () { refresh(true); });
    refresh(false);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
