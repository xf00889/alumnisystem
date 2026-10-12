/* Accessible, auditable fraud review. Never uses native prompt/confirm. */
(function () {
  'use strict';
  function start() {
    const dialog = document.getElementById('fraud-review-dialog');
    const form = document.getElementById('fraud-review-form');
    if (!dialog || !form) return;
    const error = document.getElementById('fraud-review-error');
    const button = document.getElementById('fraud-review-submit');
    let targetUrl = '';
    document.querySelectorAll('[data-review-alert]').forEach(trigger => trigger.addEventListener('click', function () {
      targetUrl = trigger.dataset.reviewUrl;
      document.getElementById('fraud-review-subtitle').textContent = trigger.dataset.reviewLabel;
      form.reset(); error.hidden = true; error.textContent = '';
      dialog.showModal();
    }));
    function close() { dialog.close(); }
    document.getElementById('fraud-review-close').addEventListener('click', close);
    document.getElementById('fraud-review-cancel').addEventListener('click', close);
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      if (!targetUrl || !document.getElementById('fraud-review-notes').value.trim()) {
        error.textContent = 'Record review notes before saving.'; error.hidden = false; return;
      }
      const token = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
      if (!token) { error.textContent = 'Security token missing. Refresh this page.'; error.hidden = false; return; }
      button.disabled = true; button.textContent = 'Saving…'; error.hidden = true;
      try {
        const response = await fetch(targetUrl, {method:'POST',credentials:'same-origin',
          headers:{'X-CSRFToken':token,'X-Requested-With':'XMLHttpRequest'}, body:new URLSearchParams(new FormData(form))});
        const result = await response.json();
        if (!response.ok || result.status !== 'success') throw new Error(result.message || 'Unable to save review.');
        window.location.reload();
      } catch (exc) {error.textContent = exc.message || 'Unable to save review.'; error.hidden = false;}
      finally {button.disabled = false; button.textContent = 'Save decision';}
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
