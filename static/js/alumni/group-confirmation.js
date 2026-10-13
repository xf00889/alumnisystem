/* Shared group action confirmation: same-page Bootstrap modal, no browser-native confirm(). */
(function () {
    'use strict';
    window.NORSUGroupConfirm = function (description, destructive) {
        return new Promise((resolve) => {
            const modalElement = document.getElementById('groupDecisionModal');
            if (!modalElement || !window.bootstrap?.Modal) {
                // Fail closed if the styled confirmation UI is unavailable.
                resolve(false);
                return;
            }
            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
            const confirmButton = document.getElementById('groupDecisionConfirm');
            const title = document.getElementById('groupDecisionTitle');
            const detail = document.getElementById('groupDecisionDescription');
            title.textContent = destructive ? 'Confirm removal or rejection' : 'Confirm group action';
            detail.textContent = description;
            confirmButton.className = 'btn ' + (destructive ? 'btn-danger' : 'btn-primary');
            confirmButton.textContent = destructive ? 'Confirm action' : 'Continue';
            let settled = false;
            const finish = (result) => {
                if (settled) return;
                settled = true;
                confirmButton.removeEventListener('click', onConfirm);
                modalElement.removeEventListener('hidden.bs.modal', onHide);
                resolve(result);
            };
            const onConfirm = () => { finish(true); modal.hide(); };
            const onHide = () => finish(false);
            confirmButton.addEventListener('click', onConfirm);
            modalElement.addEventListener('hidden.bs.modal', onHide, { once: true });
            modal.show();
        });
    };
})();
