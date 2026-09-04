# Changelog & Technical Debt 📋

This document tracks resolved architectural issues, bug fixes, and future optimization roadmaps of **FallenWiki Crawler**.

---

## 1. Resolved Issues Audit

| Subsystem | Previous State / Bug | Resolution Implemented | Impact |
|---|---|---|---|
| **Thread Safety** | `job_states` was mutated across threads without synchronization. | Wrapped all mutations and lookups in `threading.Lock()` (`_job_lock`). | Eliminated latent race conditions during simultaneous `/control` calls. |
| **Download Routing** | `download_result` guessed the newest folder by `mtime`. | Introduced `job_folders` dictionary indexed by `job_id`. | Guaranteed multi-user isolation so User A never receives User B's export. |
| **Rate Limiting** | HTTP 429 from MediaWiki failed silently. | Added 3-tier exponential backoff ($1\text{s} \to 2\text{s} \to 4\text{s}$) and SSE alert. | Prevents crawl failure on high-traffic or heavily throttled wikis. |
| **Redirect Loops** | MediaWiki circular redirects caused endless loops. | Added redirect hop counter with threshold `len(redirects) > 3`. | Eliminates infinite looping on corrupted wiki page redirects. |
| **Section Parsing** | Fragile `isupper()` check dropped valid headings. | Replaced with strict MediaWiki section regex `^={2,}\s*.+?\s*={2,}$`. | Accurate stripping of `References`, `See also`, and `External links`. |
| **Character Normalization** | Mixed UTF-8 characters corrupted plain text export. | Integrated `unicodedata.normalize('NFKC', text)`. | Normalizes smart quotes, curly apostrophes, em-dashes, and non-breaking spaces. |
| **Avatar & Route** | Backend served `/avatar.png` while disk had `logo.png`. | Aligned backend endpoint to `/logo.png` and updated image handler. | Resolved broken image rendering in About sidebar. |
| **Page Layout** | Layout was unconstrained, hugging screen edges. | Wrapped in centered container (`max-width: 1200px`) with symmetric padding. | Unified visual aesthetics across monitor aspect ratios. |
