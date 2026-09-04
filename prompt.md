# FallenWiki Crawler — Landing Page PRD
**Product Requirements Document · Single-Page Marketing Site**

---

## 1. Project Brief

### 1.1 Product Summary
**FallenWiki Crawler** (also known as *Scrapper*) is a FastAPI-powered tool that extracts, sanitizes, and exports entire MediaWiki / Fandom wikis into clean Markdown or plain-text documents — purpose-built for LLM fine-tuning, RAG pipelines, offline archival, and Xianxia / web novel research.

### 1.2 Audience
- Web novel translators and fan community archivists
- AI/ML engineers building RAG pipelines from fan-wiki corpora
- Developers and technical readers comfortable with CLI tools and Python
- Readers and community members of Fallen_Archangel_'s Patreon and fallenarchangel.site

### 1.3 Page's Single Job
Convert a cold visitor into someone who **downloads, stars, or follows** the project — by communicating what the tool does, how it works, and that it comes from a trusted creator in the web-novel translation community.

---

## 2. Visual Identity & Design System

### 2.1 Aesthetic Direction
**"Digital Scriptorium"** — the aesthetic tension between ancient manuscript culture (Xianxia cultivation lore, ink-brushed scrolls) and modern terminal tooling. The page should feel like a hacker's grimoire: dark parchment, glowing green type, clean monospace, with ink-stroke accents that reference the source material's East Asian literary heritage. It is technical without being sterile, and ornate without being noisy.

This is a deliberate aesthetic risk: most developer tool landing pages use either pure brutalist monospace or gradient-card SaaS styling. This page fuses cultivation-novel visual language with terminal aesthetics, which is specific to the tool's actual cultural context.

### 2.2 Color Palette

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#0D0F0C` | Page background — near-black with a faint green undertone |
| `--scroll` | `#121A10` | Card / section background — dark forest |
| `--jade` | `#4AF59A` | Primary accent — terminal green, cultivation jade |
| `--jade-dim` | `#1F6640` | Secondary jade, borders, muted glows |
| `--parchment` | `#D4C9A8` | Body text — aged paper tone, easy on dark background |
| `--ash` | `#6B7A6A` | Muted text, labels, captions |
| `--vermillion` | `#E84545` | Error / stop states, sparingly used for drama |
| `--gold` | `#C8A96E` | Highlight, brushstroke accents, chapter labels |

### 2.3 Typography

| Role | Typeface | Notes |
|---|---|---|
| **Display / Hero** | `Cinzel` (Google Fonts) | Roman-cut letterforms; evokes ancient text carved in stone. Used only at H1/H2 scale. |
| **Body** | `Inter` | Clean, highly legible at small sizes. Used for all body copy and UI labels. |
| **Code / Terminal** | `JetBrains Mono` | Monospace for all code blocks, SSE payloads, CLI commands. |

**Type Scale:**
- Hero headline: `clamp(2.8rem, 6vw, 5.5rem)`, `Cinzel`, weight 700
- Section heading: `clamp(1.4rem, 3vw, 2.2rem)`, `Cinzel`, weight 600
- Body: `1rem / 1.7`, `Inter`, weight 400
- Caption / label: `0.8rem`, `Inter`, weight 500, letter-spacing `0.08em`, uppercase
- Code: `0.875rem`, `JetBrains Mono`

### 2.4 Signature Element
A **live-animated terminal log panel** in the hero section that auto-plays a simulated crawl session — SSE events scroll past in real time (looping), showing `processing`, `success`, and `complete` events with color-coded type, a progress counter incrementing, and a jade glow pulsing on the active line. This is the single thing a visitor will remember: they *see the tool working* before reading a word of copy.

### 2.5 Motion Principles
- Terminal log: smooth `translateY` scroll, new lines fade in at `200ms`
- Section reveals: `IntersectionObserver` fade+slide-up, `400ms ease-out`, staggered for card grids
- Hover on feature cards: subtle `box-shadow` bloom in jade, `transform: translateY(-3px)`
- Progress bar in hero terminal: CSS animated fill, loops with the log
- Respect `prefers-reduced-motion`: all transitions collapse to instant

---

## 3. Page Architecture & Section Specifications

