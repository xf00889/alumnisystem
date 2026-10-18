(function () {
  'use strict';
  function init() {
    const form = document.getElementById('directoryEmployabilityForm');
    if (!form) return;
    const select = form.querySelector('#directoryEmployabilityPeriod');
    if (!select) return;
    function refresh() {
      form.querySelectorAll('[data-employment-period-field]').forEach(field => {
        field.hidden = field.dataset.employmentPeriodField !== select.value;
      });
    }
    select.addEventListener('change', refresh);
    refresh();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else init();
})();
