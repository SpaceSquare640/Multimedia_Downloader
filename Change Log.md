# Change Log

## 2026-10-16

- Created an independent Svelte 5 and Vite project for the `Multimedia_Downloader_Web_Preview` branch.
- Added an English, Traditional Chinese, and Simplified Chinese project site with an interactive, browser-only mock of download, conversion, queue, and AI plan review workflows.
- Added prominent GitHub repository and Discord community links in all three site locales.
- Added local font packages for the selected League Spartan and Figtree type system; both font families use SIL Open Font License 1.1.
- Added a GitHub Actions workflow that builds the static site and deploys the artifact to GitHub Pages when this branch is pushed.
- Documented local development and the boundary between the mock UI and the real Multimedia Downloader application.
- Validation: `npm install` completed with 0 reported vulnerabilities; `npm run build` completed successfully. Taste Skill static lint reports 0 FAIL and 9 WARN for outlined controls in the simulated app.
- Status: initial site-only commit `da66c09` was pushed to `Multimedia_Downloader_Web_Preview` after replacing its previous source-code history; `Source_Code` was not changed.
- Risk: GitHub Pages deployment status has not been verified; the repository Pages source may still need to be set to **GitHub Actions**.
