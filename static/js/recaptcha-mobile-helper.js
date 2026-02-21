/**
 * reCAPTCHA Mobile Helper
 * 
 * Improves reCAPTCHA badge positioning on mobile devices by:
 * - Detecting form focus and adjusting badge position
 * - Detecting keyboard open state
 * - Adding appropriate classes to body for CSS targeting
 */

(function() {
    'use strict';
    
    // Check if we're on a mobile device
    const isMobile = window.innerWidth <= 767.98;
    
    if (!isMobile) {
        return; // Skip on desktop
    }
    
    // Add class to body if bottom navigation exists
    function checkBottomNav() {
        const bottomNav = document.querySelector('.mobile-bottom-nav');
        if (bottomNav) {
            document.body.classList.add('has-bottom-nav');
        }
    }
    
    // Detect when form inputs are focused (keyboard likely open)
    function setupFormFocusDetection() {
        const formInputs = document.querySelectorAll('input, textarea, select');
        
        formInputs.forEach(input => {
            input.addEventListener('focus', () => {
                document.body.classList.add('form-focused');
                document.body.classList.add('keyboard-open');
            });
            
            input.addEventListener('blur', () => {
                // Delay removal to allow for switching between inputs
                setTimeout(() => {
                    const activeElement = document.activeElement;
                    const isFormElement = activeElement.tagName === 'INPUT' || 
                                         activeElement.tagName === 'TEXTAREA' || 
                                         activeElement.tagName === 'SELECT';
                    
                    if (!isFormElement) {
                        document.body.classList.remove('form-focused');
                        document.body.classList.remove('keyboard-open');
                    }
                }, 100);
            });
        });
    }
    
    // Detect scroll direction
    let lastScrollTop = 0;
    function setupScrollDetection() {
        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > 50) {
                // Scrolling down
                document.body.classList.add('scrolled-down');
            } else {
                // Scrolling up
                document.body.classList.remove('scrolled-down');
            }
            
            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }, { passive: true });
    }
    
    // Detect viewport resize (orientation change, keyboard open/close)
    let initialHeight = window.innerHeight;
    function setupResizeDetection() {
        window.addEventListener('resize', () => {
            const currentHeight = window.innerHeight;
            
            // If viewport height decreased significantly, keyboard is likely open
            if (initialHeight - currentHeight > 150) {
                document.body.classList.add('keyboard-open');
            } else {
                document.body.classList.remove('keyboard-open');
            }
        });
    }
    
    // Check if we're on a standalone auth page (login/signup without main nav)
    function checkStandaloneAuth() {
        const hasMainNav = document.querySelector('.navbar:not(.mobile-bottom-nav)');
        const isAuthPage = window.location.pathname.includes('/accounts/');
        
        if (isAuthPage && !hasMainNav) {
            document.body.classList.add('standalone-auth');
        }
    }
    
    // Adjust reCAPTCHA badge position dynamically
    function adjustRecaptchaBadge() {
        // Wait for reCAPTCHA badge to load
        const checkBadge = setInterval(() => {
            const badge = document.querySelector('.grecaptcha-badge');
            
            if (badge) {
                clearInterval(checkBadge);
                
                // Add custom data attribute for easier targeting
                badge.setAttribute('data-mobile-adjusted', 'true');
                
                // Log for debugging
                console.log('reCAPTCHA badge detected and adjusted for mobile');
            }
        }, 500);
        
        // Stop checking after 10 seconds
        setTimeout(() => clearInterval(checkBadge), 10000);
    }
    
    // Initialize all helpers
    function init() {
        // Run checks when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                checkBottomNav();
                checkStandaloneAuth();
                setupFormFocusDetection();
                setupScrollDetection();
                setupResizeDetection();
                adjustRecaptchaBadge();
            });
        } else {
            // DOM already loaded
            checkBottomNav();
            checkStandaloneAuth();
            setupFormFocusDetection();
            setupScrollDetection();
            setupResizeDetection();
            adjustRecaptchaBadge();
        }
    }
    
    // Start the helper
    init();
    
    // Expose utility function for manual adjustment
    window.adjustRecaptchaBadgePosition = function() {
        const badge = document.querySelector('.grecaptcha-badge');
        if (badge) {
            // Force recalculation
            badge.style.display = 'none';
            setTimeout(() => {
                badge.style.display = '';
            }, 10);
        }
    };
    
})();