### 3.1 Layout System
- Max content width: `1200px`, centered
- Base grid: 12-column CSS Grid
- Mobile breakpoint: `768px` — all multi-column layouts collapse to single column
- Section padding: `80px 24px` desktop, `48px 16px` mobile
- No external CSS frameworks — pure CSS custom properties + Grid/Flex

---

### Section 01 — Navigation Bar (Sticky)

**Layout:** Full-width sticky header, `60px` tall, blurs background on scroll.

**Content:**
- Left: `logo.png` avatar (32px circle) + wordmark **"FallenWiki Crawler"** in `Cinzel`
- Right nav links: `Features`, `How It Works`, `Deploy`, `GitHub` (icon + text)
- CTA button: `[ Download ]` — jade border, transparent fill, jade text. On hover: fills jade, text flips to ink.

**Behavior:** Transparent at top of page. On scroll >80px: `background: rgba(13,15,12,0.85)`, `backdrop-filter: blur(12px)`, `border-bottom: 1px solid var(--jade-dim)`.

---

### Section 02 — Hero

**Layout:** Full-viewport-height (`100svh`), two-column split at desktop. Left: copy stack. Right: animated terminal panel.

**Left Column (Copy):**
```
EYEBROW (label style, gold):
  ⬡  FANDOM WIKI EXTRACTION ENGINE

H1 (Cinzel, hero scale):
  Scrape the Wiki.
  Build the Corpus.

BODY (Inter, parchment, 1.15rem):
  FallenWiki Crawler pulls every article from any MediaWiki or
  Fandom wiki and exports it as clean Markdown or plain text —
  ready for LLM training, RAG pipelines, and offline archives.

CTA ROW:
  [ Start Crawling → ]   (filled jade button, ink text)
  [ View on GitHub ]     (ghost button, jade border)

MICRO-CAPTION (ash, small):
  pip install fastapi uvicorn requests  ·  Python 3.10+
```

**Right Column — Animated Terminal Panel:**
```
┌─────────────────────────────────────────────────────────┐
│  ◉ FallenWiki Crawler  ·  job_id: a3f9b2               │
│─────────────────────────────────────────────────────────│
│  [INFO]       Starting crawl: cultivation-wiki.fandom   │
│  [INFO]       Mode: all_pages  ·  Format: Markdown      │
│  [PROCESSING] Fetching page index... 500 titles found   │
│  [SUCCESS]    ✓ [001/312]  Qi Condensation Realm        │
│  [SUCCESS]    ✓ [002/312]  Five Elements Cultivation    │
│  [SUCCESS]    ✓ [003/312]  Nascent Soul Stage           │
│  [PROCESSING] ✓ [004/312]  Divine Sense...              │
│─────────────────────────────────────────────────────────│
│  ████████████░░░░░░░░░░░░  47 / 312  pages              │
└─────────────────────────────────────────────────────────┘
```
- Terminal styled with `JetBrains Mono`, dark scroll background, jade text for `[SUCCESS]`, gold for `[INFO]`, parchment for `[PROCESSING]`
- New log lines animate in from bottom; panel auto-scrolls
- Progress bar fills in jade with a soft `box-shadow` glow
- Counter increments in real time (JS `setInterval`)
- Loops back to start after reaching 100%

---

### Section 03 — Key Capabilities (Feature Grid)

**Eyebrow:** `WHAT IT DOES`
**Heading:** `Built for the Whole Pipeline`

**Layout:** 3-column card grid at desktop, 2-col at tablet, 1-col at mobile.

**6 Feature Cards** (icon + title + body):

| Icon | Title | Body |
|---|---|---|
| `⚡` | **Dual Crawl Modes** | Discover every article automatically via `allpages` API, or supply a custom URL list — one URL per line, or uploaded as a `.txt` file. |
| `🧹` | **7-Step Sanitization** | Strips ads, nav boilerplate, translator comments, chapter stubs, short junk lines, and collapses whitespace — preserving only clean article content. |
| `📡` | **Real-Time SSE Streaming** | Pause, resume, or stop any crawl mid-flight. A live terminal console streams color-coded progress events from server to browser over SSE. |
| `📑` | **Auto Table of Contents** | Every export opens with a linked TOC — clean Markdown anchors for `.md` exports, structured headers for `.txt` — so the corpus is immediately navigable. |
| `🛡️` | **Rate Limit Resilience** | Built-in 3-tier exponential backoff on HTTP 429s, configurable politeness delay (0.5s–10s), and redirect-loop suppression protect every long crawl. |
| `🪟` | **Safe on Windows & Linux** | Explicit file-handle management, `gc.collect()` before cleanup, and startup orphan purging ensure zero leftover scratch directories on any OS. |

