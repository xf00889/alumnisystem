(function () {
    'use strict';

    function initializeGallery(gallery) {
        const section = gallery.closest('.home-shell');
        const track = gallery.querySelector('.home-team-track');
        const previousButton = section ? section.querySelector('[data-team-previous]') : null;
        const nextButton = section ? section.querySelector('[data-team-next]') : null;

        if (!track || !previousButton || !nextButton) {
            return;
        }

        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        let updateFrame = null;

        function scrollStep() {
            const firstMember = track.querySelector('.home-team-member');
            if (!firstMember) {
                return track.clientWidth;
            }

            const trackStyles = window.getComputedStyle(track);
            const gap = Number.parseFloat(trackStyles.columnGap || trackStyles.gap) || 0;
            return firstMember.getBoundingClientRect().width + gap;
        }

        function updateControls() {
            const maximumScroll = Math.max(0, track.scrollWidth - track.clientWidth);
            previousButton.disabled = track.scrollLeft <= 2;
            nextButton.disabled = track.scrollLeft >= maximumScroll - 2;
        }

        function requestControlUpdate() {
            if (updateFrame !== null) {
                return;
            }

            updateFrame = window.requestAnimationFrame(function () {
                updateFrame = null;
                updateControls();
            });
        }

        function move(direction) {
            track.scrollBy({
                left: scrollStep() * direction,
                behavior: reducedMotion.matches ? 'auto' : 'smooth'
            });
        }

        previousButton.addEventListener('click', function () {
            move(-1);
        });

        nextButton.addEventListener('click', function () {
            move(1);
        });

        track.addEventListener('scroll', requestControlUpdate, { passive: true });
        track.addEventListener('keydown', function (event) {
            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                move(-1);
            } else if (event.key === 'ArrowRight') {
                event.preventDefault();
                move(1);
            } else if (event.key === 'Home') {
                event.preventDefault();
                track.scrollTo({ left: 0, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
            } else if (event.key === 'End') {
                event.preventDefault();
                track.scrollTo({ left: track.scrollWidth, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
            }
        });

        if ('ResizeObserver' in window) {
            const resizeObserver = new ResizeObserver(requestControlUpdate);
            resizeObserver.observe(track);
        } else {
            window.addEventListener('resize', requestControlUpdate, { passive: true });
        }

        updateControls();
    }

    function initializeTeamGalleries() {
        document.querySelectorAll('[data-team-gallery]').forEach(initializeGallery);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeTeamGalleries, { once: true });
    } else {
        initializeTeamGalleries();
    }
}());
