# Shaxsiy yordamchi

<!-- impeccable:product-schema 1 -->

## Platform
Web, with an optional native desktop wrapper. Windows, macOS and Linux users run one private instance each.

## Stack
Python, aiohttp, local HTML/CSS/JavaScript, perspective-projected 3D canvas; Hermes execution; optional Telegram and Gemini audio; file-backed knowledge and SQLite scheduling.

## Users
Uzbek-speaking learners installing their own personal assistant from a public source archive or GitHub repository.

## Product Purpose
A personal workspace for conversation, documents, evidence retrieval and editable owner preferences. The browser dashboard opens before account setup. External AI and Telegram capabilities report their actual setup state.

## Operating Context
Local-only authenticated web panel. Profiles, sessions and knowledge live outside source control. One Telegram identity runs on one host. The existing desktop is retained as an optional legacy surface.

## Capabilities and Constraints
No model fine-tuning: relevant sources are retrieved at response time. Speech recognition and synthesis depend on browser support and language voices. No account credentials are shipped. Cloud AI needs the user's own authorized account. Background reminders require a running Telegram service.

## Brand Commitments
Uzbek interface; configurable introduction. User requested a futuristic Jarvis-like 3D control panel. Clear everyday controls surround a single animated 3D nucleus; decorative animation never claims service health.

## Product Principles
- State what is connected and what still needs setup.
- Preserve source evidence and make retrieval inspectable.
- Keep secrets outside source and browser responses.
- Honor reduced motion, keyboard navigation and small screens.

## Integrated onboarding and planning — 0.5.0

The installer prepares its own Hermes installation and dependency home before opening a five-step Uzbek browser wizard. The wizard handles owner profile, OpenAI/Anthropic OAuth, Telegram code/2FA and owner verification, browser/Gemini voice, and a real model-response check before completion. Anthropic OAuth requires Max plus extra credits. No automatic paid-provider fallback.

The home dashboard shows real scheduler jobs and a bounded local Telegram message inbox. The month calendar creates/cancels the existing durable jobs; the service is the sole scheduler writer while running. Inbound important-message rules use configured keywords or mentions; manual sync fetches a bounded unread preview without marking Telegram read. Browser walkthroughs simulate external account logins, never claim live OAuth/Telegram success.