**Card Design:** `background: var(--scroll)`, `border: 1px solid var(--jade-dim)`, `border-radius: 8px`, `padding: 28px`. Icon in jade. Title in `Cinzel` small heading. Body in `Inter` parchment. Hover: jade border brightens, card lifts `3px`.

---

### Section 04 — How It Works (Process Flow)

**Eyebrow:** `HOW IT WORKS`
**Heading:** `From Wiki URL to Clean Corpus`

**Layout:** Horizontal step flow at desktop (connected by a dashed jade line), vertical stack at mobile.

**4 Steps:**

```
  [ 1 ]──────────────[ 2 ]──────────────[ 3 ]──────────────[ 4 ]
  Configure            Discover            Extract             Download
  ─────────            ────────            ───────             ────────
  Enter a wiki         Crawler queries     7-step pipeline     Click Download.
  URL or upload        MediaWiki API,      cleans each page.   Server streams
  a URL list.          collects all        Progress streams     the file and
  Choose format        article titles      live to your         wipes the temp
  and sleep delay.     with pagination.    browser.             folder.
```

Each step has: a circled number in jade, a title in `Cinzel`, and 2-sentence body copy in `Inter`.

The dashed connector line between steps is a `border-top: 2px dashed var(--jade-dim)` pseudo-element, hidden on mobile.

---

### Section 05 — Technical Snapshot (Spec Block)

**Eyebrow:** `UNDER THE HOOD`
**Heading:** `Designed for Reliability`

**Layout:** Two-column at desktop. Left: prose + stat pills. Right: code block.

**Left — Stat Pills (3 across):**
```
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │  3-Tier      │  │  7-Step      │  │  SSE-Native  │
  │  Backoff     │  │  Sanitizer   │  │  Streaming   │
  └──────────────┘  └──────────────┘  └──────────────┘
```
Pills: `border: 1px solid var(--jade-dim)`, jade label, parchment description text beneath.

**Right — Code Block (SSE payload example):**
```json
// Live SSE event from /stream
{
  "type": "success",
  "message": "✓ [042/312]  Martial Soul Awakening"
}

// Job control signal to /control
{
  "job_id": "a3f9b2c1",
  "action": "pause"
}
```
Styled with `JetBrains Mono`, `background: #0A0F09`, jade syntax highlights for keys, gold for string values, ash for comments.

---

### Section 06 — Deploy in 60 Seconds

**Eyebrow:** `QUICKSTART`
**Heading:** `Running in Under a Minute`

**Layout:** Centered single-column, max-width `720px`.

**Content:**

Three numbered code steps, each in its own terminal block:

```bash
# 1 — Install dependencies
pip install fastapi uvicorn requests
```
```bash
# 2 — Launch the server
python app.py
```
```
# 3 — Open in browser
http://localhost:8000
```

Below the steps, an **Nginx callout card** (collapsible `<details>` element):
```
▶  Hosting behind Nginx? (click to expand)
   proxy_buffering off;
   proxy_read_timeout 86400s;
   ...
```
Callout styled with `border-left: 3px solid var(--gold)`, gold eyebrow, parchment body.

---

### Section 07 — About / Creator (Sidebar-style Section)

**Layout:** Two-column card at desktop — left is creator bio, right is community links.

**Left — Creator Card:**
- `logo.png` avatar, circular, `72px`, jade ring border
- Name: **Fallen_Archangel_** in `Cinzel`
- Bio copy: "Translator, archivist, and builder. FallenWiki Crawler was built to power the research and archival work behind my Xianxia translation projects. If it's useful to you too — run it, fork it, and contribute."
- Link to `fallenarchangel.site`

**Right — Community Card:**
- Patreon link with Patreon icon, styled in gold
- GitHub link
- "Star the repo" micro-CTA

---

### Section 08 — Footer

**Layout:** Full-width, `border-top: 1px solid var(--jade-dim)`.

