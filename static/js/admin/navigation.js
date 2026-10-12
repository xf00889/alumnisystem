/** Administration navigation: native disclosure buttons + accessible mobile drawer. */
(function () {
    'use strict';
    function init() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar || !sidebar.classList.contains('staff-sidebar') || sidebar.dataset.initialized) return;
        sidebar.dataset.initialized = 'true';
        const launcher = document.querySelector('.staff-nav__open');
        const closeButton = sidebar.querySelector('.staff-nav__close');
        const backdrop = document.querySelector('.staff-nav__backdrop');
        const mobile = window.matchMedia('(max-width: 991.98px)');
        const sections = [...sidebar.querySelectorAll('.staff-nav__disclosure')];
        const links = [...sidebar.querySelectorAll('.staff-nav__link')];
        const storeKey = 'norsu-staff-nav-open-v1';
        let remembered = {};
        try { remembered = JSON.parse(localStorage.getItem(storeKey) || '{}') || {}; } catch (_) { remembered = {}; }

        // Use exact URLs first, then the most-specific prefix. Avoid marking both
        // Alumni Directory and Alumni Management active for the same route.
        const here = location.pathname.replace(/\/+$/, '') || '/';
        const rank = link => {
            const url = new URL(link.href, location.href);
            if (url.origin !== location.origin) return -1;
            const path = url.pathname.replace(/\/+$/, '') || '/';
            if (path === here) return 10000 + path.length;
            if (path !== '/' && here.startsWith(path + '/')) return path.length;
            return -1;
        };
        let active = null, best = -1;
        links.forEach(link => {
            const score = rank(link);
            if (score > best) { best = score; active = link; }
        });
        if (!active || best < 0) {
            const djangoActive = links.filter(link => link.classList.contains('active'));
            // Server-side active states remain a fallback for uncommon nested routes.
            active = djangoActive.sort((a,b) => b.pathname.length - a.pathname.length)[0] || null;
        }
        links.forEach(link => {
            const current = link === active;
            link.classList.toggle('active', current);
            if (current) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
        const activeSection = active && active.closest('.staff-nav__group');
        function setSection(button, expanded, save) {
            const group = document.getElementById(button.getAttribute('aria-controls'));
            if (!group) return;
            button.setAttribute('aria-expanded', String(expanded));
            group.hidden = !expanded;
            if (save) {
                remembered[group.id] = expanded;
                try { localStorage.setItem(storeKey, JSON.stringify(remembered)); } catch (_) { /* optional */ }
            }
        }
        sections.forEach(button => {
            const group = document.getElementById(button.getAttribute('aria-controls'));
            if (!group) return;
            const containsActive = activeSection === group;
            button.classList.toggle('has-active', containsActive);
            const preferred = Object.hasOwn(remembered, group.id) ? remembered[group.id] : false;
            setSection(button, containsActive || preferred, false);
            button.addEventListener('click', () => setSection(button, button.getAttribute('aria-expanded') !== 'true', true));
        });

        let opened = false;
        function show() {
            if (!mobile.matches || opened) return;
            opened = true;
            sidebar.dataset.open = 'true';
            sidebar.inert = false;
            backdrop.hidden = false;
            launcher.setAttribute('aria-expanded', 'true');
            document.body.style.overflow = 'hidden';
            closeButton.focus();
        }
        function hide(restoreFocus) {
            const wasOpen = opened;
            opened = false;
            sidebar.dataset.open = 'false';
            backdrop.hidden = true;
            launcher.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
            sidebar.inert = mobile.matches;
            if (wasOpen && restoreFocus && mobile.matches) launcher.focus();
        }
        function syncViewport() {
            if (!mobile.matches) {
                hide(false);
                sidebar.inert = false;
            } else {
                hide(false);
            }
        }
        launcher.addEventListener('click', () => opened ? hide(true) : show());
        closeButton.addEventListener('click', () => hide(true));
        backdrop.addEventListener('click', () => hide(true));
        sidebar.querySelectorAll('.staff-nav__link').forEach(link => link.addEventListener('click', () => {
            if (mobile.matches) hide(false);
        }));
        document.addEventListener('keydown', event => {
            if (!opened || !mobile.matches) return;
            if (event.key === 'Escape') { event.preventDefault(); hide(true); return; }
            if (event.key !== 'Tab') return;
            const focusables = [...sidebar.querySelectorAll('a[href], button:not([disabled])')]
                .filter(el => !el.closest('[hidden]') && el.getClientRects().length);
            if (!focusables.length) return;
            const first = focusables[0], last = focusables[focusables.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
        });
        if (mobile.addEventListener) mobile.addEventListener('change', syncViewport);
        else mobile.addListener(syncViewport);
        syncViewport();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
