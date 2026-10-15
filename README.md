# IX Learning Studio — Universal v1.0

A curated, offline-buildable, static multipage learning website, prepared for publication through GitHub Pages. User interface and learning copy are primarily Thai.

## Lessons included

- `/lessons/gnss-epoch/`: GNSS Epoch Propagation (existing V2, preserved and reused; constant-velocity synthetic Local ENU).
- `/lessons/newtons-cooling/`: Newton's Law of Cooling (new synthetic teaching simulation).
- `/index.html`: searchable learning library, learning protocol, privacy guard.

## Next lesson

1. Ask in ChatGPT: “สอน `<topic>` แบบ IX Learning Studio ...”
2. Use `MASTER_PROMPT_TH.md` and `WORKFLOW_TH.md` to create `lessons/<slug>/index.html`.
3. Run scientific / functional gates and complete a QA report.
4. Add only approved public content to Learning Library. For private data, deliver a local/offline artifact or private workspace instead.

## Publishing through GitHub Pages

The current site bundle has NOT been published. Create a **separate** public GitHub repository called `ix-learning-studio` (not the existing `pyproj` fork). Upload this site's contents to the repository root (not the zip itself), then in GitHub **Settings > Pages > Build and deployment > Source: Deploy from a branch > main / (root)**. See `DEPLOY_TH.md` for step-by-step and restrictions.

GitHub Pages publishes static files and does not generate AI lessons on demand. New lessons require creating/validating files and updating the repository.

## Source/provenance and limitations

- GNSS lesson derives from previous `03_interactive_ipad_v2.html`; original source retained elsewhere.
- Newton's cooling: closed-form classical simplified model with synthetic parameters.
- No account, storage, analytics, cookies, or data collection implemented.
- Tested on local Chromium with touch emulation; not the user's physical iPad.
- See `QA_REPORT.md`, `CHANGELOG.md`, and SHA256SUMS.txt.

## Rollback

No upstream GitHub repo changed. Delete the new site directory to discard the local draft, or restore previous published commit if it is deployed later.