**Content:**
- Left: `© Fallen_Archangel_ · FallenWiki Crawler`
- Center: nav links (Features · How It Works · Deploy · GitHub)
- Right: `Built with FastAPI · Uvicorn · Python`

All in `ash` color, `0.85rem`.

---

## 4. Copy Guidelines

- **Voice:** Direct, technically confident, no hype. Assumes the reader can read code. Describes what happens, not how great it is.
- **Avoid:** "powerful", "seamless", "revolutionize", "next-generation", "blazing fast"
- **Use instead:** Concrete verbs — extracts, sanitizes, streams, exports, deletes, retries
- **Xianxia flavor:** The simulated terminal content uses cultivation terminology (Nascent Soul, Qi Condensation, Divine Sense) as realistic wiki page titles — this is the signature cultural detail that makes the demo feel authentic rather than generic.
- **Error states and edge cases** mentioned in copy should reflect actual tool behavior (e.g., redirect loop suppression, Windows file handle management) — this builds credibility with technical readers.

---

## 5. Interaction & Behavior Specifications

### 5.1 Animated Terminal (Hero)
```javascript
// Pseudo-logic for the looping terminal animation
const events = [
  { type: 'info',       text: 'Starting crawl: cultivation-wiki.fandom.com' },
  { type: 'info',       text: 'Mode: all_pages  ·  Format: Markdown' },
  { type: 'processing', text: 'Querying allpages API... 312 titles found' },
  { type: 'success',    text: '✓ [001/312]  Qi Condensation Realm' },
  // ... more entries
  { type: 'complete',   text: '✓ Done! 312 pages exported. Download ready.' },
];
// Append one line every 600ms, scroll panel, update progress bar counter
// After complete event: wait 2s, reset and loop
```

### 5.2 Scroll-Triggered Reveals
- Use `IntersectionObserver` with `threshold: 0.15`
- Elements start: `opacity: 0; transform: translateY(20px)`
- On intersect: transition to `opacity: 1; transform: translateY(0)` over `400ms ease-out`
- Stagger card grids by `50ms` per card using `animation-delay`

### 5.3 Sticky Nav Behavior
- JS `scroll` listener adds class `.scrolled` at `80px`
- `.scrolled` applies backdrop blur and border via CSS

### 5.4 Nginx Callout Expand
- Native HTML `<details>/<summary>` element
- Custom CSS: triangle icon rotates on open, smooth `max-height` transition

---

## 6. Performance & Accessibility Requirements

| Requirement | Target |
|---|---|
| Lighthouse Performance | ≥ 90 |
| First Contentful Paint | < 1.5s |
| No external JS runtime deps | ✓ (Google Fonts + JetBrains Mono via `<link>` only) |
| Keyboard navigable | ✓ All interactive elements have visible `:focus-visible` |
| `prefers-reduced-motion` | ✓ All animations collapse to `transition: none` |
| `alt` text on all images | ✓ |
| Color contrast (WCAG AA) | ✓ — jade on ink, parchment on scroll both pass |
| Mobile responsive | ✓ Breakpoints at 768px and 480px |
| Single HTML file delivery | Preferred — inline CSS + JS in one `index.html` |

---

## 7. Deliverable Specification

**Format:** Single self-contained `index.html` file.
- All CSS in `<style>` tag in `<head>`
- All JS in `<script>` tag before `</body>`
- Fonts loaded via Google Fonts `<link>` (Cinzel, Inter, JetBrains Mono)
- `logo.png` referenced as `./logo.png` (served by FastAPI alongside this file, or swapped for a base64 inline)
- No build step, no bundler, no npm — drop-in deployment

**Sections in order:**
1. `<nav>` — Sticky navigation
2. `<section id="hero">` — Hero with terminal
3. `<section id="features">` — Feature card grid
4. `<section id="how-it-works">` — Process steps
5. `<section id="technical">` — Spec block + code
6. `<section id="quickstart">` — Deploy steps
7. `<section id="about">` — Creator + community
8. `<footer>` — Footer

---

## 8. Out of Scope

- User authentication or account system
- Actual live crawl demo embedded in the landing page (the terminal is simulated)
- Blog or changelog page
- Localization / i18n
- Analytics integration (can be added later via script tag)
