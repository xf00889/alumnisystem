/**
 * Officials Slider - Modern responsive carousel using Swiper.js
 * Lightweight, touch-enabled, accessible slider for staff members
 */

document.addEventListener('DOMContentLoaded', function() {
    const sliderContainer = document.querySelector('.officials-swiper');
    
    if (!sliderContainer) {
        console.warn('Officials slider container not found');
        return;
    }

    // Initialize Swiper
    const officialsSwiper = new Swiper('.officials-swiper', {
        // Responsive breakpoints
        slidesPerView: 1,
        spaceBetween: 20,
        centeredSlides: true,
        
        breakpoints: {
            // Mobile landscape and up
            576: {
                slidesPerView: 1,
                spaceBetween: 20,
                centeredSlides: true
            },
            // Tablet and up
            768: {
                slidesPerView: 2,
                spaceBetween: 24,
                centeredSlides: false
            },
            // Desktop and up
            992: {
                slidesPerView: 3,
                spaceBetween: 30,
                centeredSlides: false
            },
            // Large desktop
            1200: {
                slidesPerView: 4,
                spaceBetween: 32,
                centeredSlides: false
            }
        },

        // Navigation arrows
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },

        // Pagination dots
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
            dynamicBullets: true,
            dynamicMainBullets: 3
        },

        // Keyboard control
        keyboard: {
            enabled: true,
            onlyInViewport: true
        },

        // Mouse wheel control
        mousewheel: {
            forceToAxis: true,
            sensitivity: 1,
            releaseOnEdges: true
        },

        // Touch settings
        touchRatio: 1,
        touchAngle: 45,
        grabCursor: true,

        // Accessibility
        a11y: {
            enabled: true,
            prevSlideMessage: 'Previous official',
            nextSlideMessage: 'Next official',
            firstSlideMessage: 'This is the first official',
            lastSlideMessage: 'This is the last official',
            paginationBulletMessage: 'Go to official {{index}}'
        },

        // Performance
        watchSlidesProgress: true,
        watchSlidesVisibility: true,
        preloadImages: false,
        lazy: {
            loadPrevNext: true,
            loadPrevNextAmount: 2
        },

        // Effects
        speed: 400,
        effect: 'slide',

        // Auto height
        autoHeight: false,

        // Loop (optional - enable if you want infinite scroll)
        loop: false,

        // Optional: Autoplay (uncomment to enable)
        // autoplay: {
        //     delay: 5000,
        //     disableOnInteraction: true,
        //     pauseOnMouseEnter: true
        // },

        // Events
        on: {
            init: function() {
                console.log('Officials slider initialized');
                sliderContainer.classList.add('swiper-initialized');
            },
            slideChange: function() {
                // Optional: Add analytics or custom behavior on slide change
            },
            reachEnd: function() {
                // Optional: Handle reaching the end
            }
        }
    });

    // Make swiper instance globally accessible for debugging
    window.officialsSwiper = officialsSwiper;

    // Optional: Pause autoplay on focus (accessibility)
    if (officialsSwiper.autoplay && officialsSwiper.autoplay.running) {
        sliderContainer.addEventListener('focusin', () => {
            officialsSwiper.autoplay.stop();
        });
        
        sliderContainer.addEventListener('focusout', () => {
            officialsSwiper.autoplay.start();
        });
    }

    // Add intersection observer for animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                sliderContainer.classList.add('in-view');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    });

    observer.observe(sliderContainer);
});
