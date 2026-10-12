/* Leaflet basemap switching only. Alumni clusters, pins and the viewport remain untouched. */
(() => {
    'use strict';

    const STYLE_STORAGE_KEY = 'norsu.staff.alumni-map.basemap.v1';
    const MAP_CREDIT = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>';
    const CARTO_CREDIT = MAP_CREDIT + ' &copy; <a href="https://carto.com/" target="_blank" rel="noopener noreferrer">CARTO</a>';
    const TOPO_CREDIT = MAP_CREDIT + ' | SRTM &copy; <a href="https://opentopomap.org/" target="_blank" rel="noopener noreferrer">OpenTopoMap</a> (CC-BY-SA)';
    const MAPTILER_CREDIT = '&copy; <a href="https://www.maptiler.com/copyright/" target="_blank" rel="noopener noreferrer">MapTiler</a> ' + MAP_CREDIT;
    const STYLE_LABELS = Object.freeze({ streets: 'Street map', light: 'Light map', dark: 'Dark map', satellite: 'Satellite', terrain: 'Terrain' });
    const STYLES = Object.keys(STYLE_LABELS);

    function create(map, root, byId) {
        const cartoKey = String(root.dataset.cartoKey || '').trim();
        const maptilerKey = String(root.dataset.maptilerKey || '').trim();
        const picker = byId('mapStylePicker');
        const toggle = byId('mapStyleToggle');
        const menu = byId('mapStyleMenu');
        const hint = byId('mapStyleHint');
        const current = byId('mapStyleCurrent');
        const logo = byId('mapTilerLogo');
        const feedback = byId('mapFeedback');
        const buttons = [...picker.querySelectorAll('[data-map-style]')];
        let active = null;
        let pending = null;
        let selectedStyle = null;
        let autoFallbackAttempted = false;

        function describeStyle(style) {
            const common = {
                minZoom: 2,
                maxZoom: 19,
                referrerPolicy: 'strict-origin-when-cross-origin',
                crossOrigin: true,
            };
            if (style === 'terrain') {
                return {
                    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                    options: { ...common, subdomains: 'abc', maxNativeZoom: 17, attribution: TOPO_CREDIT },
                };
            }
            if (style === 'satellite') {
                if (!maptilerKey) return null;
                return {
                    url: `https://api.maptiler.com/tiles/satellite-v4/{z}/{x}/{y}?key=${encodeURIComponent(maptilerKey)}`,
                    options: { ...common, maxNativeZoom: 18, attribution: MAPTILER_CREDIT },
                };
            }
            const cartoNames = { streets: 'voyager', light: 'light_all', dark: 'dark_all' };
            if (cartoKey) {
                return {
                    url: `https://basemaps.cartocdn.com/rastertiles/${cartoNames[style]}/{z}/{x}/{y}.png?key=${encodeURIComponent(cartoKey)}`,
                    options: { ...common, maxNativeZoom: 19, attribution: CARTO_CREDIT },
                };
            }
            // Honest, no-key visual alternatives to OSM's standard raster cartography.
            // Only the tile layer is color-adjusted. Markers, badges and popups are unaffected.
            return {
                url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                options: {
                    ...common,
                    maxNativeZoom: 19,
                    attribution: MAP_CREDIT,
                    className: style === 'light' ? 'alumni-map-baselayer--light' : style === 'dark' ? 'alumni-map-baselayer--dark' : '',
                },
            };
        }

        function status(text) { hint.textContent = text; }
        function setMenuOpen(isOpen) {
            menu.hidden = !isOpen;
            toggle.setAttribute('aria-expanded', String(isOpen));
            picker.classList.toggle('is-open', isOpen);
        }
        function updateSelection(style) {
            selectedStyle = style;
            current.textContent = STYLE_LABELS[style];
            buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mapStyle === style)));
            if (logo) logo.hidden = style !== 'satellite';
        }
        function remember(style) {
            try { window.localStorage.setItem(STYLE_STORAGE_KEY, style); } catch (_) { /* private browsing */ }
        }
        function restore() {
            try {
                const saved = window.localStorage.getItem(STYLE_STORAGE_KEY);
                if (STYLES.includes(saved) && (saved !== 'satellite' || maptilerKey)) return saved;
            } catch (_) { /* private browsing */ }
            return 'streets';
        }
        function discardPending() {
            if (!pending) return;
            clearTimeout(pending.timeout);
            map.removeLayer(pending.layer);
            pending = null;
        }
        function select(style, options = {}) {
            if (!STYLES.includes(style)) return false;
            if (style === 'satellite' && !maptilerKey) {
                status('Satellite requires a MapTiler API key. Add LOCATION_MAPTILER_BASEMAP_KEY to .env, then reload.');
                return false;
            }
            if (style === selectedStyle && !pending) return true;
            if (pending && pending.style === style) return true;
            discardPending();
            const config = describeStyle(style);
            const layer = L.tileLayer(config.url, config.options);
            const transition = { layer, style, errors: 0, timeout: null };
            pending = transition;
            status(`Loading ${STYLE_LABELS[style].toLowerCase()}…`);
            function finish() {
                if (pending !== transition) return;
                clearTimeout(transition.timeout);
                const previous = active;
                active = layer;
                pending = null;
                if (previous && previous !== layer) map.removeLayer(previous);
                updateSelection(style);
                remember(style);
                setMenuOpen(false);
                const suffix = !cartoKey && ['streets', 'light', 'dark'].includes(style)
                    ? ' (keyless OpenStreetMap styling)' : '';
                status(`${STYLE_LABELS[style]} selected${suffix}. Alumni markers remain unchanged.`);
            }
            function fail() {
                if (pending !== transition) return;
                discardPending();
                if (active) {
                    status(`${STYLE_LABELS[style]} tiles could not load. Previous map style kept. Check the provider key, allowed website origins or Network tab.`);
                    feedback.textContent = `The requested ${STYLE_LABELS[style].toLowerCase()} map is unavailable; your previous map remains active.`;
                    return;
                }
                if (style !== 'terrain' && !autoFallbackAttempted) {
                    autoFallbackAttempted = true;
                    feedback.textContent = 'Street tiles are unavailable. Trying Terrain as the alternative tile provider.';
                    select('terrain', { automaticFallback: true });
                } else {
                    status('Map imagery is unavailable. Check Network tile errors, your connection and map-provider policies.');
                    feedback.textContent = 'Map imagery could not load from either provider. Alumni location data may still be available in the list.';
                }
            }
            layer.on('tileload', finish);
            layer.on('tileerror', () => {
                transition.errors += 1;
                if (pending === transition && transition.errors >= 3) {
                    fail();
                } else if (active === layer && transition.errors >= 3 && !transition.warned) {
                    transition.warned = true;
                    if (style !== 'terrain' && !autoFallbackAttempted) {
                        autoFallbackAttempted = true;
                        feedback.textContent = 'The current tile provider is failing. Trying Terrain as an alternative.';
                        select('terrain', { automaticFallback: true });
                    } else {
                        feedback.textContent = 'Some map tiles are blocked. Check the provider policy, website restrictions and browser Network tab.';
                    }
                }
            });
            transition.timeout = setTimeout(fail, 14000);
            map.addLayer(layer);
            return true;
        }

        const satelliteButton = buttons.find(button => button.dataset.mapStyle === 'satellite');
        if (!maptilerKey && satelliteButton) {
            satelliteButton.disabled = true;
            satelliteButton.title = 'Configure LOCATION_MAPTILER_BASEMAP_KEY to enable satellite imagery';
            satelliteButton.setAttribute('aria-disabled', 'true');
        } else if (byId('satelliteAvailability')) {
            byId('satelliteAvailability').textContent = 'Aerial and satellite imagery';
        }
        toggle.addEventListener('click', () => setMenuOpen(menu.hidden));
        buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.mapStyle)));
        document.addEventListener('click', event => {
            if (!menu.hidden && !picker.contains(event.target)) setMenuOpen(false);
        });
        document.addEventListener('keydown', event => {
            if (event.key === 'Escape' && !menu.hidden) {
                setMenuOpen(false);
                toggle.focus();
            }
        });
        select(restore());
        return { select, getSelectedStyle: () => selectedStyle };
    }

    window.NorsuMapBasemaps = Object.freeze({ create });
})();
