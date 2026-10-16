/* Staff-only Manage Jobs delete confirmation; preserves the existing POST endpoint. */
(function () {
    'use strict';

    function csrfToken() {
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    document.addEventListener('click', async function (event) {
        const button = event.target.closest('[data-delete-job-url]');
        if (!button || button.disabled) return;

        const title = button.dataset.jobTitle || 'this posting';
        if (typeof window.Swal === 'undefined') {
            // Do not silently submit destructive requests without the agreed confirmation UI.
            window.alert('The confirmation dialog is unavailable. Reload this page and try again.');
            return;
        }
        const answer = await window.Swal.fire({
            title: 'Delete job posting?',
            text: 'Delete “' + title + '”? This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Delete job',
            cancelButtonText: 'Keep job',
            confirmButtonColor: '#b42336',
            cancelButtonColor: '#2b3e70',
            focusCancel: true
        });
        if (!answer.isConfirmed) return;

        button.disabled = true;
        try {
            const response = await fetch(button.dataset.deleteJobUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': csrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });
            const data = await response.json();
            if (!response.ok || data.status !== 'success') {
                throw new Error(data.message || 'Unable to delete this posting.');
            }
            await window.Swal.fire({title: 'Job deleted', text: data.message, icon: 'success', confirmButtonColor: '#2b3e70'});
            window.location.reload();
        } catch (error) {
            button.disabled = false;
            await window.Swal.fire({title: 'Unable to delete', text: error.message, icon: 'error', confirmButtonColor: '#2b3e70'});
        }
    });
})();
