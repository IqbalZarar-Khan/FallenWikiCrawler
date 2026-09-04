# Frontend & UI Architecture 🎨

This document describes the design system, reactive state machine, layout hierarchy, and real-time streaming engine implemented in the single-page frontend (`index.html`).

---

## 1. UI Layout Hierarchy

The interface uses a centered two-column card structure bounded by a `max-width: 1200px` container.

```mermaid
graph TD
    subgraph PageLayout[".page-layout (Max-Width 1200px, Centered Card)"]
        subgraph MainCol[".main-col (Crawler Control & Feedback)"]
            Header["Title & Theme Switcher"]
            Inputs["Inputs: Wiki URL, Filename, Format (TXT/MD), Sleep Delay"]
            Controls["Buttons: Start, Pause, Resume, Stop"]
            Progress["Progress Bar & Item Counter (e.g. 45 / 300)"]
            Terminal["Color-Coded Live Log Console"]
            DownloadCard["Download Export Action Banner"]
        end

        subgraph SideCol[".side-col (About & Community Sidebar)"]
            Avatar["Author Logo & Bio"]
            Links["Patreon Link"]
        end
    end
```

---

## 2. Client State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle: Page Load
    
    Idle --> Crawling: Click "Start Crawling"
    Crawling --> Paused: Click "Pause"
    Paused --> Crawling: Click "Resume"
    Crawling --> Stopped: Click "Stop"
    Paused --> Stopped: Click "Stop"
    Crawling --> Finished: Completed (100%)

    Stopped --> Idle: Reset / New Job
    Finished --> Idle: Reset / New Job
```
