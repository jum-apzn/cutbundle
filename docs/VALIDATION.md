# Validation record

Recorded 2026-10-10.

## Executed

- Node syntax checks for browser JavaScript modules: passed.
- Nine Node unit tests: passed. Covers path sanitation, centered aspect-preserving layout, portrait safe margin, alpha bounding boxes, empty masks, edge-connected removal preserving enclosed matching colors, uneven-corner warnings, standard CRC32 vector, ZIP signatures/UTF-8 flags.
- Standalone build: generated successfully using SHA-256 CSP hashes. No CDN or bundled runtime dependencies.
- Optional companion API and real inference checks: see `../companion/validation.md` for actual results and scope.

## Browser scope

A Playwright end-to-end script is supplied in `tests/browser.mjs`. It tests six-photo/twelve-output download, grouping, edit confirmation/cancellation, zero-size selection, originals, deletion, invalid input, responsive overflow, JavaScript errors and outgoing requests.

This script could not run in the authoring environment because Chromium was blocked from creating a socket. Consequently browser screenshots, real browser-generated sample ZIP integrity and cross-browser behavior are not claimed as verified here. Run the documented test on a normal local computer before relying on a batch for production. This limitation does not change the pure-function or companion test results.
