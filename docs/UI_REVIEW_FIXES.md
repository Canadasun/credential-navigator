# Credential Navigator UI and correctness fixes

Local review date: 25 October 2026. Baseline: a0a9bde. Changes are uncommitted and unpushed for local review at http://localhost:3010/.

| Finding | Resolution | Regression evidence |
|---|---|---|
| B1: future dates and impossible scores accepted | API date/range/finite-value/step validation; matching browser limits; readable API validation messages | EnglishValidationRegressions; ApiValidationRegressions; browser API negative scenarios |
| B2: hidden English exemption overrides visible test | Selecting a test resets exemption and scores/date; inactive exemption never enters the test payload; conflicting API evidence rejected | Model conflict test and nursing UI test |
| B3: old responses overwrite newer ones | Shared revision-owned request hook aborts superseded work and ignores late successes/errors; input changes invalidate pending requests | Delayed response and in-flight upload scenarios |
| B4: leap-day crash | Safe calendar anniversary using the final valid day of the target month | Unit anniversary/expiration boundary and API leap-day tests |
| B5: stale results after edits | Roadmaps and comparisons clear as soon as inputs change; snapshot document/discipline shown with comparison | Edit-after-result and upload scenarios |
| B6: engineering mobile overflow | Constrained/shrinkable upload fields and flex children, bounded controls | All routes at 320, 375, 768 px; score/result states at phone widths |
| B7: phone test misses engineering | Original suite loops all routes; dedicated regression suite runs in CI | frontend/tests/e2e.cjs and regressions.cjs |

Additional review recommendations implemented:

- Current-page navigation via aria-current, professional home-page hierarchy and short start guidance.
- Grouped forms and on-page section links; result/cost links appear when a report exists.
- Pending/ready announcements, keyboard focus to the result heading, clear partial-input guidance.
- Optional browser-only drafts, explicit save opt-in, restoration and deletion, no uploaded-file persistence; graceful storage/corrupt-draft handling.
- Print/save-PDF and JSON downloads; timeline source links; expandable course-match terms and document identity.

Validation completed: production build, TypeScript and git diff whitespace checks pass. All 44 backend tests, all 7 original browser scenarios and all 15 additional browser regression scenarios pass against the rebuilt Docker preview. Automated axe checks report zero violations on the three routes and the tested nursing result. Browser cases include malformed/denied storage, cancelled uploads, JSON export, mobile results and all original findings. A print-preview PDF was generated and the desktop/mobile layouts visually inspected.

Scope limits: Chromium automated/visual checks; no Safari/Firefox or full manual screen-reader certification. Existing regulatory facts and matching thresholds are unchanged. No authentication, deployment or persistence backend was added. The prototype remains advisory. No Git commit or push is part of this change.
