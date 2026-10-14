// Shared export calendar controls. Disabled fields are never submitted.
document.addEventListener('DOMContentLoaded', function () {
  const urlValues = new URLSearchParams(window.location.search);
  const modeFields = {
    day: ['day'],
    monthly: ['year', 'month'],
    quarterly: ['year', 'quarter'],
    semi_annual: ['year', 'half'],
    annual: ['year'],
    custom: ['custom'],
  };
  document.querySelectorAll('.report-period-fields').forEach(fieldset => {
    const selector = fieldset.querySelector('select[name="period"]');
    if (!selector) return;
    const fields = fieldset.querySelectorAll('[data-period-field]');
    // Restore values from the active query so periods do not reset to Q1 or January.
    fieldset.querySelectorAll('[data-period-field] input, [data-period-field] select').forEach(input => {
      const value = urlValues.get(input.name);
      if (value !== null) input.value = value;
    });
    function update() {
      const enabledFields = modeFields[selector.value] || [];
      fields.forEach(field => {
        const visible = enabledFields.includes(field.dataset.periodField);
        field.hidden = !visible;
        field.querySelectorAll('input,select').forEach(input => { input.disabled = !visible; });
      });
    }
    selector.addEventListener('change', update);
    update();
  });
});
