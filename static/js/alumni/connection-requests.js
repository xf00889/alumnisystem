/* Single delegated handler for connection requests. Uses shared HTML dialog modals. */
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        const container = document.getElementById('requestTabsContent');
        const feedback = document.getElementById('connectionRequestFeedback');
        const token = document.querySelector('#connectionRequestCsrf [name=csrfmiddlewaretoken]')?.value;
        if (!container) return;
        let working = false;
        function announce(text, error) {
            if (!feedback) return;
            feedback.hidden = false;
            feedback.textContent = text;
            feedback.classList.toggle('is-error', Boolean(error));
        }
        function updateCounts() {
            for (const type of ['incoming', 'outgoing']) {
                const count = container.querySelectorAll('#' + (type === 'incoming' ? 'incoming' : 'outgoing') + ' [data-request-card]').length;
                const countLabel = document.querySelector('[data-request-count="' + type + '"]');
                if (countLabel) countLabel.textContent = String(count);
                const empty = container.querySelector('[data-request-empty="' + type + '"]');
                if (empty) empty.hidden = count > 0;
                const list = container.querySelector('[data-request-grid="' + type + '"]');
                if (list) list.hidden = count === 0;
            }
            document.querySelectorAll('[data-connection-request-count]').forEach(function (badge) {
                const count = container.querySelectorAll('#incoming [data-request-card]').length;
                badge.hidden = count === 0;
                badge.textContent = String(count);
                badge.setAttribute('aria-label', count + ' pending connection requests');
            });
            document.dispatchEvent(new Event('norsu:connection-requests-updated'));
        }
        container.addEventListener('click', async function (event) {
            const button = event.target.closest('[data-request-action]');
            if (!button || working) return;
            event.preventDefault();
            const action = button.dataset.requestAction;
            const person = button.dataset.person || 'this alumnus';
            const choices = {
                accept: {title:'Accept connection request?', description:'Connect with ' + person + '? You will be able to message one another.', confirmText:'Accept request'},
                reject: {title:'Reject connection request?', description:'Reject the invitation from ' + person + '? It will be removed from your incoming requests.', confirmText:'Reject request', cancelText:'Keep request', danger:true},
                cancel: {title:'Cancel sent request?', description:'Withdraw the invitation you sent to ' + person + '? They will no longer have a pending request.', confirmText:'Withdraw request', cancelText:'Keep request', danger:true}
            };
            if (!choices[action]) return;
            if (typeof window.confirmConnectionAction !== 'function') { announce('Confirmation dialog unavailable. Reload and try again.', true); return; }
            if (!await window.confirmConnectionAction(choices[action])) return;
            working = true;
            const card = button.closest('[data-request-card]');
            const actionButtons = card ? [...card.querySelectorAll('[data-request-action]')] : [button];
            actionButtons.forEach(item => { item.disabled = true; });
            try {
                const response = await fetch(button.dataset.url, {
                    method: 'POST', credentials: 'same-origin',
                    headers: {'X-CSRFToken': token || '', 'X-Requested-With': 'XMLHttpRequest', 'Accept':'application/json'}
                });
                const payload = await response.json();
                if (!response.ok || !payload.success) throw new Error(payload.message || 'Unable to update request.');
                if (card) card.remove();
                updateCounts();
                announce(action === 'accept' ? 'You are now connected with ' + person + '.' : action === 'reject' ? 'Request from ' + person + ' rejected.' : 'Request to ' + person + ' withdrawn.', false);
            } catch (error) {
                actionButtons.forEach(item => { item.disabled = false; });
                announce(error.message || 'Network error. Try again.', true);
            } finally {working = false;}
        });
        updateCounts();
    });
}());
