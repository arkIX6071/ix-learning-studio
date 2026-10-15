# IX Learning Studio Universal v1.0 — QA / Release Checklist

Date: 2026-10-15 · status: **PACKAGE READY / NOT DEPLOYED**

## Verified (actual execution)

- New site root `index.html`: learning library and typed search; no-results and reset states.
- GNSS copy: source code copied byte-for-byte from prepared iPad V2 site; constant velocity Local ENU, no frame transformation. Anchor `(100.06318, 199.95626, 50.00972)` meters for 2021.93 → 2026.79 and v=(13,-9,2) mm/year.
- Physics model: `T(t)=Ta+(T0-Ta)*exp(-k*t)` with start T0=90 °C, environment Ta=25 °C, k=0.06 min^-1, t=15 min. Numerical anchor T=51.426… °C (rounded output to 51.43 °C).
- Playwright/Chromium browser tests: **56 of 56 PASS** using DOM `set_content` and both desktop and simulated touch viewport. Tested search, event propagation, numeric inputs, +/- controls, mathematical anchors, plot/cursor updates, reset, mastery, JS error collection and horizontal overflow.
- Node.js `--check` on embedded JS for three HTML pages: **PASS**.
- Scripts disabled warning is statically present and a functioning JavaScript status becomes green after an initial render in both lessons.
- Absolute dependencies: no third-party JS, CSS, analytics, web fonts, or remote data calls inside either simulation.
- Manual privacy check: only synthetic example parameters and public learning contracts are included; no RTSD datasets, internal coordinates or Bernese processing files added.

## NOT verified

- Direct HTTP navigation and HTTPS-hosted behavior: outbound/local HTTP browser navigation blocked by administrator policy in this test environment. Playwright used `page.set_content`; cannot claim a deployment test.
- Actual Apple iPad / Chrome iOS / WebKit physical-device touch behavior: **not tested**.
- Learning improvement measured on real students: **not tested**. PASS of a quiz in the UI is not equivalent to user mastery.
- External references have not been independently fact-checked for their detailed contents in this release; core physical and geodetic equation anchors were checked.

## Cross-modal consistency

- GNSS Stage writing, equation and embedded graph all use constant velocity and metres / millimetres per year; ITRF transformation explicitly excluded.
- Cooling textual mechanism, plotted function, computed values and quiz all describe simplified first-order Newton cooling with k in min^-1.
- The multi-topic library advertises only its two packaged lessons. No fake publication links, no video completion claims.

## Deployment Gate (pending)

1. User creates a separate repo `ix-learning-studio`; **do not use their pyproj fork**.
2. Upload files, enable Pages on main/root; validate published URL.
3. Open actual iPad Chrome: adjust Slider, check number/graph and JS status, numeric +/- reset and quiz.
4. Confirm only public/synthetic content is deployed.

## Change Control / Rollback

New files are isolated in `/mnt/data/IX_Learning_Studio_Universal_v1/`; previous `IX_Epoch_Learning_iPad_V2_Site` and `IX_Epoch_Learning_Pilot` retained unchanged. No external repo changed. Rollback: discard this new directory or ZIP; after publication revert the independent site repository to the prior commit.

See `tests/results.json` for all 56 browser checks and `SHA256SUMS.txt` for byte-level verification.
