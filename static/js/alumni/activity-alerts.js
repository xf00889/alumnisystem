/* Poll new recipient-scoped activity without duplicating Django flash toasts. */
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        // Notification deep links for group chats open their row in the existing inbox.
        // The group detail endpoint itself renders an HTMX partial, not a stand-alone page.
        const groupToOpen = new URLSearchParams(window.location.search).get('open_group');
        if (groupToOpen && /^\d+$/.test(groupToOpen)) {
            window.setTimeout(function () {
                const row = Array.from(document.querySelectorAll('.conversation-item[data-mobile-url]'))
                    .find(function (item) { return item.getAttribute('data-mobile-url') === '/connections/group/' + groupToOpen + '/'; });
                if (row) row.click();
            }, 0);
        }
        const utilities = document.querySelector('.alumni-nav-utilities[data-activity-url]');
        if (!utilities) return;
        const stack = document.getElementById('alumniActivityAlerts');
        if (!stack) return;
        const userId = document.querySelector('meta[name="user-id"]')?.content || '';
        const storageKey = 'norsu-activity-seen-' + userId;
        let lastSeen = 0;
        let initialized = false;
        let running = false;
        try {
            const saved = Number(sessionStorage.getItem(storageKey));
            if (Number.isSafeInteger(saved) && saved > 0) lastSeen = saved;
        } catch (error) { /* Private browsing may block storage. */ }

        function badge(selector, count) {
            document.querySelectorAll(selector).forEach(function (element) {
                element.hidden = count <= 0;
                element.textContent = count > 99 ? '99+' : String(count);
                element.setAttribute('aria-label', count + ' unread');
            });
        }
        function showAlert(notification) {
            if (stack.children.length >= 3) stack.firstElementChild.remove();
            const alert = document.createElement('article');
            alert.className = 'alumni-activity-alert';
            const icon = document.createElement('span');
            icon.className = 'alumni-activity-alert__icon';
            icon.setAttribute('aria-hidden', 'true');
            icon.textContent = '●';
            const content = document.createElement('div');
            const heading = document.createElement('div');
            heading.className = 'alumni-activity-alert__title';
            heading.textContent = notification.title;
            const body = document.createElement('p');
            body.className = 'alumni-activity-alert__text';
            body.textContent = notification.message;
            const link = document.createElement('a');
            link.className = 'alumni-activity-alert__link';
            // Action URLs are supplied by our server, and must remain same-origin.
            let target = '/notifications/';
            try {
                const url = new URL(notification.action_url || target, window.location.origin);
                if (url.origin === window.location.origin && url.protocol === window.location.protocol) {
                    target = url.pathname + url.search;
                }
            } catch (error) { /* use local fallback */ }
            link.href = target;
            link.textContent = notification.notification_type === 'connection_request' ? 'Review request' : 'View notification';
            content.append(heading, body, link);
            const close = document.createElement('button');
            close.type = 'button'; close.className = 'alumni-activity-alert__close';
            close.textContent = '×'; close.setAttribute('aria-label', 'Dismiss banner');
            close.addEventListener('click', function () { alert.remove(); });
            alert.append(icon, content, close);
            stack.append(alert);
            window.setTimeout(function () { alert.remove(); }, 10000);
        }
        async function poll() {
            if (running || document.visibilityState === 'hidden') return;
            running = true;
            try {
                const response = await fetch(utilities.dataset.activityUrl, {
                    credentials: 'same-origin', headers: { Accept: 'application/json' }, cache: 'no-store'
                });
                if (!response.ok || !(response.headers.get('content-type') || '').includes('application/json')) return;
                const data = await response.json();
                if (!data.success) return;
                badge('[data-connection-request-count]', Number(data.pending_requests) || 0);
                badge('[data-message-unread-count]', Number(data.unread_messages) || 0);
                const items = Array.isArray(data.notifications) ? data.notifications : [];
                const newest = items.reduce(function (max, item) { return Math.max(max, Number(item.id) || 0); }, lastSeen);
                if (initialized || lastSeen) {
                    items.filter(function (item) { return Number(item.id) > lastSeen; })
                        .sort(function (a, b) { return Number(a.id) - Number(b.id); })
                        .filter(function (item) { return item.notification_type !== 'new_message'; })
                        .slice(-3).forEach(showAlert);
                }
                if (newest > lastSeen) {
                    lastSeen = newest;
                    try { sessionStorage.setItem(storageKey, String(lastSeen)); } catch (error) { /* optional */ }
                }
                initialized = true;
            } catch (error) { /* Polling must never break page navigation. */ }
            finally { running = false; }
        }
        poll();
        // Refresh immediately when a server-rendered conversation was opened.
        // Normal polling remains the fallback across tabs and other pages.
        window.addEventListener('norsu:conversation-opened', poll);
        const interval = window.setInterval(poll, 20000);
        document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') poll(); });
        window.addEventListener('pagehide', function () { window.clearInterval(interval); }, { once: true });
    });
}());
