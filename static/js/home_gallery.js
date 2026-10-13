/* Progressive enhancement for CMS-managed NORSU campus, alumni, and staff galleries.
 * Usable without JS via native scroll-snap; motion is optional and pausable.
 */
(() => {
  'use strict';

  function init() {
    const root = document.querySelector('.home-experience');
    if (!root) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    // One-at-a-time FAQ behavior, preserving <details> when JavaScript is off.
    root.querySelectorAll('[data-home-accordion]').forEach((accordion) => {
      accordion.addEventListener('toggle', (event) => {
        const opened = event.target;
        if (!(opened instanceof HTMLDetailsElement) || !opened.open) return;
        accordion.querySelectorAll('details').forEach((other) => {
          if (other !== opened) other.open = false;
        });
      }, true);
    });

    root.querySelectorAll('[data-home-gallery]').forEach((gallery) => {
      const track = gallery.querySelector('[data-gallery-track]');
      const items = track ? [...track.querySelectorAll('[data-gallery-slide]')] : [];
      const prev = gallery.querySelector('[data-gallery-prev]') || gallery.closest('section')?.querySelector('[data-gallery-prev]');
      const next = gallery.querySelector('[data-gallery-next]') || gallery.closest('section')?.querySelector('[data-gallery-next]');
      const toggle = gallery.querySelector('[data-gallery-toggle]') || gallery.closest('section')?.querySelector('[data-gallery-toggle]');
      const dots = gallery.querySelector('[data-gallery-dots]');
      const status = gallery.querySelector('[data-gallery-status]');
      if (!track || !items.length || !prev || !next || !toggle) return;

      const intervalTime = Math.max(5000, Number(gallery.dataset.galleryInterval) || 6500);
      let visible = false;
      let playing = items.length > 1 && !reduceMotion.matches;
      let interrupted = false;
      let timer = null;
      let resizeObserver = null;
      const carouselName = gallery.getAttribute('aria-label') || 'gallery';

      function stepWidth() {
        const one = items[0];
        const style = window.getComputedStyle(track);
        const gap = parseFloat(style.columnGap || style.gap) || 0;
        return one.getBoundingClientRect().width + gap;
      }
      function maxScroll() { return Math.max(0, track.scrollWidth - track.clientWidth); }
      function currentIndex() {
        const step = stepWidth();
        return Math.min(items.length - 1, Math.max(0, Math.round(track.scrollLeft / (step || 1))));
      }
      function sync() {
        const index = currentIndex();
        prev.disabled = track.scrollLeft <= 2;
        next.disabled = track.scrollLeft >= maxScroll() - 2;
        if (status) status.textContent = `${String(index + 1).padStart(2, '0')} / ${String(items.length).padStart(2, '0')}`;
        if (dots) dots.querySelectorAll('button').forEach((dot, dotIndex) => {
          dot.setAttribute('aria-current', String(index === dotIndex));
        });
      }
      function scrollToIndex(index) {
        const target = items[Math.max(0, Math.min(index, items.length - 1))];
        if (!target) return;
        track.scrollTo({
          left: target.offsetLeft - items[0].offsetLeft,
          behavior: reduceMotion.matches ? 'instant' : 'smooth'
        });
      }
      function stopTimer() {
        if (timer !== null) window.clearInterval(timer);
        timer = null;
      }
      function syncToggle() {
        toggle.setAttribute('aria-pressed', String(playing));
        const canPlay = items.length > 1 && maxScroll() > 2 && !reduceMotion.matches;
        toggle.disabled = !canPlay;
        toggle.setAttribute('aria-label', playing ? `Pause ${carouselName}` : `Play ${carouselName}`);
        toggle.replaceChildren();
        const symbol = document.createElement('i');
        symbol.className = playing ? 'fas fa-pause' : 'fas fa-play';
        symbol.setAttribute('aria-hidden', 'true');
        toggle.append(symbol);
      }
      function setPlaying(value) {
        playing = Boolean(value && items.length > 1 && !reduceMotion.matches);
        syncToggle();
        schedule();
      }
      function schedule() {
        stopTimer();
        if (!visible || !playing || interrupted || document.hidden || maxScroll() <= 2) return;
        timer = window.setInterval(() => {
          if (track.scrollLeft >= maxScroll() - 3) scrollToIndex(0);
          else scrollToIndex(currentIndex() + 1);
        }, intervalTime);
      }
      function pauseOnInteraction() {
        // WCAG: once interacted with, automatic motion will not resume on blur.
        interrupted = true;
        setPlaying(false);
      }

      prev.addEventListener('click', () => { pauseOnInteraction(); scrollToIndex(currentIndex() - 1); });
      next.addEventListener('click', () => { pauseOnInteraction(); scrollToIndex(currentIndex() + 1); });
      toggle.addEventListener('click', () => {
        interrupted = false;
        setPlaying(!playing);
      });
      track.addEventListener('pointerdown', pauseOnInteraction, { passive: true });
      gallery.addEventListener('focusin', pauseOnInteraction);
      // Controls may live in the adjacent heading rather than the gallery.
      [prev, next, toggle].forEach((button) => button.addEventListener('focus', pauseOnInteraction));
      track.addEventListener('keydown', (event) => {
        if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
        pauseOnInteraction();
        event.preventDefault();
        if (event.key === 'Home') scrollToIndex(0);
        else if (event.key === 'End') scrollToIndex(items.length - 1);
        else scrollToIndex(currentIndex() + (event.key === 'ArrowRight' ? 1 : -1));
      });
      track.addEventListener('scroll', () => window.requestAnimationFrame(sync), { passive: true });
      if (dots) {
        items.forEach((_, index) => {
          const dot = document.createElement('button');
          dot.type = 'button';
          dot.setAttribute('aria-label', `Show ${carouselName} item ${index + 1}`);
          dot.setAttribute('aria-current', String(index === 0));
          dot.addEventListener('click', () => { pauseOnInteraction(); scrollToIndex(index); });
          dots.append(dot);
        });
      }
      if ('ResizeObserver' in window) {
        resizeObserver = new ResizeObserver(() => { sync(); syncToggle(); schedule(); });
        resizeObserver.observe(track);
      } else {
        window.addEventListener('resize', () => { sync(); syncToggle(); schedule(); }, { passive: true });
      }
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
          visible = entries[0].isIntersecting;
          schedule();
        }, { threshold: .15 });
        observer.observe(gallery);
      } else {
        visible = true;
      }
      reduceMotion.addEventListener?.('change', () => setPlaying(false));
      document.addEventListener('visibilitychange', schedule);
      sync();
      syncToggle();
      schedule();
    });

    // Appearance-only reveal motion; added only with observer support.
    if (!reduceMotion.matches && 'IntersectionObserver' in window) {
      const candidates = root.querySelectorAll('.home-section-header, .home-feature-item, .home-journey-steps article, .home-announcement-item, .home-events-panel, .home-vm-grid article, .home-feedback-panel');
      const reveal = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      }, { threshold: .08, rootMargin: '0px 0px 35px 0px' });
      candidates.forEach((node) => { node.classList.add('home-reveal'); reveal.observe(node); });
      root.classList.add('has-motion');
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
