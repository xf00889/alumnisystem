/* Mentor decisions share a single, CSRF-protected, named Django endpoint.
 * Do not assume every server/CDN failure returns JSON. */
(() => {
  'use strict';
  const actionSelector = '[data-mentorship-status-action]';
  const getToken = () => {
    const supplied = document.querySelector('[name="csrfmiddlewaretoken"]')?.value ||
      document.querySelector('meta[name="csrf-token"]')?.content || '';
    if (supplied && supplied !== 'NOTPROVIDED') return supplied;
    const found = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return found ? decodeURIComponent(found[1]) : '';
  };

  function feedback(row, message, isError = true) {
    if (!row) return;
    let node = row.querySelector('[data-mentorship-request-feedback]');
    if (!node) {
      node = document.createElement('p');
      node.dataset.mentorshipRequestFeedback = '';
      node.className = 'mentorship-request-feedback';
      row.appendChild(node);
    }
    node.textContent = message;
    node.classList.toggle('is-error', isError);
    node.setAttribute('role', isError ? 'alert' : 'status');
  }

  let dialog;
  function confirmDecision(verb, name) {
    if (!dialog) {
      dialog = document.createElement('dialog');
      dialog.className = 'mentorship-decision-dialog';
      dialog.setAttribute('aria-labelledby', 'mentorship-decision-heading');
      dialog.innerHTML = `
        <div class="mentorship-decision-dialog__body">
          <h2 id="mentorship-decision-heading">Confirm decision</h2>
          <p data-mentorship-decision-description></p>
        </div>
        <div class="mentorship-decision-dialog__actions">
          <button type="button" data-decision-cancel>Keep pending</button>
          <button type="button" data-decision-confirm>Confirm</button>
        </div>`;
      document.body.appendChild(dialog);
      dialog.querySelector('[data-decision-cancel]').addEventListener('click', () => dialog.close('cancel'));
      dialog.querySelector('[data-decision-confirm]').addEventListener('click', () => dialog.close('confirm'));
      dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close('cancel'); });
    }
    dialog.querySelector('[data-mentorship-decision-description]').textContent =
      `Are you sure you want to ${verb.toLowerCase()} this mentorship request${name ? ` from ${name}` : ''}?`;
    dialog.querySelector('[data-decision-confirm]').textContent = verb;
    dialog.querySelector('[data-decision-confirm]').classList.toggle('is-reject', verb === 'Reject');
    return new Promise(resolve => {
      const finish = () => {
        dialog.removeEventListener('close', finish);
        resolve(dialog.returnValue === 'confirm');
      };
      dialog.addEventListener('close', finish);
      dialog.showModal();
      dialog.querySelector('[data-decision-cancel]').focus();
    });
  }

  async function processDecision(button) {
    const status = button.dataset.mentorshipStatus;
    const target = button.dataset.mentorshipStatusUrl;
    if (!['APPROVED', 'REJECTED'].includes(status) || !target) return;
    const row = button.closest('[data-mentorship-request-row]') || button.parentElement;
    const label = status === 'APPROVED' ? 'Accept' : 'Reject';
    if (!await confirmDecision(label, '')) return;
    const csrf = getToken();
    if (!csrf) {
      feedback(row, 'The security token is missing. Reload this page and try again.');
      return;
    }
    const actions = row.querySelectorAll(actionSelector);
    if ([...actions].some(action => action.dataset.mentorshipProcessing === 'true')) return;
    actions.forEach(action => { action.disabled = true; action.dataset.mentorshipProcessing = 'true'; });
    feedback(row, 'Saving your decision…', false);
    try {
      const payload = new URLSearchParams({status});
      const response = await fetch(target, {
        method: 'POST',
        credentials: 'same-origin',
        redirect: 'follow',
        headers: {
          'X-CSRFToken': csrf,
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        },
        body: payload.toString()
      });
      const contentType = response.headers.get('content-type') || '';
      // A reverse-proxy 403 or a login redirect often returns HTML, not JSON.
      const data = contentType.includes('application/json') ? await response.json() : null;
      if (response.redirected || !response.ok || !data || !data.status) {
        let message = data?.detail || data?.error || data?.message;
        if (!message && response.redirected) message = 'Your login may have expired. Sign in again and retry.';
        if (!message && response.status === 403) message = 'The server denied this request. Check your session or ask an administrator to inspect the security logs.';
        if (!message) message = 'Could not update this request. Please refresh the page and retry.';
        throw new Error(message);
      }
      if (data.status !== status) throw new Error('The server did not confirm the requested status.');
      feedback(row, data.message || 'Request updated successfully.', false);
      window.location.reload();
    } catch (error) {
      console.error('Unable to update mentorship request:', error);
      feedback(row, error.message || 'Unable to save this decision. Please try again.');
    } finally {
      actions.forEach(action => { action.disabled = false; delete action.dataset.mentorshipProcessing; });
    }
  }

  document.addEventListener('click', event => {
    const button = event.target.closest(actionSelector);
    if (!button || button.disabled) return;
    event.preventDefault();
    processDecision(button);
  });
})();
