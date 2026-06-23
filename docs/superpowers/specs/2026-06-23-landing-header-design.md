# Landing Page Header Design

## Goal

Create a clean institutional landing-page header whose university name is visually and mathematically centered, with balanced branding and improved responsive presentation.

## Approved Direction

Use a three-column CSS grid with equal-width outer columns. The NORSU seal occupies the left column, the university identity occupies the center column, and the Alumni Affairs logo occupies the right column. Equal outer columns ensure the text remains centered even when the two logo assets have different dimensions.

## Visual Design

- Keep the existing white institutional header and red/blue university wordmark.
- Center the university name and office subtitle as one identity block.
- Use restrained spacing and responsive typography for a polished, formal appearance.
- Add a thin red-and-blue accent along the header edge to connect the institutional colors without competing with the navbar.
- Preserve the existing dark-blue landing navigation and its behavior.
- Retain subtle logo hover feedback while respecting reduced-motion preferences.

## Responsive Behavior

- Desktop: both logos flank a single-line university name with balanced outer columns.
- Tablet: reduce logo size, spacing, and type size while retaining the centered layout.
- Mobile: keep the current behavior that hides the institutional header so the compact landing navigation remains usable.
- Prevent overflow at intermediate widths by allowing the title to wrap cleanly when needed rather than shifting off-center.

## Implementation Scope

- Update `templates/components/university_header.html` only if minor semantic structure changes are needed.
- Update `static/css/university_header.css` for grid balance, typography, spacing, accent treatment, and responsive behavior.
- Adjust landing-page header/navbar offsets only if the redesigned header height changes.
- Do not redesign the navbar or other landing-page sections.

## Accessibility

- Preserve meaningful logo alternative text.
- Preserve the Alumni Affairs external-link label and safe link attributes.
- Maintain sufficient red/blue text contrast on white.
- Preserve high-contrast and reduced-motion accommodations.

## Verification

- Confirm the identity block is centered independently of logo widths.
- Check desktop and tablet breakpoints for wrapping, clipping, and header/navbar overlap.
- Confirm the mobile header remains hidden and page offsets remain correct.
- Run relevant Django template/tests and inspect the rendered landing page when a local server is available.
