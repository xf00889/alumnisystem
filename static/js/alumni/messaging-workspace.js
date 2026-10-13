/* Alumni messaging workspace: presentation and keyboard navigation only.
   The existing HTMX, group messaging, attachment, and send handlers remain authoritative. */
(() => {
  'use strict';

  const workspace = document.querySelector('[data-messaging-workspace]');
  if (!workspace || !document.body.classList.contains('alumni-portal')) return;

  const detail = workspace.querySelector('#conversation-detail');
  const back = workspace.querySelector('.messaging-mobile-back');
  const mobile = window.matchMedia('(max-width: 767.98px)');
  if (!detail || !back) return;

  let pendingConversation = false;
  let lastSelected = null;
  let activeRequest = null;
  let requestSequence = 0;

  function enhanceItems(root = workspace) {
    root.querySelectorAll('.conversation-item').forEach((item) => {
      if (!item.hasAttribute('tabindex')) item.tabIndex = 0;
      if (!item.hasAttribute('role')) item.setAttribute('role', 'button');
      if (!item.hasAttribute('aria-label') || item.getAttribute('aria-label') === 'Open conversation') {
        const name = item.querySelector('.conversation-name, h6')?.textContent?.trim() || 'conversation';
        item.setAttribute('aria-label', `Open conversation with ${name}`);
      }
      item.setAttribute('aria-pressed', item.classList.contains('active') ? 'true' : 'false');
    });
  }

  // Mobile Safari may leave 100dvh unchanged when its on-screen keyboard
  // appears. Track the actual visible viewport so the composer stays visible.
  function syncMobileViewport() {
    if (!mobile.matches) {
      document.documentElement.style.removeProperty('--norsu-chat-visual-height');
      return;
    }
    const visibleHeight = window.visualViewport?.height || window.innerHeight;
    if (visibleHeight > 0) {
      document.documentElement.style.setProperty('--norsu-chat-visual-height', `${Math.round(visibleHeight)}px`);
    }
  }

  function scrollChatToLatest() {
    const scroller = detail.querySelector('#messagesContainer, #messages-container');
    if (!scroller) return;
    scroller.scrollTop = getComputedStyle(scroller).flexDirection === 'column-reverse'
      ? 0 : scroller.scrollHeight;
  }

  syncMobileViewport();
  window.addEventListener('resize', syncMobileViewport, { passive: true });
  window.visualViewport?.addEventListener('resize', syncMobileViewport, { passive: true });
  mobile.addEventListener?.('change', syncMobileViewport);

  function showChat() {
    if (!mobile.matches) return;
    syncMobileViewport();
    workspace.classList.add('is-chat-open');
    // Compatibility with the existing HTMX handlers; CSS keeps this within the workspace.
    document.body.classList.add('mobile-conversation-active');
    back.focus({ preventScroll: true });
    requestAnimationFrame(scrollChatToLatest);
  }

  function showInbox() {
    if (activeRequest) activeRequest.abort();
    activeRequest = null;
    requestSequence += 1;
    workspace.classList.remove('is-chat-open');
    document.body.classList.remove('mobile-conversation-active');
    pendingConversation = false;
    if (lastSelected && lastSelected.isConnected) lastSelected.focus({ preventScroll: true });
    else workspace.querySelector('#searchInput')?.focus({ preventScroll: true });
  }

  function conversationLoaded() {
    const loaded = detail.querySelector('.chat-container, .conversation-content');
    if (!loaded || !pendingConversation) return;
    pendingConversation = false;
    showChat();
  }

  // On small screens the conversation list is a full-screen inbox. HTMX's
  // per-item clicks may not run when its CDN is unavailable; use a single
  // same-origin partial fetch instead and leave desktop HTMX untouched.
  async function openMobileConversation(item) {
    const url = item.getAttribute('data-mobile-url') || item.getAttribute('hx-get');
    if (!url) return;
    if (activeRequest) activeRequest.abort();
    const request = new AbortController();
    activeRequest = request;
    const sequence = ++requestSequence;
    lastSelected = item;
    pendingConversation = false;
    workspace.querySelectorAll('.conversation-item').forEach((other) => {
      const selected = other === item;
      other.classList.toggle('active', selected);
      other.setAttribute('aria-pressed', String(selected));
    });
    detail.innerHTML = '<div class="messaging-loading-state" role="status">Loading messages…</div>';
    showChat();
    try {
      const response = await fetch(url, {
        method: 'GET', credentials: 'same-origin', redirect: 'error',
        headers: { 'HX-Request': 'true', 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'text/html' },
        signal: request.signal
      });
      if (!response.ok) throw new Error('Could not open this conversation. Please retry.');
      if (!(response.headers.get('Content-Type') || '').includes('text/html')) {
        throw new Error('Unexpected response. Please sign in again.');
      }
      const html = await response.text();
      if (sequence !== requestSequence || request.signal.aborted) return;
      const parsed = new DOMParser().parseFromString(html, 'text/html');
      if (!parsed.querySelector('.chat-container, .conversation-content')) {
        throw new Error('This conversation could not be displayed.');
      }
      detail.innerHTML = html;
      // The original HTMX swap executes script elements in message partials.
      // Preserve that behavior for existing attachment and send handlers.
      detail.querySelectorAll('script').forEach((script) => {
        const active = document.createElement('script');
        for (const attr of script.attributes) active.setAttribute(attr.name, attr.value);
        active.textContent = script.textContent;
        script.replaceWith(active);
      });
      if (window.htmx) window.htmx.process(detail);
      requestAnimationFrame(scrollChatToLatest);
    } catch (error) {
      if (request.signal.aborted || sequence !== requestSequence) return;
      detail.replaceChildren();
      const state = document.createElement('div');
      state.className = 'messaging-loading-state messaging-error-state';
      state.setAttribute('role', 'alert');
      const note = document.createElement('p');
      note.textContent = error.message || 'Unable to load messages.';
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'btn btn-primary';
      retry.textContent = 'Try again';
      retry.addEventListener('click', () => openMobileConversation(item));
      state.append(note, retry);
      detail.append(state);
    } finally {
      if (activeRequest === request) activeRequest = null;
    }
  }

  workspace.addEventListener('click', (event) => {
    const item = event.target.closest('.conversation-item');
    if (!item || !workspace.contains(item) || !mobile.matches) return;
    // Capture before inline handlers/HTMX to prevent duplicate network loads.
    event.preventDefault();
    event.stopPropagation();
    openMobileConversation(item);
  }, true);

  workspace.addEventListener('click', (event) => {
    if (event.target.closest('#inlineSendMessage, #createGroupBtn')) {
      pendingConversation = true;
      return;
    }
    const item = event.target.closest('.conversation-item');
    if (!item || !workspace.contains(item)) return;
    lastSelected = item;
    pendingConversation = true;
    workspace.querySelectorAll('.conversation-item').forEach((other) => {
      other.classList.toggle('active', other === item);
      other.setAttribute('aria-pressed', other === item ? 'true' : 'false');
    });
    // Network responses may be returned by HTMX or the existing manual fetch functions.
    // The detail observer below opens only when a real conversation has rendered.
  });

  workspace.addEventListener('keydown', (event) => {
    const item = event.target.closest('.conversation-item');
    if (!item || !workspace.contains(item)) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      item.click();
    }
  });

  back.addEventListener('click', showInbox);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && workspace.classList.contains('is-chat-open') && mobile.matches) {
      event.preventDefault();
      showInbox();
    }
  });

  const detailObserver = new MutationObserver(() => conversationLoaded());
  detailObserver.observe(detail, { childList: true });

  document.addEventListener('htmx:afterSwap', (event) => {
    const target = event.detail?.target;
    if (!target) return;
    if (target === detail || detail.contains(target)) conversationLoaded();
    if (target.id === 'conversationsList' || target.contains?.(workspace.querySelector('#conversationsList'))) {
      enhanceItems();
    }
  });

  mobile.addEventListener('change', (event) => {
    if (!event.matches) {
      if (activeRequest) activeRequest.abort();
      activeRequest = null;
      requestSequence += 1;
      workspace.classList.remove('is-chat-open');
      document.body.classList.remove('mobile-conversation-active');
    }
  });

  // Support the existing group-conversation manual fetch, which doesn't dispatch HTMX events.
  // The observer intentionally does not change or retry requests.
  enhanceItems();

  // Opening a connected alumnus from their directory profile must open that
  // user's thread, not just the inbox. Use the same fragment loader on phones
  // and desktops to support conversations that contain no messages yet.
  const initialUserId = workspace.dataset.initialChatUserId;
  if (initialUserId && /^\d+$/.test(initialUserId)) {
    const openInitial = () => {
      const item = [...workspace.querySelectorAll('.conversation-item[data-direct-user-id]')]
        .find(node => node.dataset.directUserId === initialUserId);
      if (item) openMobileConversation(item);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', openInitial, { once: true });
    else openInitial();
  }
})();
