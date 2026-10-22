/** AJAX registrar import with an honest indeterminate processing state. */
(function () {
    'use strict';
    const form = document.getElementById('registryImportForm');
    if (!form) return;
    const picker = document.getElementById('registryCsvFile');
    const submit = document.getElementById('registryImportSubmit');
    const cancel = document.getElementById('registryImportCancel');
    const progress = document.getElementById('registryImportProgress');
    const result = document.getElementById('registryImportResult');
    const modal = document.getElementById('registryImportModal');
    let busy = false;
    let complete = false;

    function showResult(message, type, details) {
        result.replaceChildren();
        result.className = 'alert ' + (type === 'success' ? 'alert-success' : 'alert-danger') + ' mt-3 mb-0';
        const title = document.createElement('strong');
        title.textContent = message;
        result.appendChild(title);
        if (details) {
            const text = document.createElement('p');
            text.className = 'mb-0 mt-2';
            text.textContent = details;
            result.appendChild(text);
        }
        result.hidden = false;
    }

    modal?.addEventListener('hide.bs.modal', function (event) {
        if (busy) event.preventDefault();
    });

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (busy || !form.reportValidity()) return;
        const file = picker.files && picker.files[0];
        if (!file) return;
        if (!/\.(csv|xlsx)$/i.test(file.name)) {
            showResult('Choose a .csv or .xlsx registrar file.', 'error');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            showResult('The maximum file size is 10 MB.', 'error');
            return;
        }
        const body = new FormData(form);
        body.set('import_registry_csv', '1');
        busy = true;
        complete = false;
        progress.hidden = false;
        result.hidden = true;
        submit.disabled = true;
        cancel.disabled = true;
        picker.disabled = true;
        submit.setAttribute('aria-busy', 'true');
        const originalLabel = submit.innerHTML;
        submit.textContent = 'Importing…';
        try {
            const response = await fetch(form.action, {
                method: 'POST', body,
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
            });
            let payload;
            try { payload = await response.json(); } catch (_) { payload = null; }
            if (!response.ok || !payload || !payload.ok) {
                throw new Error(payload?.message || 'Import failed. Please try again.');
            }
            complete = true;
            const detail = `${payload.created} new, ${payload.updated} updated, ${payload.skipped} skipped.`;
            const warnings = (payload.warnings || []).slice(0, 4).join(' · ');
            showResult('Registrar import complete', 'success', warnings ? detail + ' Review: ' + warnings : detail);
            submit.textContent = 'Done · Refresh list';
            submit.disabled = false;
        } catch (error) {
            showResult(error.message || 'Unable to import the file.', 'error');
        } finally {
            busy = false;
            progress.hidden = true;
            cancel.disabled = false;
            picker.disabled = false;
            submit.removeAttribute('aria-busy');
            if (!complete) {
                submit.disabled = false;
                submit.innerHTML = originalLabel;
            }
        }
    });
    submit.addEventListener('click', function (event) {
        if (complete) {
            event.preventDefault();
            event.stopImmediatePropagation();
            window.location.reload();
        }
    }, true);
})();
