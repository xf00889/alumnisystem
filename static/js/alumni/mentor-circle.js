(() => {
  'use strict';
  const root = document.getElementById('mentorCircle');
  if (!root) return;
  const activity = document.getElementById('circleActivity');
  const status = document.getElementById('circleFeedback');
  const csrf = document.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
  let pending = false;
  const flash = (message, error = false) => {
    status.hidden = !message;
    status.textContent = message;
    status.classList.toggle('is-error', error);
  };
  const request = async (url, data) => {
    const response = await fetch(url, {method: 'POST', body: data || new FormData(), credentials: 'same-origin', headers: {'X-CSRFToken': csrf, 'Accept': 'application/json'}});
    const type = response.headers.get('content-type') || '';
    const result = type.includes('application/json') ? await response.json() : {};
    if (!response.ok || !result.success) {
      const firstField = Object.values(result.fields || {})[0];
      throw new Error((firstField && firstField[0] && firstField[0].message) || result.error || `The server returned ${response.status}. Please reload or sign in again.`);
    }
    return result;
  };
  async function refresh(scroll = false) {
    if (pending) return;
    pending = true;
    try {
      const response = await fetch(root.dataset.activityUrl, {credentials: 'same-origin', headers: {'Accept': 'text/html'}});
      if (!response.ok) throw new Error('Could not load group activity.');
      activity.innerHTML = await response.text();
      if (scroll) activity.scrollTop = activity.scrollHeight;
    } catch (error) { flash(error.message, true); }
    finally {pending = false;}
  }
  const sendForm = document.getElementById('circleMessageForm');
  sendForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!sendForm.reportValidity()) return;
    const submit = sendForm.querySelector('button[type="submit"]');
    const originalLabel = submit.innerHTML;
    submit.disabled = true;
    submit.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Sending';
    flash('');
    try {
      await request(root.dataset.sendUrl, new FormData(sendForm));
      sendForm.reset();
      await refresh(true);
    } catch (error) {flash(error.message, true);}
    finally {submit.disabled = false; submit.innerHTML = originalLabel;}
  });
  const meetingForm = document.getElementById('circleMeetingForm');
  meetingForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!meetingForm.reportValidity()) return;
    const button = meetingForm.querySelector('button[type="submit"]');
    const errorNode = document.getElementById('circleMeetingError');
    errorNode.hidden = true;
    const originalLabel = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Saving';
    try {
      const result = await request(root.dataset.scheduleUrl, new FormData(meetingForm));
      bootstrap.Modal.getOrCreateInstance(document.getElementById('circleMeetingModal')).hide();
      flash(`Meeting scheduled for ${result.participants} group member(s).`);
      window.location.reload();
    } catch (error) {errorNode.hidden = false; errorNode.textContent = error.message;}
    finally {button.disabled = false; button.innerHTML = originalLabel;}
  });
  let cancelUrl = null;
  const cancelModal = document.getElementById('circleCancelModal');
  root.addEventListener('click', (event) => {
    const button = event.target.closest('[data-circle-cancel-url]');
    if (!button || !cancelModal) return;
    cancelUrl = button.dataset.circleCancelUrl;
    document.getElementById('circleCancelDescription').textContent = `Cancel “${button.dataset.circleMeetingTitle}”? The affected members will see this update in the conversation.`;
    document.getElementById('circleCancelError').hidden = true;
    bootstrap.Modal.getOrCreateInstance(cancelModal).show();
  });
  document.getElementById('circleConfirmCancel')?.addEventListener('click', async (event) => {
    if (!cancelUrl) return;
    event.currentTarget.disabled = true;
    try {await request(cancelUrl); window.location.reload();}
    catch (error) {const node = document.getElementById('circleCancelError');node.hidden = false;node.textContent = error.message;}
    finally {event.currentTarget.disabled = false;}
  });
  refresh(true);
  // Refresh only while the conversation is on screen; never POST automatically.
  window.setInterval(() => {if (!document.hidden) refresh();}, 20000);
})();
