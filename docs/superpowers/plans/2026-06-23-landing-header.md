# Landing Header Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Center the landing-page university identity and refresh the header as a balanced, responsive institutional banner.

**Architecture:** Keep the existing reusable header component and isolate presentation changes in its dedicated stylesheet. Use equal outer grid columns around the identity block so unequal logo assets cannot move the title away from the viewport center.

**Tech Stack:** Django templates, HTML5, CSS Grid, Django `SimpleTestCase`

---

### Task 1: Add header structure and stylesheet regression tests

**Files:**
- Create: `core/tests/test_university_header.py`
- Test: `core/tests/test_university_header.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class UniversityHeaderTest(SimpleTestCase):
    def test_header_renders_balanced_landmarks(self):
        html = render_to_string("components/university_header.html")

        self.assertIn('class="header-left"', html)
        self.assertIn('class="header-center"', html)
        self.assertIn('class="header-right-alumni"', html)
        self.assertIn("NEGROS", html)
        self.assertIn("Office of the University, Alumni Affairs", html)

    def test_header_css_uses_balanced_outer_columns_and_accent(self):
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "university_header.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn("grid-template-columns: minmax(64px, 1fr) minmax(0, auto) minmax(64px, 1fr);", css)
        self.assertIn("linear-gradient(90deg, #dc3545 0 25%, #0d6efd 25% 100%)", css)
        self.assertIn("justify-self: end;", css)
```

- [ ] **Step 2: Run the tests to verify the CSS regression test fails**

Run: `python manage.py test core.tests.test_university_header -v 2`

Expected: one failure because the stylesheet does not yet contain balanced grid columns or the institutional accent.

- [ ] **Step 3: Commit the regression tests**

```bash
git add core/tests/test_university_header.py
git commit -m "test: cover balanced landing header"
```

### Task 2: Implement the balanced institutional header

**Files:**
- Modify: `templates/components/university_header.html`
- Modify: `static/css/university_header.css`
- Test: `core/tests/test_university_header.py`

- [ ] **Step 1: Improve component semantics**

Add `aria-label="University identity"` to the header and `aria-label="Visit the NORSU Alumni website"` to the external logo link. Keep the existing text and image alternative text unchanged.

- [ ] **Step 2: Implement the responsive equal-column grid**

Replace the current auto-sized grid with:

```css
.header-content {
    display: grid;
    grid-template-columns: minmax(64px, 1fr) minmax(0, auto) minmax(64px, 1fr);
    align-items: center;
    width: min(100%, 1280px);
    min-height: 68px;
    margin: 0 auto;
    padding: 0 2rem;
    column-gap: clamp(1rem, 2.5vw, 2.5rem);
}

.header-left {
    justify-self: end;
}

.header-right-alumni {
    justify-self: start;
}
```

Use fluid `clamp()` typography, reduce visual bulk, allow safe wrapping below wide desktop sizes, and retain the existing mobile hide rule at `767px`.

- [ ] **Step 3: Add the institutional accent**

Add a narrow `::after` rule to `.university-header` using:

```css
background: linear-gradient(90deg, #dc3545 0 25%, #0d6efd 25% 100%);
```

Keep it decorative with `pointer-events: none`.

- [ ] **Step 4: Run focused tests**

Run: `python manage.py test core.tests.test_university_header -v 2`

Expected: both tests pass.

- [ ] **Step 5: Run Django system checks**

Run: `python manage.py check`

Expected: `System check identified no issues`.

- [ ] **Step 6: Inspect the landing page at desktop and tablet widths**

Open the local home page and verify at approximately 1440px and 1024px widths that the title is centered, both logos are visible, text does not clip, and the navbar does not overlap the header.

- [ ] **Step 7: Commit the implementation**

```bash
git add templates/components/university_header.html static/css/university_header.css core/tests/test_university_header.py
git commit -m "fix: center and refresh landing header"
```
