/* Manage pending mentorship requests without native confirmations or toast spam. */
(() => {
  'use strict';
  const modal = document.getElementById('menteeWithdrawModal');
  if (!modal) return;
  const confirm = document.getElementById('menteeWithdrawConfirm');
  const errorNode = document.getElementById('menteeWithdrawError');
  const description = document.getElementById('menteeWithdrawDescription');
  let url = null;
  modal.addEventListener('show.bs.modal', event => {
    const trigger = event.relatedTarget;
    url = trigger?.dataset.menteeWithdrawUrl || null;
    description.textContent = `Withdraw your pending request to ${trigger?.dataset.menteeWithdrawName || 'this mentor'}? You can request again later if applications are open.`;
    errorNode.hidden = true;
    errorNode.textContent = '';
  });
  document.addEventListener('click', event => {
    const trigger = event.target.closest('[data-mentee-withdraw-url]');
    if (!trigger) return;
    bootstrap.Modal.getOrCreateInstance(modal).show(trigger);
  });
  confirm.addEventListener('click', async () => {
    if (!url) return;
    confirm.disabled = true;
    try {
      const csrf = document.querySelector('#menteeSecurityForm [name="csrfmiddlewaretoken"]')?.value || '';
      const response = await fetch(url, {method:'POST',credentials:'same-origin',headers:{'X-CSRFToken':csrf,Accept:'application/json'}});
      const type = response.headers.get('Content-Type') || '';
      const result = type.includes('json') ? await response.json() : {};
      if (!response.ok || !result.success) throw new Error(result.error || 'Unable to withdraw this request. Refresh your session and try again.');
      location.reload();
    } catch (error) {
      errorNode.textContent = error.message;
      errorNode.hidden = false;
      confirm.disabled = false;
    }
  });
})();
