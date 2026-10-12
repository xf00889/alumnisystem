/* Progressive enhancements for the one-time administrator setup form. */
(function () {
    'use strict';
    function init() {
        const form = document.getElementById('superuserForm');
        if (!form) return;
        const password = document.getElementById('id_password1');
        const confirmation = document.getElementById('id_password2');
        const strengthBar = document.getElementById('passwordStrength');
        const strengthText = document.getElementById('passwordStrengthText');
        const matchText = document.getElementById('passwordMatch');
        const submit = document.getElementById('createAdminButton');
        const errors = document.getElementById('setup-form-errors');
        if (errors) errors.focus();

        document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
            button.addEventListener('click', function () {
                const input = document.getElementById(button.dataset.passwordToggle);
                if (!input) return;
                const show = input.type === 'password';
                input.type = show ? 'text' : 'password';
                button.setAttribute('aria-pressed', String(show));
                button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
                button.querySelector('i')?.classList.toggle('fa-eye-slash', show);
                button.querySelector('i')?.classList.toggle('fa-eye', !show);
            });
        });
        if (password && strengthBar && strengthText) {
            password.addEventListener('input', function () {
                const value = password.value;
                const checks = [value.length >= 8, /[a-z]/.test(value), /[A-Z]/.test(value), /\d/.test(value), /[^\w]/.test(value)];
                const passed = checks.filter(Boolean).length;
                strengthBar.style.width = value ? (passed * 20) + '%' : '0%';
                strengthBar.dataset.strength = passed < 3 ? 'weak' : passed < 5 ? 'fair' : 'strong';
                strengthText.textContent = !value ? 'Enter a strong password' : passed < 3 ? 'Weak password' : passed < 5 ? 'Getting stronger' : 'Strong password';
            });
        }
        if (password && confirmation && matchText) {
            function updateMatch() {
                matchText.textContent = !confirmation.value ? 'Passwords must match.' : password.value === confirmation.value ? 'Passwords match.' : 'Passwords do not match.';
                matchText.dataset.match = confirmation.value ? String(password.value === confirmation.value) : '';
            }
            password.addEventListener('input', updateMatch);
            confirmation.addEventListener('input', updateMatch);
        }
        if (submit) {
            form.addEventListener('submit', function () {
                // Do not prevent Django's normal validation or suppress errors.
                submit.disabled = true;
                submit.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Creating administrator…';
            });
        }
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
