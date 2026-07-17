# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 4.1.x   | :white_check_mark: |
| 4.0.x   | :white_check_mark: |
| < 4.0   | :x:                |

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Instead, report privately via GitHub's
[**Report a vulnerability**](https://github.com/SpaceSquare640/Multimedia_Downloader/security/advisories/new)
button (Security → Advisories). We'll acknowledge within a few days and keep you
posted on the fix.

## Scope notes

- The **AI Assistant** sends your prompts to [OpenRouter](https://openrouter.ai)
  using an API key **you** provide; the key is stored locally and never sent
  anywhere else. Any file-touching action requires your explicit confirmation.
- The **web version** (`web_app.py`) has **no built-in authentication** — do not
  expose it to an untrusted network without putting your own auth in front of it.
- The bundled `ffmpeg` is a third-party binary (GPLv3); see
  [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
