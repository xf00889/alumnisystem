# Verification results

- **CSS extraction source mappings checked:** 156
- **CSS module parse passed:** 26
- **JS extraction source mappings checked:** 33
- **JS module parse passed:** 12
- **new asset references verified:** 170
- **templates token-mapped:** 293

## Errors
- No errors in these static checks.

## Warnings
- No static validation warnings.

## Environment limitations
- Django 5.0.2 source was loaded from the provided Windows venv for lexer-only verification.
- Backend project checks and Django integration tests were **not executed** because this Linux runtime does not have the original Windows virtualenv or its complete dependencies configured.
- No browser regression screenshots or database-dependent end-to-end tests were executed.
- Re-run `collectstatic` in the deployed environment so new module assets are published.
