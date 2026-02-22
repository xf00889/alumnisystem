/**
 * Officials Slider - Lightweight, responsive carousel for staff members
 * Features: Touch/swipe support, keyboard navigation, responsive breakpoints
 */

class OfficialsSlider {
    constructor(container) {
        this.container = container;
        this.track = container.querySelector('.officials-track');
        this.slides = Array.from(container.querySelectorAll('.official-slide'));
        this.prevBtn = container.querySelector('.slider-nav-prev');
        this.nextBtn = container.querySelector('.slider-nav-next');
        this.dotsContainer = container.querySelector('.slider-dots');
        
        this.currentIndex = 0;
        this.slidesPerView = this.getSlidesPerView();
        this.totalSlides = this.slides.length;
        this.maxIndex = Math.max(0, this.totalSlides - this.slidesPerView);
        
        // Touch/swipe support
        this.isDragging = false;
        this.startPos = 0;
        this.currentTranslate = 0;
        this.prevTranslate = 0;
        this.animationID = null;
        
        this.init();
    }
    
    init() {
        if (this.totalSlides === 0) return;
        
        // Hide slider controls if not enough slides
        if (this.totalSlides <= this.slidesPerView) {
            this.prevBtn?.classList.add('d-none');
            this.nextBtn?.classList.add('d-none');
            this.dotsContainer?.classList.add('d-none');
            return;
        }
        
        // Create dots
        this.createDots();
        
        // Event listeners
        this.prevBtn?.addEventListener('click', () => this.prev());
        this.nextBtn?.addEventListener('click', () => this.next());
        
        // Touch events
        this.track.addEventListener('touchstart', this.touchStart.bind(this), { passive: true });
        this.track.addEventListener('touchmove', this.touchMove.bind(this), { passive: true });
        this.track.addEventListener('touchend', this.touchEnd.bind(this));
        
        // Mouse events for desktop drag
        this.track.addEventListener('mousedown', this.touchStart.bind(this));
        this.track.addEventListener('mousemove', this.touchMove.bind(this));
        this.track.addEventListener('mouseup', this.touchEnd.bind(this));
        this.track.addEventListener('mouseleave', this.touchEnd.bind(this));
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (this.isInViewport()) {
                if (e.key === 'ArrowLeft') this.prev();
                if (e.key === 'ArrowRight') this.next();
            }
        });
        
        // Responsive handling
        window.addEventListener('resize', this.debounce(() => {
            const newSlidesPerView = this.getSlidesPerView();
            if (newSlidesPerView !== this.slidesPerView) {
                this.slidesPerView = newSlidesPerView;
                this.maxIndex = Math.max(0, this.totalSlides - this.slidesPerView);
                this.currentIndex = Math.min(this.currentIndex, this.maxIndex);
                this.updateSlider();
            }
        }, 250));
        
        // Initial update
        this.updateSlider();
    }
    
    getSlidesPerView() {
        const width = window.innerWidth;
        if (width < 768) return 1;
        if (width < 992) return 2;
        if (width < 1200) return 3;
        return 4;
    }
    
    createDots() {
        if (!this.dotsContainer) return;
        
        this.dotsContainer.innerHTML = '';
        const numDots = this.maxIndex + 1;
        
        for (let i = 0; i < numDots; i++) {
            const dot = document.createElement('button');
            dot.className = 'slider-dot';
            dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
            dot.addEventListener('click', () => this.goToSlide(i));
            this.dotsContainer.appendChild(dot);
        }
    }
    
    updateSlider(animate = true) {
        // Update track position
        const slideWidth = this.slides[0]?.offsetWidth || 0;
        const gap = 32; // 2rem in pixels
        const offset = -(this.currentIndex * (slideWidth + gap));
        
        if (animate) {
            this.track.classList.add('transitioning');
        } else {
            this.track.classList.remove('transitioning');
        }
        
        // Use transform for smooth animation
        this.track.style.transform = `translateX(${offset}px)`;
        
        // Update navigation buttons
        this.updateNavButtons();
        
        // Update dots
        this.updateDots();
        
        // Remove transition class after animation
        if (animate) {
            setTimeout(() => {
                this.track.classList.remove('transitioning');
            }, 500);
        }
    }
    
    updateNavButtons() {
        if (this.prevBtn) {
            this.prevBtn.classList.toggle('disabled', this.currentIndex === 0);
            this.prevBtn.setAttribute('aria-disabled', this.currentIndex === 0);
        }
        if (this.nextBtn) {
            this.nextBtn.classList.toggle('disabled', this.currentIndex >= this.maxIndex);
            this.nextBtn.setAttribute('aria-disabled', this.currentIndex >= this.maxIndex);
        }
    }
    
    updateDots() {
        const dots = this.dotsContainer?.querySelectorAll('.slider-dot');
        dots?.forEach((dot, index) => {
            dot.classList.toggle('active', index === this.currentIndex);
        });
    }
    
    prev() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.updateSlider();
        }
    }
    
    next() {
        if (this.currentIndex < this.maxIndex) {
            this.currentIndex++;
            this.updateSlider();
        }
    }
    
    goToSlide(index) {
        this.currentIndex = Math.max(0, Math.min(index, this.maxIndex));
        this.updateSlider();
    }
    
    // Touch/Swipe support
    touchStart(e) {
        this.isDragging = true;
        this.startPos = this.getPositionX(e);
        this.animationID = requestAnimationFrame(this.animation.bind(this));
        this.container.classList.add('dragging');
    }
    
    touchMove(e) {
        if (this.isDragging) {
            const currentPosition = this.getPositionX(e);
            this.currentTranslate = this.prevTranslate + currentPosition - this.startPos;
        }
    }
    
    touchEnd() {
        this.isDragging = false;
        cancelAnimationFrame(this.animationID);
        this.container.classList.remove('dragging');
        
        const movedBy = this.currentTranslate - this.prevTranslate;
        
        // Swipe threshold: 50px
        if (movedBy < -50 && this.currentIndex < this.maxIndex) {
            this.next();
        } else if (movedBy > 50 && this.currentIndex > 0) {
            this.prev();
        } else {
            this.updateSlider();
        }
        
        this.prevTranslate = this.currentTranslate;
    }
    
    getPositionX(e) {
        return e.type.includes('mouse') ? e.pageX : e.touches[0].clientX;
    }
    
    animation() {
        if (this.isDragging) {
            requestAnimationFrame(this.animation.bind(this));
        }
    }
    
    isInViewport() {
        const rect = this.container.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Public method to refresh slider (useful after dynamic content changes)
    refresh() {
        this.slides = Array.from(this.container.querySelectorAll('.official-slide'));
        this.totalSlides = this.slides.length;
        this.slidesPerView = this.getSlidesPerView();
        this.maxIndex = Math.max(0, this.totalSlides - this.slidesPerView);
        this.currentIndex = Math.min(this.currentIndex, this.maxIndex);
        this.createDots();
        this.updateSlider(false);
    }
}

