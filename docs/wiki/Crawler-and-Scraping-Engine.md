# Crawler & Scraping Engine ⚙️

This document details the crawling algorithms, MediaWiki API integration, content parsing, sanitization rules, rate-limiting resilience, and document formatting engine of **FallenWiki Crawler**.

---

## 1. Page Discovery Strategies

FallenWiki Crawler supports two distinct modes of page acquisition:

```mermaid
flowchart TD
    Start([User Initiates Job]) --> ModeCheck{Mode?}
    
    %% Mode 1
    ModeCheck -->|all_pages| M1_Normalize[Normalize Base URL<br/>e.g., https://site.fandom.com]
    M1_Normalize --> M1_Fetch[Query MediaWiki API<br/>list=allpages aplimit=500]
    M1_Fetch --> M1_Pages[Collect Titles]
    M1_Pages --> M1_Cont{Has apcontinue?}
    M1_Cont -->|Yes| M1_Fetch
    M1_Cont -->|No| Dedup[Deduplicate Page Titles]

    %% Mode 2
    ModeCheck -->|links| M2_Source{Source?}
    M2_Source -->|Single URL| M2_URL[Parse URL & Extract Title]
    M2_Source -->|File Upload| M2_File[Read Lines & Filter http URLs]
    M2_URL --> Dedup
    M2_File --> Dedup

    Dedup --> Filter[Namespace & Chapter Regex Filtering]
    Filter --> CrawlLoop[Sequential Fetch & Clean Loop]
```

---

## 2. Namespace & Junk Filtering

Before querying article content, the crawler eliminates non-article pages and chapter stubs:

### Junk Namespaces
Titles starting with any of the following namespaces are discarded:
- `User:`, `User talk:`, `Talk:`
- `Category:`
- `File:`
- `Special:`
- `Blog:`
- `Template:`, `Module:`, `MediaWiki:`
- `Thread:`, `Message Wall:`, `Board:`, `Board Thread:`

### Chapter Noise Elimination
Web novel wikis often contain machine-translated chapter stubs. The crawler ignores titles matching:
- `^chapter[\s\d:.-]+` (e.g. *Chapter 123*)
- `chapter\s*\d+`
- `^\d{3,}` (e.g. *0012*)
- `^\d+-\d+` (e.g. *12-15*)

---

## 3. The 7-Step Content Cleanup Pipeline

```mermaid
flowchart TD
    A["Raw Extracted Text"] --> B["Step 0: Unicode Normalization (NFKC)<br/>Normalize curly quotes, em-dashes, NBSP"]
    B --> C["Step 1: Nav & Sidebar Filter<br/>Remove 'Home', 'Wiki', 'Special pages', etc."]
    C --> D["Step 1b: Chapter Junk Filter<br/>Remove 'Sign in to save', 'Translator:', etc."]
    D --> E["Step 2: Ad Placeholder Removal<br/>Strip 'Advertisement', 'CC-BY-SA', 'Fandom'"]
    E --> F["Step 3: Category Metadata Strip<br/>Remove 'Categories: ...'"]
    F --> G["Step 4: Short Junk Removal<br/>Remove lines with < 3 characters"]
    G --> H["Step 5: Blank Line Collapsing<br/>Collapse 3+ empty lines to 1"]
    H --> I["Step 6: Boilerplate Section Trimming<br/>Strip 'References', 'See also', 'External links'"]
    I --> J{"Step 7: Word Count Check<br/>Word count > 0?"}
    J -->|Yes| K["Append Clean Document to File"]
    J -->|No / Stub| L["Skip & Log as Stub"]
```

---

## 4. Rate Limiting & Resilience Architecture

### Layer 1: Configurable Politeness Delay
The `sleep` parameter (default `1.0s`, configurable `0.5s`–`10.0s`) pauses execution between page requests.

### Layer 2: HTTP 429 Exponential Backoff
When encountering a `429 Too Many Requests` status:
- First retry: Waits $2^0 = 1\text{ second}$
- Second retry: Waits $2^1 = 2\text{ seconds}$
- Third retry: Waits $2^2 = 4\text{ seconds}$

### Layer 3: Redirect Loop Suppression
MediaWiki redirects are resolved automatically via `redirects=true`. If the API reports greater than 3 redirect hops, the page is flagged as a loop and safely skipped.
