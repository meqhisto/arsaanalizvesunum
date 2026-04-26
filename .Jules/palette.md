## 2024-04-23 - Accessibility Improvements for Icon-only Buttons
**Learning:** Many icon-only buttons (like theme toggles, notification bells, sidebar toggles, and modal close buttons) in the application lacked `aria-label` attributes, making them inaccessible to screen readers.
**Action:** When adding icon-only buttons, always ensure they have an `aria-label` that describes their function to assistive technologies. For `btn-close` buttons in Bootstrap, an `aria-label="Close"` should be standard.
