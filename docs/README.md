# FallenWiki Crawler Documentation Portal 📚

Welcome to the documentation portal for **FallenWiki Crawler**.

---

## ⚡ Direct Links
- 🌐 **[Project Homepage (README.md)](file:///README.md)**
- 🚀 **[Run the Web Tool (http://localhost:8000)](http://localhost:8000)**
- 📖 **[Main Wiki Index (docs/wiki/Home.md)](file:///docs/wiki/Home.md)**

---

## 📑 Wiki Chapters & Technical Manuals

All specialized technical documents with detailed Mermaid diagrams and code references are located in [`docs/wiki/`](file:///docs/wiki/Home.md):

1. 🏛️ **[01 - Architecture & System Design](file:///docs/wiki/Architecture-and-System-Design.md)** — Thread-safe concurrency model, job state machine, SSE streaming mechanics, and filesystem lifecycle.
2. 🔌 **[02 - API Reference](file:///docs/wiki/API-Reference.md)** — Comprehensive specification for all endpoints (`/stream`, `/control`, `/download-result`), SSE payload schemas, and curl examples.
3. ⚙️ **[03 - Crawler & Scraping Engine](file:///docs/wiki/Crawler-and-Scraping-Engine.md)** — MediaWiki Action API interaction, 7-step content sanitization pipeline, and HTTP 429 exponential backoff.
4. 🎨 **[04 - Frontend & UI Architecture](file:///docs/wiki/Frontend-and-UI.md)** — Single-page application design tokens, light/dark theme system, client state machine, and real-time SSE stream reader.
5. 🚀 **[05 - Deployment & Operations](file:///docs/wiki/Deployment-and-Operations.md)** — System requirements, installation, Nginx reverse proxy buffering rules, systemd daemon setup, and troubleshooting.
6. 📋 **[06 - Changelog & Technical Debt](file:///docs/wiki/Changelog-and-Technical-Debt.md)** — Evolution history, audit of resolved race conditions and bugs, and future async performance roadmap.
