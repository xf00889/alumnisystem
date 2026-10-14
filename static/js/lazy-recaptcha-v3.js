(function () {
    'use strict';

    const controller = window.NorsuLazyRecaptchaV3 || {
        apiPromise: null,
        observer: null,

        loadApi(siteKey) {
            if (!siteKey) {
                return Promise.reject(new Error('reCAPTCHA site key is missing.'));
            }
            if (window.grecaptcha && typeof window.grecaptcha.execute === 'function' &&
                typeof window.grecaptcha.ready === 'function') {
                return Promise.resolve(window.grecaptcha);
            }
            if (this.apiPromise) {
                return this.apiPromise;
            }

            this.apiPromise = new Promise((resolve, reject) => {
                const existing = document.getElementById('norsu-recaptcha-v3-api');
                const script = existing || document.createElement('script');
                let settled = false;
                const timeout = window.setTimeout(() => fail(new Error('reCAPTCHA timed out.')), 12000);
                const fail = (error) => {
                    if (settled) return;
                    settled = true;
                    window.clearTimeout(timeout);
                    this.apiPromise = null;
                    script.remove();
                    reject(error);
                };
                const ready = () => {
                    if (!window.grecaptcha || typeof window.grecaptcha.execute !== 'function' ||
                        typeof window.grecaptcha.ready !== 'function') {
                        fail(new Error('The reCAPTCHA v3 API did not initialize.'));
                        return;
                    }
                    window.grecaptcha.ready(() => {
                        if (settled) return;
                        settled = true;
                        window.clearTimeout(timeout);
                        resolve(window.grecaptcha);
                    });
                };
                script.addEventListener('load', ready, { once: true });
                script.addEventListener('error', () => fail(new Error('Unable to load reCAPTCHA.')), { once: true });
                if (!existing) {
                    script.id = 'norsu-recaptcha-v3-api';
                    script.src = `https://www.google.com/recaptcha/api.js?render=${encodeURIComponent(siteKey)}`;
                    script.async = true;
                    script.defer = true;
                    document.head.appendChild(script);
                }
            });
            return this.apiPromise;
        },

        warm(field) {
            const siteKey = field.dataset.sitekey;
            if (siteKey) {
                this.loadApi(siteKey).catch(() => {});
            }
        },

        reportError(field) {
            const form = field.form;
            let message = form.querySelector('[data-recaptcha-error]');
            if (!message) {
                message = document.createElement('div');
                message.dataset.recaptchaError = '';
                message.className = 'alert alert-danger mt-2 auth-recaptcha-message';
                message.setAttribute('role', 'alert');
                const title = document.createElement('strong');
                title.textContent = 'Security verification unavailable';
                const description = document.createElement('span');
                description.textContent = 'We could not connect to Google reCAPTCHA. Check your connection or site permissions and try again. If the problem continues, contact Alumni Affairs.';
                const retry = document.createElement('button');
                retry.type = 'button';
                retry.className = 'btn btn-outline-danger btn-sm auth-recaptcha-retry';
                retry.textContent = 'Retry verification';
                retry.addEventListener('click', () => {
                    message.remove();
                    if (typeof form.requestSubmit === 'function') {
                        form.requestSubmit();
                    } else {
                        form.querySelector('[type="submit"]').click();
                    }
                });
                message.append(title, description, retry);
                field.insertAdjacentElement('afterend', message);
            }
            form.querySelectorAll('[type="submit"]').forEach((button) => {
                button.disabled = false;
            });
            const callbackName = field.dataset.errorCallback;
            if (callbackName && typeof window[callbackName] === 'function') {
                window[callbackName]();
            }
        },

        initializeField(field) {
            if (field.dataset.recaptchaInitialized === 'true' || !field.form) {
                return;
            }

            field.dataset.recaptchaInitialized = 'true';
            const form = field.form;
            const warm = () => this.warm(field);

            form.addEventListener('focusin', warm, { once: true, passive: true });
            form.addEventListener('pointerdown', warm, { once: true, passive: true });

            if ('IntersectionObserver' in window) {
                if (!this.observer) {
                    this.observer = new IntersectionObserver((entries) => {
                        entries.forEach((entry) => {
                            if (!entry.isIntersecting) {
                                return;
                            }
                            const targetField = entry.target.querySelector('.norsu-recaptcha-v3');
                            if (targetField) {
                                this.warm(targetField);
                            }
                            this.observer.unobserve(entry.target);
                        });
                    }, { rootMargin: '300px 0px' });
                }
                this.observer.observe(form);
            }

            form.addEventListener('submit', (event) => {
                if (form.dataset.recaptchaSubmitting === 'true') {
                    return;
                }

                event.preventDefault();
                form.dataset.recaptchaSubmitting = 'true';
                const siteKey = field.dataset.sitekey;
                const action = field.dataset.recaptchaAction || 'submit';

                this.loadApi(siteKey)
                    .then((grecaptcha) => grecaptcha.execute(siteKey, { action }))
                    .then((token) => {
                        if (typeof token !== 'string' || !token.trim()) {
                            throw new Error('The reCAPTCHA API returned an empty token.');
                        }
                        field.value = token;
                        const message = form.querySelector('[data-recaptcha-error]');
                        if (message) message.remove();
                        HTMLFormElement.prototype.submit.call(form);
                    })
                    .catch(() => {
                        delete form.dataset.recaptchaSubmitting;
                        this.reportError(field);
                    });
            });
        },

        initialize() {
            document.querySelectorAll('.norsu-recaptcha-v3').forEach((field) => {
                this.initializeField(field);
            });
        }
    };

    window.NorsuLazyRecaptchaV3 = controller;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => controller.initialize(), { once: true });
    } else {
        controller.initialize();
    }
}());
