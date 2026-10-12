/* Scoped donor workflow enhancements; server enforces all financial rules. */
document.addEventListener('DOMContentLoaded', () => {
 // Payment transfers can keep this page open long enough for another login
 // to rotate CSRF cookies. Refresh the *server-issued* masked form token right
 // before submitting; do not copy or guess a raw browser cookie.
 const proofForm = document.getElementById('donation-proof-form');
 proofForm?.addEventListener('submit', async (event) => {
  if (proofForm.dataset.csrfReady === 'true') return;
  event.preventDefault();
  if (proofForm.dataset.csrfRefreshing === 'true') return;
  proofForm.dataset.csrfRefreshing = 'true';
  let notice = proofForm.querySelector('[data-csrf-error]');
  if (!notice) {
   notice = document.createElement('p');
   notice.dataset.csrfError = '';
   notice.setAttribute('role', 'alert');
   notice.className = 'dn-error';
   proofForm.prepend(notice);
  }
  notice.textContent = '';
  try {
   const response = await fetch(proofForm.dataset.csrfRefreshUrl, {
    method: 'GET', credentials: 'same-origin', cache: 'no-store',
    headers: { 'Accept': 'application/json' },
   });
   if (!response.ok) throw new Error('Security token refresh failed');
   const data = await response.json();
   const input = proofForm.querySelector('input[name="csrfmiddlewaretoken"]');
   if (!input || typeof data.csrf_token !== 'string' || data.csrf_token.length !== 64) {
    throw new Error('Security token is missing');
   }
   // This deployment uses a readable CSRF cookie; don't submit a payment
   // document if the browser is refusing the required security cookie.
   const hasCookie = document.cookie.split(';').some(part => part.trim().startsWith('csrftoken='));
   if (!hasCookie) throw new Error('Security cookie unavailable');
   input.value = data.csrf_token;
   proofForm.dataset.csrfReady = 'true';
   if (typeof proofForm.requestSubmit === 'function') {
    proofForm.requestSubmit(event.submitter || undefined);
   } else {
    HTMLFormElement.prototype.submit.call(proofForm);
   }
  } catch (_) {
   notice.textContent = 'Your security session could not be refreshed. Keep this page open, enable first-party cookies, and retry. If this is local HTTP, check your cookie security settings.';
  } finally {
   proofForm.dataset.csrfRefreshing = 'false';
   proofForm.dataset.csrfReady = 'false';
  }
 });
 document.querySelectorAll('[data-donation-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
   const value = document.getElementById(button.dataset.donationCopy)?.textContent.trim();
   if (!value) return;
   try { await navigator.clipboard.writeText(value); button.textContent = 'Copied!'; }
   catch (_) { button.textContent = 'Select number to copy'; }
  });
 });
 document.querySelectorAll('[data-donation-preset]').forEach((button) => {
  button.addEventListener('click', () => {
   const input = document.querySelector('input[name="amount"]');
   if (input) { input.value = button.dataset.donationPreset; input.dispatchEvent(new Event('input', { bubbles:true })); }
  });
 });
});
