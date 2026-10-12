/* Mentor application review: delegated submit handles AJAX-inserted modal content. */
(() => {
  'use strict';
  const getModal = () => document.getElementById('mentorApplicationDetailModal');
  const getPopup = () => window.Swal;
  let submitting = false;

  document.addEventListener('submit', async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.id !== 'reviewApplicationForm') return;
    event.preventDefault();
    if (submitting) return;

    const action = event.submitter && event.submitter.name === 'action'
      ? event.submitter.value : '';
    if (!['approve', 'reject'].includes(action)) {
      const notice = form.querySelector('[data-mentor-review-error]');
      if (notice) { notice.textContent = 'Choose Approve or Reject.'; notice.hidden = false; }
      return;
    }

    const request = new FormData(form);
    // FormData(form) does not include the submitter: without this the backend
    // receives action=None and cannot know which decision the reviewer made.
    request.set('action', action);
    const name = action === 'approve' ? 'Approve' : 'Reject';
    const message = action === 'approve'
      ? 'Approve this application and create its verified mentor profile?'
      : 'Reject this application? Any review notes will be visible to the applicant.';
    const popup = getPopup();
    if (!popup) {
      const notice = form.querySelector('[data-mentor-review-error]');
      if (notice) { notice.textContent = 'Confirmation dialog is unavailable. Refresh the page and try again.'; notice.hidden = false; }
      return;
    }
    const decision = await popup.fire({
      title: `${name} application?`, text: message,
      icon: action === 'approve' ? 'question' : 'warning',
      showCancelButton: true, confirmButtonText: `${name} application`,
      cancelButtonText: 'Go back', reverseButtons: true, focusCancel: true,
      confirmButtonColor: action === 'approve' ? '#246f57' : '#aa3038',
    });
    if (!decision.isConfirmed) return;

    submitting = true;
    const submitButtons = [...form.querySelectorAll('button[type="submit"]')];
    const notice = form.querySelector('[data-mentor-review-error]');
    if (notice) notice.hidden = true;
    submitButtons.forEach((button) => { button.disabled = true; });
    popup.fire({ title: 'Saving decision…', text: 'Please wait.',
      allowOutsideClick: false, allowEscapeKey: false, showConfirmButton: false,
      didOpen: () => popup.showLoading(),
    });
    try {
      const response = await fetch(form.action, {
        method: 'POST', body: request, credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
      });
      if (response.redirected || (response.headers.get('content-type') || '').indexOf('application/json') === -1) {
        throw new Error('Your session may have expired. Refresh the page and sign in again.');
      }
      const result = await response.json();
      if (!response.ok || result.status !== 'success') {
        throw new Error(result.message || 'The decision could not be saved.');
      }
      await popup.fire({ icon: 'success', title: 'Decision saved',
        text: result.message || 'The mentor application was reviewed.',
        confirmButtonColor: '#2b3c6b', timer: 2200, timerProgressBar: true,
      });
      const modal = getModal();
      if (modal && window.bootstrap && window.bootstrap.Modal) {
        window.bootstrap.Modal.getInstance(modal)?.hide();
      }
      window.location.reload();
    } catch (error) {
      if (notice) { notice.textContent = error.message; notice.hidden = false; }
      await popup.fire({ icon: 'error', title: 'Could not save decision', text: error.message,
        confirmButtonColor: '#2b3c6b',
      });
    } finally {
      submitting = false;
      submitButtons.forEach((button) => { button.disabled = false; });
    }
  });
})();
