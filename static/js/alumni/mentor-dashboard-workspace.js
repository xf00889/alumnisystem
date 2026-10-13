(() => {
  'use strict';
  const csrf = document.querySelector('#mentorship-csrf-token input[name="csrfmiddlewaretoken"]')?.value || document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
  const request = async (url, data) => {
    const response = await fetch(url, {method: 'POST', body: data, credentials: 'same-origin', headers: {'X-CSRFToken': csrf, Accept: 'application/json'}});
    const type = response.headers.get('content-type') || '';
    const result = type.includes('json') ? await response.json() : {};
    if (!response.ok || !result.success) throw new Error(result.error || `Unable to save (${response.status}). Please sign in again if your session expired.`);
    return result;
  };
  function manageForm(formId, errorId) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const button = form.querySelector('button[type=submit]');
      const error = document.getElementById(errorId);
      error.hidden = true;
      button.disabled = true;
      try { await request(form.dataset.submitUrl, new FormData(form)); window.location.reload(); }
      catch (exception) { error.textContent = exception.message; error.hidden = false; }
      finally { button.disabled = false; }
    });
  }
  const progressModal = document.getElementById('progressUpdateModal');
  progressModal?.addEventListener('show.bs.modal', event => {
    const trigger = event.relatedTarget;
    const form = document.getElementById('progressUpdateForm');
    form.dataset.submitUrl = trigger.dataset.progressUrl;
    document.getElementById('mentorProgressRecipient').textContent = trigger.dataset.menteeName;
    const percent = document.getElementById('mentorProgressPercentage');
    percent.value = trigger.dataset.progressPercent || '0';
    document.getElementById('mentorProgressOutput').textContent = `${percent.value}%`;
    document.getElementById('mentorProgressNote').value = '';
    document.getElementById('mentorProgressError').hidden = true;
  });
  document.getElementById('mentorProgressPercentage')?.addEventListener('input', event => {
    document.getElementById('mentorProgressOutput').textContent = `${event.target.value}%`;
  });
  manageForm('progressUpdateForm', 'mentorProgressError');

  const rows = document.getElementById('mentorMilestoneRows');
  const rowTemplate = document.getElementById('mentorMilestoneRowTemplate');
  function appendMilestone(period = '', description = '', status = 'NOT_STARTED') {
    if (!rows || !rowTemplate || rows.children.length >= 25) return;
    const row = rowTemplate.content.firstElementChild.cloneNode(true);
    row.querySelector('[name="period[]"]').value = period;
    row.querySelector('[name="description[]"]').value = description;
    row.querySelector('[name="status[]"]').value = status;
    row.querySelector('.mentor-remove-milestone').addEventListener('click', () => {
      if (rows.children.length > 1) row.remove();
    });
    rows.appendChild(row);
  }
  const timelineModal = document.getElementById('timelineModal');
  timelineModal?.addEventListener('show.bs.modal', event => {
    const trigger = event.relatedTarget;
    const form = document.getElementById('timelineForm');
    form.dataset.submitUrl = trigger.dataset.timelineUrl;
    document.getElementById('mentorTimelineRecipient').textContent = trigger.dataset.menteeName;
    document.getElementById('mentorExpectedEndDate').value = trigger.dataset.endDate || '';
    document.getElementById('mentorTimelineError').hidden = true;
    rows.replaceChildren();
    const rawTimeline = trigger.dataset.timeline || '';
    const notes = rawTimeline.match(/(?:^|\n)Notes:\s*\n([\s\S]*)$/);
    document.getElementById('mentorTimelineNotes').value = notes ? notes[1].trim() : '';
    rawTimeline.split(/\r?\n/).forEach(line => {
      const match = line.match(/^Week\/Day\s+(.+?):\s+(.+?)(?:\s+\[(NOT_STARTED|IN_PROGRESS|COMPLETED)\])?$/);
      if (match) appendMilestone(match[1], match[2], match[3] || 'NOT_STARTED');
    });
    if (!rows.children.length) appendMilestone();
  });
  document.getElementById('mentorAddMilestone')?.addEventListener('click', () => appendMilestone());
  manageForm('timelineForm', 'mentorTimelineError');

  const cancelModal = document.getElementById('personalMeetingCancelModal');
  let cancelUrl = '';
  cancelModal?.addEventListener('show.bs.modal', event => {
    const trigger = event.relatedTarget;
    cancelUrl = trigger?.dataset.cancelUrl || '';
    document.getElementById('personalMeetingCancelDescription').textContent =
      `Cancel “${trigger?.dataset.meetingName || 'this meeting'}”? The change will appear in the mentee's private activity.`;
    document.getElementById('personalMeetingCancelError').hidden = true;
  });
  document.getElementById('personalMeetingCancelConfirm')?.addEventListener('click', async event => {
    if (!cancelUrl) return;
    event.currentTarget.disabled = true;
    try { await request(cancelUrl, new FormData()); window.location.reload(); }
    catch (error) {
      const node = document.getElementById('personalMeetingCancelError');
      node.textContent = error.message; node.hidden = false;
    } finally { event.currentTarget.disabled = false; }
  });

  const toggle = document.getElementById('availabilityToggle');
  if (toggle) {
    toggle.removeAttribute('onchange');
    toggle.addEventListener('change', async () => {
      const checked = toggle.checked;
      toggle.disabled = true;
      const url = toggle.dataset.url;
      try {
        const response = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf,'Accept':'application/json'},body:JSON.stringify({is_available:checked}),credentials:'same-origin'});
        if (!response.ok) throw new Error('Unable to update availability.');
      } catch (error) {
        toggle.checked = !checked;
        const notice = document.createElement('div');
        notice.className = 'alert alert-danger mt-2'; notice.role='alert';
        notice.textContent = error.message;
        toggle.closest('.form-check').after(notice);
      } finally { toggle.disabled = false; }
    });
  }
})();
