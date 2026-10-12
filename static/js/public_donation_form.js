/* Public donation form enhancement. Backend remains the source of truth. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('donation-form');
    if (!form) return;
    const amount = form.querySelector('[name="amount"]');
    const nameField = form.querySelector('[name="donor_name"]');
    const email = form.querySelector('[name="donor_email"]');
    const anonymous = form.querySelector('[name="is_anonymous"]');
    const nameWrapper = document.getElementById('donor-name-field');
    const preview = document.querySelector('[data-donation-preview]');
    const presets = Array.from(form.querySelectorAll('[data-donation-amount]'));
    const amountError = document.getElementById('amount-client-error');
    const submit = document.getElementById('donate-btn');

    function donationValue() {
      const value = amount ? Number(amount.value) : NaN;
      return Number.isFinite(value) ? value : 0;
    }
    function updateAmount() {
      const value = donationValue();
      if (preview) preview.textContent = value > 0 ? '₱' + value.toLocaleString('en-PH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'Select an amount';
      presets.forEach(function (button) {
        button.setAttribute('aria-pressed', String(Number(button.dataset.donationAmount) === value && value > 0));
      });
      if (amountError) amountError.hidden = true;
      if (amount) amount.removeAttribute('aria-invalid');
    }
    presets.forEach(function (button) {
      button.addEventListener('click', function () {
        if (!amount) return;
        amount.value = button.dataset.donationAmount;
        amount.dispatchEvent(new Event('input', {bubbles: true}));
      });
    });
    if (amount) {
      amount.setAttribute('inputmode', 'decimal');
      amount.setAttribute('min', '1');
      amount.setAttribute('max', '99999999.99');
      amount.setAttribute('step', '0.01');
      amount.setAttribute('required', 'required');
      amount.addEventListener('input', updateAmount);
    }
    if (email) email.required = true;
    function syncAnonymous() {
      const isAnonymous = Boolean(anonymous && anonymous.checked);
      if (nameWrapper) nameWrapper.hidden = isAnonymous;
      if (nameField) nameField.required = !isAnonymous;
    }
    if (anonymous) anonymous.addEventListener('change', syncAnonymous);
    syncAnonymous();
    updateAmount();

    form.addEventListener('submit', function (event) {
      if (submit && submit.dataset.submitting === 'true') {
        event.preventDefault();
        event.stopImmediatePropagation();
        return;
      }
      const value = donationValue();
      if (!value || value < 1 || value > 99999999.99 || Math.round(value * 100) / 100 !== value) {
        event.preventDefault();
        event.stopImmediatePropagation();
        if (amountError) {
          amountError.textContent = 'Enter an amount between ₱1.00 and ₱99,999,999.99 with no more than two decimal places.';
          amountError.hidden = false;
        }
        if (amount) {
          amount.setAttribute('aria-invalid', 'true');
          }
        return;
      }
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopImmediatePropagation();
        form.reportValidity();
        return;
      }
      // The project-wide lazy reCAPTCHA controller owns asynchronous submission.
      if (form.querySelector('.norsu-recaptcha-v3')) return;
      if (submit) {
        submit.dataset.submitting = 'true';
        submit.disabled = true;
        // A full navigation is expected. Restore the button if the user returns via browser history.
        window.addEventListener('pageshow', function () {
          submit.disabled = false;
          delete submit.dataset.submitting;
        }, {once: true});
      }
    }, {capture: true});
  });
}());