// Initialize slider when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const sliderContainer = document.querySelector('.officials-slider-container');
    if (sliderContainer) {
        // Add loading state
        sliderContainer.classList.add('loading');
        
        // Initialize slider after a brief delay to ensure proper layout
        setTimeout(() => {
            const slider = new OfficialsSlider(sliderContainer);
            sliderContainer.classList.remove('loading');
            
            // Optional: Auto-play (uncomment to enable)
            // let autoplayInterval;
            // const startAutoplay = () => {
            //     autoplayInterval = setInterval(() => {
            //         if (slider.currentIndex >= slider.maxIndex) {
            //             slider.goToSlide(0);
            //         } else {
            //             slider.next();
            //         }
            //     }, 5000); // Change slide every 5 seconds
            // };
            
            // const stopAutoplay = () => {
            //     clearInterval(autoplayInterval);
            // };
            
            // // Start autoplay
            // startAutoplay();
            
            // // Pause on hover
            // sliderContainer.addEventListener('mouseenter', stopAutoplay);
            // sliderContainer.addEventListener('mouseleave', startAutoplay);
            
            // // Pause on focus (accessibility)
            // sliderContainer.addEventListener('focusin', stopAutoplay);
            // sliderContainer.addEventListener('focusout', startAutoplay);
            
            // Make slider instance globally accessible for debugging
            window.officialsSlider = slider;
            
            // Add smooth scroll to slider when it comes into view
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        sliderContainer.classList.add('in-view');
                    }
                });
            }, { threshold: 0.2 });
            
            observer.observe(sliderContainer);
        }, 100);
    }
});
