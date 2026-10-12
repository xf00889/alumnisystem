/* Group feed composer. Independent of the legacy post/comment listeners. */
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        const form = document.getElementById('postForm');
        if (!form) return;
        const content = form.querySelector('[name="content"]');
        const image = form.querySelector('[name="image"]');
        const submit = form.querySelector('[type="submit"]');
        const counter = document.getElementById('groupPostCounter');
        const status = document.getElementById('groupPostFeedback');
        const preview = document.getElementById('groupPhotoPreview');
        const previewImage = document.getElementById('groupPhotoPreviewImage');
        const remove = document.getElementById('removeGroupPhoto');
        let previewUrl = null;
        function message(value, error) {
            status.hidden = false;
            status.textContent = value;
            status.classList.toggle('is-error', Boolean(error));
        }
        function clearPhoto() {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
            previewUrl = null;
            image.value = '';
            previewImage.removeAttribute('src');
            preview.hidden = true;
        }
        content.addEventListener('input', function () {
            counter.textContent = `${content.value.length} / 5000`;
        });
        image.addEventListener('change', function () {
            clearPreviewOnly();
            const file = image.files && image.files[0];
            if (!file) return;
            if (file.size > 5 * 1024 * 1024 || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
                message('Choose a JPEG, PNG, or WebP photo no larger than 5 MB.', true);
                image.value = '';
                return;
            }
            previewUrl = URL.createObjectURL(file);
            previewImage.src = previewUrl;
            preview.hidden = false;
            status.hidden = true;
        });
        function clearPreviewOnly() {
            if (previewUrl) URL.revokeObjectURL(previewUrl);
            previewUrl = null;
            preview.hidden = true;
        }
        remove.addEventListener('click', clearPhoto);
        form.addEventListener('submit', async function (event) {
            event.preventDefault();
            if (!content.value.trim() && !image.files.length) {
                message('Write an update or attach a photo before sharing.', true);
                content.focus();
                return;
            }
            submit.disabled = true;
            submit.setAttribute('aria-busy', 'true');
            message('Sharing your update…', false);
            try {
                const data = new FormData(form);
                const response = await fetch(form.action, {
                    method: 'POST', body: data, credentials: 'same-origin',
                    headers: { 'X-CSRFToken': data.get('csrfmiddlewaretoken'), 'Accept': 'application/json' }
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || 'Could not share your post.');
                form.reset();
                clearPreviewOnly();
                content.value = '';
                counter.textContent = '0 / 5000';
                message(result.message || 'Your post has been shared.', false);
                // Reload from the authoritative server rendering; do not create a fake approved post.
                const url = new URL(window.location.href);
                url.searchParams.set('tab', 'feed');
                window.location.assign(url.toString());
            } catch (error) {
                message(error.message || 'Network error. Try again.', true);
            } finally {
                submit.disabled = false;
                submit.removeAttribute('aria-busy');
            }
        });
        const current = new URLSearchParams(window.location.search).get('tab');
        if (current && current !== 'feed') {
            const tab = document.getElementById(current + '-tab');
            if (tab && window.bootstrap && window.bootstrap.Tab) {
                window.bootstrap.Tab.getOrCreateInstance(tab).show();
            }
        }
    });
}());
/* Use the existing comment form to reply to a particular comment, including AJAX-rendered comments. */
document.addEventListener('click', function (event) {
    const reply = event.target.closest('.group-comment-reply');
    if (!reply) return;
    const form = document.querySelector(`.comment-form[data-post-id="${reply.dataset.postId}"]`);
    if (!form) return;
    const parent = form.querySelector('[name="parent_id"]');
    const input = form.querySelector('[name="content"]');
    if (parent) parent.value = reply.dataset.commentId;
    if (input) { input.placeholder = 'Reply to @' + (reply.dataset.author || 'alumnus'); input.focus(); }
});

/* In-place refresh of the group timeline. Fetch only approved, authorized server HTML. */
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        const viewport = document.getElementById('groupFeedScroll');
        const holder = document.getElementById('groupFeedPosts');
        const scrollReload = document.getElementById('groupFeedScrollRefresh');
        const status = document.getElementById('groupFeedRefreshStatus');
        if (!viewport || !holder || !scrollReload || !status) return;
        let busy = false;
        function updateFloatingRefresh() {
            scrollReload.hidden = holder.scrollTop < 90;
        }
        holder.addEventListener('scroll', updateFloatingRefresh, { passive: true });
        updateFloatingRefresh();
        async function refresh() {
            if (busy) return;
            busy = true;
            scrollReload.disabled = true;
            scrollReload.setAttribute('aria-busy', 'true');
            const buttonLabel = scrollReload.innerHTML;
            const previousScroll = holder.scrollTop;
            scrollReload.textContent = 'Checking…';
            status.textContent = 'Checking for newer posts…';
            try {
                const url = new URL(scrollReload.dataset.url, window.location.href);
                url.searchParams.set('feed_sort', new URLSearchParams(window.location.search).get('feed_sort') || 'newest');
                const response = await fetch(url.toString(), {
                    credentials: 'same-origin', headers: { 'Accept': 'application/json' }, cache: 'no-store'
                });
                if (!response.ok) throw new Error(response.status === 403 ? 'Your group access has changed. Refresh the page.' : 'Could not load posts. Please retry.');
                const result = await response.json();
                if (typeof result.html !== 'string' || !Array.isArray(result.post_ids)) throw new Error('Unexpected response from server.');
                const existing = new Set(Array.from(holder.querySelectorAll('.post-card[id^="post-"]')).map(card => card.id));
                const fresh = result.post_ids.filter(id => !existing.has('post-' + id)).length;
                // Templates escape user content. Parsing into a detached template doesn't execute scripts.
                const fragment = document.createElement('template');
                fragment.innerHTML = result.html;
                holder.replaceChildren(fragment.content);
                holder.scrollTop = fresh ? 0 : previousScroll;
                document.dispatchEvent(new Event('group-feed:refreshed'));
                status.textContent = fresh ? `${fresh} newer post${fresh === 1 ? '' : 's'} loaded.` : 'Feed is up to date.';
                updateFloatingRefresh();
            } catch (error) {
                status.textContent = error.message || 'Could not refresh feed.';
            } finally {
                busy = false;
                scrollReload.disabled = false;
                scrollReload.removeAttribute('aria-busy');
                scrollReload.innerHTML = buttonLabel;
                updateFloatingRefresh();
            }
        }
        scrollReload.addEventListener('click', refresh);
        window.refreshGroupFeed = refresh;
    });
}());
