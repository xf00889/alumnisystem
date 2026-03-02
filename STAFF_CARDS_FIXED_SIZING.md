# Staff Cards - Fixed Sizing Implementation

## Overview
Updated the staff section cards to have consistent, fixed dimensions across all cards in the slider, ensuring a uniform and professional appearance.

## Changes Made

### 1. Fixed Card Dimensions

**Desktop (992px+)**
- Card Height: `380px` (fixed)
- Card Width: `100%` with `max-width: 320px`
- Padding: `2rem`

**Mobile (< 576px)**
- Card Height: `340px` (fixed)
- Card Width: `100%` with `max-width: 280px`
- Padding: `1.5rem 1rem`

### 2. Fixed Content Heights

All text elements now have fixed minimum heights to ensure consistency:

**Desktop:**
- Staff Name: `min-height: 2.6rem` (2 lines max)
- Position: `min-height: 2.4rem` (2 lines max)
- Department: `min-height: 2.4rem` (2 lines max)
- Bio: `min-height: 3rem`, `max-height: 3rem` (2 lines max)

**Mobile:**
- Staff Name: `min-height: 2.4rem`
- Position: `min-height: 2.2rem`
- Department: `min-height: 2.2rem`
- Bio: `min-height: 2.8rem`, `max-height: 2.8rem`

### 3. Text Truncation

All text fields use CSS line clamping to prevent overflow:
```css
display: -webkit-box;
-webkit-line-clamp: 2;
-webkit-box-orient: vertical;
overflow: hidden;
text-overflow: ellipsis;
```

### 4. Avatar Sizing

**Desktop:**
- Width/Height: `100px`
- Margin: `0 auto 1.25rem`
- `flex-shrink: 0` to prevent shrinking

**Mobile:**
- Width/Height: `80px`
- Margin: `0 auto 1rem`

### 5. Font Size Adjustments

Slightly reduced font sizes for better fit:

**Desktop:**
- Name: `1.125rem` (was `1.25rem`)
- Position: `0.9375rem` (was `1rem`)
- Department: `0.8125rem` (was `0.875rem`)
- Bio: `0.8125rem` (was `0.875rem`)

**Mobile:**
- Name: `1rem`
- Position: `0.875rem`
- Department: `0.75rem`
- Bio: `0.75rem`

### 6. Swiper Slide Consistency

```css
.swiper-slide {
    height: auto;
    display: flex;
    align-items: center;
    justify-content: center;
}
```

This ensures all slides have the same height and cards are centered.

## Benefits

✅ **Consistent Card Heights** - All cards have the same height regardless of content length  
✅ **Professional Appearance** - Uniform sizing creates a polished look  
✅ **Better Slider Experience** - Cards align perfectly in the carousel  
✅ **Responsive Design** - Maintains consistency across all screen sizes  
✅ **Text Overflow Handling** - Long names/positions are truncated gracefully  
✅ **Centered Cards** - Cards are centered within their slides  

## Testing

### Test File
Open `test_staff_cards.html` in a browser to see the fixed sizing in action.

The test includes:
- Short names
- Long names with credentials
- Long department names
- Various content lengths

### Visual Verification

All cards should:
1. Have exactly the same height
2. Have exactly the same width
3. Be centered in their slides
4. Show text truncation with ellipsis (...) for overflow
5. Maintain spacing consistency

### Responsive Testing

Test at these breakpoints:
- Mobile: < 576px (1 card per view)
- Tablet: 576-991px (2 cards per view)
- Desktop: 992-1199px (3 cards per view)
- Large Desktop: 1200px+ (4 cards per view)

## Browser Compatibility

The CSS uses:
- Flexbox (widely supported)
- CSS line clamping with `-webkit-` prefix (supported in all modern browsers)
- Fixed heights (universal support)

## Files Modified

1. `static/css/officials_slider.css` - Updated card dimensions and text sizing
2. `test_staff_cards.html` - Created test file for verification

## Usage

The changes are automatically applied to the staff section on the homepage. No template changes were needed.

### In Templates

The existing template structure works perfectly:
```django
<div class="swiper-slide">
    <div class="staff-card">
        <div class="staff-avatar">...</div>
        <h5 class="staff-name">{{ staff.name }}</h5>
        <p class="staff-position">{{ staff.position }}</p>
        <p class="staff-department">{{ staff.department }}</p>
        <div class="staff-contact">...</div>
    </div>
</div>
```

## Maintenance

### Adding New Staff Members

Simply add staff members through the admin or seeder command. The fixed sizing will automatically apply.

### Adjusting Card Height

To change the card height, update these values in `officials_slider.css`:

```css
/* Desktop */
.staff-card {
    height: 380px; /* Change this value */
}

/* Mobile */
@media (max-width: 575px) {
    .staff-card {
        height: 340px; /* Change this value */
    }
}
```

### Adjusting Text Line Limits

To show more/fewer lines, update the `-webkit-line-clamp` value:

```css
.staff-name {
    -webkit-line-clamp: 2; /* Change to 1, 2, 3, etc. */
}
```

## Notes

- Bio field is hidden by default (empty in seeder) but styling is ready if needed
- Contact button automatically pushes to bottom with `margin-top: auto`
- All cards maintain consistent spacing between elements
- Hover effects still work perfectly with fixed sizing

---

**Implementation Date:** March 2, 2026  
**Status:** ✅ Complete and Tested
