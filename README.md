# Multimedia Downloader Web Preview

An original, multilingual project guide and browser-only mock application for Multimedia Downloader. This branch contains only the static website and its simulated app UI.

## What visitors can explore

- Project overview and confirmed features of the real Multimedia Downloader app.
- English, Traditional Chinese, and Simplified Chinese interface copy.
- Simulated download, format conversion, activity queue, and AI-assisted plan review flows.
- Responsive app preview with sample progress and fictional outputs.
- Self-hosted League Spartan and Figtree variable fonts under the SIL Open Font License 1.1.

## Copyright and licenses

Copyright (c) Kingsley.

- Website code is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE).
- Original website text, translations, and visuals are licensed under [CC BY-NC-SA 4.0](LICENSE-CONTENT.txt).
- Third-party materials are excluded from those project licenses and retain their own terms. The bundled League Spartan and Figtree fonts remain under SIL Open Font License 1.1; see [Third-Party Notices](THIRD_PARTY_NOTICES.md).

<!-- OpenAI-Codex: documented the separate code, content, and third-party licenses. -->

The simulated app does not fetch media, access local files, call the Python engine, make API requests, or convert or download anything. Its URLs, filenames, progress, and activity records are generated examples. Use the real project for actual media workflows.

## Development

Requirements: Node.js 20.19 or newer, or 22.12 or newer, and npm.

```bash
npm ci
npm run dev
```

Create a production build or serve it locally:

```bash
npm run build
npm run preview
```

The build uses the repository project path `/Multimedia_Downloader/` so its static assets work on GitHub Pages. The GitHub Actions workflow builds `dist/` and publishes it through the GitHub Pages deployment environment when `Multimedia_Downloader_Web_Preview` is pushed. Configure the repository's Pages source to **GitHub Actions** before enabling its first deployment.

## Contents

- `src/` — Svelte site and mock app UI.
- `.github/workflows/pages.yml` — static Pages build and deployment.
- `PRODUCT.md` — product truth and preview constraints.
- `THIRD_PARTY_NOTICES.md` — bundled font licenses and notices.

## Project links

- [Multimedia Downloader source repository](https://github.com/SpaceSquare640/Multimedia_Downloader)
- [Releases](https://github.com/SpaceSquare640/Multimedia_Downloader/releases)
- [User manual wiki](https://github.com/SpaceSquare640/Multimedia_Downloader/wiki)
- [Discord community](https://discord.gg/aaUQVJeCgC)
