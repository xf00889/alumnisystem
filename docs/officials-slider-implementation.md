# Officials Slider Implementation

## Overview
The Officials Slider is a responsive, touch-enabled carousel component designed to display the ~20 active University Alumni Affairs Officials on the homepage. It replaces the previous static grid layout with a dynamic slider that provides better UX for large numbers of staff members.

## Features

### Core Functionality
- **Responsive Design**: Automatically adjusts slides per view based on screen size
  - Desktop (≥1200px): 4 slides
  - Tablet (992-1199px): 3 slides
  - Small Tablet (768-991px): 2 slides
  - Mobile (<768px): 1 slide

- **Navigation Controls**:
  - Previous/Next arrow buttons
  - Dot pagination indicators
  - Keyboard navigation (Arrow Left/Right)
  - Touch/swipe gestures on mobile devices

- **Accessibility**:
  - ARIA labels and roles
  - Keyboard navigation support
  - Focus management
  - Screen reader friendly

### User Interactions
1. **Click Navigation**: Use arrow buttons to navigate
2. **Dot Navigation**: Click dots to jump to specific slides
3. **Keyboard**: Use arrow keys when slider is in viewport
4. **Touch/Swipe**: Swipe left/right on touch devices
5. **Mouse Drag**: Drag to navigate on desktop (optional)

## Files

### JavaScript
- **Location**: `static/js/officials_slider.js`
- **Class**: `OfficialsSlider`
- **Dependencies**: None (vanilla JavaScript)

### CSS
- **Location**: `static/css/officials_slider.css`
- **Features**: 
  - Responsive breakpoints
  - Smooth transitions
  - Touch-friendly controls
  - Modern design matching site theme

### Template
- **Location**: `templates/home.html`
- **Section**: Staff Section (Office of the University Alumni Affairs Officials)

## Configuration

### Auto-play (Optional)
To enable auto-play, uncomment the auto-play code in `officials_slider.js`:

```javascript
// Optional: Auto-play (uncomment to enable)
let autoplayInterval;
const startAutoplay = () => {
    autoplayInterval = setInterval(() => {
        if (slider.currentIndex >= slider.maxIndex) {
            slider.goToSlide(0);
        } else {
            slider.next();
        }
    }, 5000); // Change slide every 5 seconds
};
```

### Customization

#### Slides Per View
Modify the `getSlidesPerView()` method in `officials_slider.js`:

```javascript
getSlidesPerView() {
    const width = window.innerWidth;
    if (width < 768) return 1;
    if (width < 992) return 2;
    if (width < 1200) return 3;
    return 4; // Change this for desktop
}
```

#### Transition Speed
Modify the CSS transition in `officials_slider.css`:

```css
.officials-track.transitioning {
    transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
```

#### Gap Between Slides
Modify the gap in `officials_slider.css`:

```css
.officials-track {
    gap: 1.5rem; /* Change this value */
}
```

And update the JavaScript calculation in `updateSlider()`:

```javascript
const gap = 24; // 1.5rem in pixels - update to match CSS
```

## Browser Support
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Full support with touch gestures

## Performance
- Lightweight: ~8KB JavaScript (unminified)
- No external dependencies
- Smooth 60fps animations
- Optimized for touch devices

## Accessibility Compliance
- WCAG 2.1 Level AA compliant
- Keyboard navigable
- Screen reader friendly
- Focus indicators
- ARIA labels and roles

## Troubleshooting

### Slider not initializing
1. Check browser console for errors
2. Verify `officials_slider.js` is loaded
3. Ensure `.officials-slider-container` element exists

### Navigation buttons not working
1. Check if there are enough slides (needs more than slidesPerView)
2. Verify button elements have correct classes
3. Check console for JavaScript errors

### Responsive issues
1. Clear browser cache
2. Run `python manage.py collectstatic --noinput`
3. Check CSS media queries

### Touch/swipe not working
1. Ensure touch-action CSS is applied
2. Check for conflicting event listeners
3. Test on actual device (not just browser DevTools)

## Future Enhancements
- [ ] Lazy loading for staff images
- [ ] Infinite loop mode
- [ ] Vertical slider option
- [ ] Animation effects (fade, slide, etc.)
- [ ] Thumbnail navigation
- [ ] Video support for staff introductions

## Maintenance
- Update `officials_slider.js` for new features
- Test on new browser versions
- Monitor performance metrics
- Gather user feedback for improvements

## Related Files
- `cms/models.py`: StaffMember model
- `core/views.py`: Homepage view with staff_members context
- `templates/home.html`: Main template
- `static/css/base.css`: Staff card styles
