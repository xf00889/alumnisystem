/* Staff Leaflet explorer — location updates do not rebuild the map viewport. */
(() => {
    'use strict';
    const root = document.getElementById('alumniLocationPage');
    if (!root) return;
    const byId = id => document.getElementById(id);
    if (!window.L || typeof L.markerClusterGroup !== 'function') {
        byId('mapLoading').textContent = 'The map library could not load. Check your network connection and reload.';
        return;
    }

    const map = L.map('map', { preferCanvas: true, zoomControl: false }).setView([9.3, 123.3], 7);
    L.control.zoom({ position: 'topright' }).addTo(map);
    L.control.scale({ imperial: false, position: 'bottomright' }).addTo(map);
    // Basemap layers are independent of the alumni marker cluster overlay.
    if (!window.NorsuMapBasemaps) {
        byId('mapLoading').textContent = 'Map appearance controls could not load. Reload the page.';
        return;
    }
    window.NorsuMapBasemaps.create(map, root, byId);

    const clusters = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: zoom => zoom < 10 ? 72 : zoom < 14 ? 55 : 38,
        zoomToBoundsOnClick: true,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        spiderfyDistanceMultiplier: 1.35,
        iconCreateFunction(cluster) {
            const count = cluster.getChildCount();
            const size = count < 10 ? 39 : count < 50 ? 47 : 56;
            return L.divIcon({
                html: `<span>${count}</span>`,
                className: `alumni-map-cluster ${count < 10 ? '' : count < 50 ? 'alumni-map-cluster--medium' : 'alumni-map-cluster--large'}`,
                iconSize: [size, size], iconAnchor: [size / 2, size / 2]
            });
        }
    }).addTo(map);

    let alumni = [];
    let visible = [];
    let selectedId = null;
    let didFit = false;
    let isLoading = false;
    let markers = new Map();
    const placeholderAvatar = root.dataset.avatarUrl;
    const filters = ['alumniSearch', 'batchFilter', 'courseFilter', 'locationFilter', 'groupBy'];

    // Never turn user-entered names or URLs into raw HTML.
    function escapeHTML(value) {
        return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }
    function avatarFor(value) {
        if (!value) return placeholderAvatar;
        try {
            const url = new URL(value, window.location.origin);
            return url.origin === window.location.origin && ['http:', 'https:'].includes(url.protocol) ? url.href : placeholderAvatar;
        } catch (_) { return placeholderAvatar; }
    }
    function timestamp(alumnus) {
        const date = new Date(alumnus.timestamp);
        return Number.isNaN(date.getTime()) ? 'Unknown time' : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
    }
    function isRecent(a) {
        const elapsed = Date.now() - new Date(a.timestamp).getTime();
        return Number.isFinite(elapsed) && elapsed >= 0 && elapsed < 86400000;
    }
    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text != null) node.textContent = String(text);
        return node;
    }
    function popupRow(label, text) {
        const row = element('div', 'alumni-map-popup__line');
        row.append(element('b', '', label), element('span', '', text));
        return row;
    }
    function createPopup(a) {
        const panel = element('div', 'alumni-map-popup');
        const head = element('div', 'alumni-map-popup__intro');
        const avatar = element('img', 'alumni-map-popup__avatar');
        avatar.src = avatarFor(a.avatar);
        avatar.alt = '';
        avatar.onerror = () => { avatar.onerror = null; avatar.src = placeholderAvatar; };
        const identification = element('div');
        identification.append(element('h3', 'alumni-map-popup__name', a.user), element('span', 'alumni-map-popup__badge', 'Verified alumnus · last-shared position'));
        head.append(avatar, identification);
        panel.append(head,
            popupRow('Program', a.course),
            popupRow('Batch', a.batch),
            popupRow('Profile city', a.location),
            popupRow('Updated', timestamp(a)));

        const lookup = element('button', 'alumni-map-popup__action', 'Look up nearby street address');
        lookup.type = 'button';
        const addressBox = element('div', 'alumni-map-popup__address', 'Coordinates are shared privately with OpenStreetMap Nominatim only when you request an address.');
        lookup.addEventListener('click', async () => {
            lookup.disabled = true;
            lookup.textContent = 'Finding mapped address…';
            addressBox.textContent = 'Searching nearby mapped streets…';
            const csrf = root.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
            const url = root.dataset.addressUrlTemplate.replace('99999999', encodeURIComponent(a.position_id));
            try {
                const response = await fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': csrf || '', 'Accept': 'application/json' } });
                const data = await response.json();
                if (!response.ok) throw new Error(data.message || 'Lookup unavailable.');
                addressBox.replaceChildren();
                addressBox.append(element('strong', '', data.address));
                addressBox.append(element('span', 'alumni-map-popup__note', data.note));
                addressBox.append(element('span', 'alumni-map-popup__note', data.attribution));
                lookup.textContent = 'Refresh mapped address';
            } catch (err) {
                addressBox.textContent = err.message || 'Address lookup failed.';
                lookup.textContent = 'Try address lookup again';
            } finally { lookup.disabled = false; }
        });
        panel.append(lookup, addressBox);
        return panel;
    }
    function markerFor(a) {
        const icon = L.divIcon({
            className: 'alumni-map-pin',
            html: `<span class="alumni-map-pin__inner"><img src="${escapeHTML(avatarFor(a.avatar))}" alt=""></span>`,
            iconSize: [38, 42], iconAnchor: [19, 39], popupAnchor: [0, -35]
        });
        const marker = L.marker([a.latitude, a.longitude], { icon, title: a.user, alt: `Location of ${a.user}` });
        marker.bindPopup(() => createPopup(a), { maxWidth: 310, closeButton: true, autoClose: true });
        marker.on('click', () => { selectedId = String(a.id); highlightSelected(); });
        return marker;
    }
    function highlightSelected() {
        root.querySelectorAll('.alumni-map-person').forEach(node => {
            const selected = node.dataset.userId === selectedId;
            node.classList.toggle('is-selected', selected);
            node.setAttribute('aria-pressed', String(selected));
        });
    }
    function focusAlumnus(id) {
        const marker = markers.get(String(id));
        if (!marker) return;
        selectedId = String(id);
        highlightSelected();
        clusters.zoomToShowLayer(marker, () => {
            map.panTo(marker.getLatLng(), { animate: false });
            marker.openPopup();
        });
    }
    function replaceOptions(selectId, values, label) {
        const select = byId(selectId);
        const existing = select.value;
        select.replaceChildren(new Option(label, ''));
        values.sort((a,b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }))
            .forEach(value => select.append(new Option(value, value)));
        select.value = values.includes(existing) ? existing : '';
    }
    function updateFilterOptions() {
        replaceOptions('batchFilter', [...new Set(alumni.map(a => a.batch))], 'All batches');
        replaceOptions('courseFilter', [...new Set(alumni.map(a => a.course))], 'All programs');
        replaceOptions('locationFilter', [...new Set(alumni.map(a => a.location))], 'All cities');
    }
    function fitAll() {
        if (clusters.getLayers().length) map.fitBounds(clusters.getBounds().pad(0.13), { maxZoom: 15, animate: false });
        else map.setView([9.3, 123.3], 7);
    }
    function renderList() {
        const holder = byId('locationResults');
        const key = byId('groupBy').value === 'batch' ? 'batch' : 'location';
        holder.replaceChildren();
        if (!visible.length) {
            holder.append(element('div', 'alumni-map-empty', alumni.length ? 'No matches. Try clearing one or more filters.' : 'No verified alumni have a recently shared location.'));
            return;
        }
        const groups = new Map();
        for (const person of visible) {
            const group = person[key] || 'Unknown';
            if (!groups.has(group)) groups.set(group, []);
            groups.get(group).push(person);
        }
        for (const [groupName, people] of [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true }))) {
            const heading = element('div', 'alumni-map-group__heading');
            heading.append(element('span', '', key === 'batch' ? `Batch ${groupName}` : groupName), element('b', '', people.length));
            holder.append(heading);
            for (const person of people.sort((a,b) => a.user.localeCompare(b.user))) {
                const row = element('button', 'alumni-map-person');
                row.type = 'button';
                row.dataset.userId = person.id;
                row.setAttribute('aria-label', `View ${person.user} on map`);
                const photo = element('img', 'alumni-map-person__avatar');
                photo.src = avatarFor(person.avatar); photo.alt = '';
                photo.onerror = () => { photo.onerror = null; photo.src = placeholderAvatar; };
                const details = element('span', 'alumni-map-person__info');
                details.append(element('span', 'alumni-map-person__name', person.user), element('span', 'alumni-map-person__sub', `${person.course} · ${key === 'batch' ? person.location : `Batch ${person.batch}`}`));
                row.append(photo, details, element('i', 'fas fa-chevron-right alumni-map-person__arrow'));
                row.addEventListener('click', () => focusAlumnus(person.id));
                holder.append(row);
            }
        }
        highlightSelected();
    }
    function applyFilters({ preserveView = true } = {}) {
        const search = byId('alumniSearch').value.trim().toLocaleLowerCase();
        const batch = byId('batchFilter').value;
        const course = byId('courseFilter').value;
        const city = byId('locationFilter').value;
        visible = alumni.filter(a =>
            (!search || [a.user, a.batch, a.course, a.location].some(s => String(s).toLocaleLowerCase().includes(search))) &&
            (!batch || a.batch === batch) && (!course || a.course === course) && (!city || a.location === city)
        );
        markers.clear();
        clusters.clearLayers();
        const freshMarkers = visible.map(a => {
            const marker = markerFor(a);
            markers.set(String(a.id), marker);
            return marker;
        });
        clusters.addLayers(freshMarkers);
        if (!visible.some(a => String(a.id) === selectedId)) selectedId = null;
        byId('totalAlumni').textContent = visible.length;
        byId('totalBatches').textContent = new Set(visible.map(a => a.batch)).size;
        byId('totalCourses').textContent = new Set(visible.map(a => a.course)).size;
        byId('recentAlumni').textContent = visible.filter(isRecent).length;
        byId('resultsCount').textContent = visible.length;
        renderList();
        if (!preserveView) fitAll();
        byId('mapFeedback').textContent = visible.length ? `${visible.length} alumni shown · click a cluster to expand.` : 'No pins match the current filters.';
    }
    async function loadLocations({ initial = false } = {}) {
        if (isLoading) return;
        isLoading = true;
        byId('refreshMap').disabled = true;
        if (initial) byId('mapLoading').hidden = false;
        try {
            const response = await fetch(root.dataset.locationsUrl, { credentials: 'same-origin', headers: { 'Accept': 'application/json' }, cache: 'no-store' });
            if (!response.ok) throw new Error(response.status === 403 ? 'You do not have permission to view these records.' : 'Could not load location data.');
            const data = await response.json();
            if (!Array.isArray(data.locations)) throw new Error('The server returned unexpected data.');
            alumni = data.locations.filter(a => Number.isFinite(Number(a.latitude)) && Number.isFinite(Number(a.longitude)))
                .map(a => ({ ...a, latitude: Number(a.latitude), longitude: Number(a.longitude),
                    batch: a.batch || 'Unknown', course: a.course || 'Unknown program', location: a.location || 'Unknown city' }));
            updateFilterOptions();
            applyFilters({ preserveView: didFit });
            didFit = true;
            byId('lastRefresh').textContent = `Updated ${new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}`;
        } catch (err) {
            byId('mapFeedback').textContent = err.message || 'Location data could not be loaded.';
            byId('lastRefresh').textContent = 'Refresh failed';
            if (!didFit) byId('locationResults').replaceChildren(element('div', 'alumni-map-empty', `${err.message} Use Refresh data to try again.`));
        } finally {
            isLoading = false;
            byId('refreshMap').disabled = false;
            byId('mapLoading').hidden = true;
            map.invalidateSize();
        }
    }

    let searchDelay;
    byId('alumniSearch').addEventListener('input', () => {
        clearTimeout(searchDelay);
        searchDelay = setTimeout(() => applyFilters(), 180);
    });
    filters.slice(1).forEach(id => byId(id).addEventListener('change', () => {
        if (id === 'groupBy') renderList(); else applyFilters();
    }));
    byId('clearFilters').addEventListener('click', () => {
        filters.slice(0, 4).forEach(id => { byId(id).value = ''; });
        applyFilters();
    });
    byId('refreshMap').addEventListener('click', () => loadLocations());
    byId('fitMap').addEventListener('click', fitAll);
    byId('myLocation').addEventListener('click', () => {
        if (!navigator.geolocation) { byId('mapFeedback').textContent = 'Your browser does not support location access.'; return; }
        byId('mapFeedback').textContent = 'Requesting your browser location; this does not share it with the server.';
        navigator.geolocation.getCurrentPosition(position => {
            map.setView([position.coords.latitude, position.coords.longitude], 14);
            byId('mapFeedback').textContent = 'Centered on your approximate device position (not shared).';
        }, () => { byId('mapFeedback').textContent = 'Your location is unavailable or permission was denied.'; },
        { enableHighAccuracy: false, timeout: 12000, maximumAge: 120000 });
    });
    window.addEventListener('resize', () => map.invalidateSize());
    loadLocations({ initial: true });
    setInterval(() => { if (!document.hidden && (!map._popup || !map._popup.isOpen())) loadLocations(); }, 60000);
})();
