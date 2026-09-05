import os
import shutil
import time
import uuid
import json
import re
import gc
import html
import threading
import unicodedata
from contextlib import asynccontextmanager
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse, quote

from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cleanup leftover scratch folders from previous runs."""
    try:
        for folder in [f for f in os.listdir(BASE_DIR) if f.startswith('fandom_data_') and os.path.isdir(os.path.join(BASE_DIR, f))]:
            shutil.rmtree(os.path.join(BASE_DIR, folder), ignore_errors=True)
    except Exception:
        pass
    yield


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL STATE (thread-safe) ---
_job_lock = threading.Lock()
job_states = {}    # {job_id: state_str}
job_folders = {}   # {job_id: folder_path}
DEFAULT_SLEEP = 1.0


def get_job_state(job_id: str) -> str:
    with _job_lock:
        return job_states.get(job_id, "stopped")


def set_job_state(job_id: str, state: str):
    with _job_lock:
        job_states[job_id] = state


def del_job_state(job_id: str):
    with _job_lock:
        job_states.pop(job_id, None)


def set_job_folder(job_id: str, folder: str):
    with _job_lock:
        job_folders[job_id] = folder


def get_job_folder(job_id: str) -> str | None:
    with _job_lock:
        return job_folders.get(job_id)


def del_job_folder(job_id: str):
    with _job_lock:
        job_folders.pop(job_id, None)


# =====================================================================
# HTML TO MARKDOWN CONVERTER
# =====================================================================

class MediaWikiHTMLToMarkdown(HTMLParser):
    def __init__(self, base_url=""):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.output = []
        self.tag_stack = []
        self.skip_stack = []
        self.list_stack = []
        
        # Table tracking
        self.in_table = False
        self.table_rows = []
        self.current_row = []
        self.current_cell = []
        self.is_header_cell = False
        self.has_th_row = False
        
        # Link tracking
        self.current_href = None
        self.link_text = []

        # Formatting states
        self.in_code = False
        self.in_pre = False
        self.in_blockquote = False
        
        # Discarded non-article elements & classes
        self.skip_tags = {'script', 'style', 'nav', 'noscript', 'aside', 'form', 'button', 'input'}
        self.skip_classes = {
            'mw-editsection', 'navbox', 'toc', 'mw-jump-link', 'reference',
            'fandom-community-header', 'wds-global-navigation', 'page-header__actions',
            'wds-dropdown', 'catlinks', 'printfooter', 'fandom-ad', 'ad-container',
            'portal', 'license-description', 'mw-cite-backlink', 'hatnote', 'dablink'
        }

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        classes = set(attr_dict.get('class', '').split())
        tag_id = attr_dict.get('id', '')

        if (tag in self.skip_tags or 
            bool(classes & self.skip_classes) or 
            tag_id in {'toc', 'mw-navigation', 'siteSub'} or
            'display:none' in attr_dict.get('style', '').replace(' ', '')):
            self.skip_stack.append(tag)
            return

        if self.skip_stack:
            self.skip_stack.append(tag)
            return

        self.tag_stack.append(tag)

        # Headings
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            level = int(tag[1])
            md_level = min(6, level + 1 if level == 1 else level)
            self._ensure_newline(2)
            self.output.append(f"{'#' * md_level} ")

        # Formatting
        elif tag in {'b', 'strong'}:
            self.output.append('**')
        elif tag in {'i', 'em'}:
            self.output.append('*')
        elif tag in {'s', 'strike', 'del'}:
            self.output.append('~~')
        elif tag == 'code' and not self.in_pre:
            self.in_code = True
            self.output.append('`')
        elif tag == 'pre':
            self.in_pre = True
            self._ensure_newline(2)
            self.output.append('```\n')
        elif tag == 'blockquote':
            self.in_blockquote = True
            self._ensure_newline(2)
            self.output.append('> ')
        elif tag == 'hr':
            self._ensure_newline(2)
            self.output.append('---\n\n')

        # Paragraphs & Breaks
        elif tag == 'p':
            self._ensure_newline(2)
        elif tag == 'br':
            if self.in_table:
                self.current_cell.append(' ')
            else:
                self.output.append('\n')

        # Links
        elif tag == 'a':
            href = attr_dict.get('href', '').strip()
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                if href.startswith('/') and self.base_url:
                    href = f"{self.base_url}{href}"
                self.current_href = href
                self.link_text = []

        # Lists
        elif tag == 'ul':
            self.list_stack.append(('ul', 0))
            self._ensure_newline()
        elif tag == 'ol':
            self.list_stack.append(('ol', 0))
            self._ensure_newline()
        elif tag == 'li':
            self._ensure_newline()
            depth = max(0, len(self.list_stack) - 1)
            indent = '  ' * depth
            if self.list_stack:
                list_type, count = self.list_stack[-1]
                if list_type == 'ol':
                    count += 1
                    self.list_stack[-1] = (list_type, count)
                    self.output.append(f"{indent}{count}. ")
                else:
                    self.output.append(f"{indent}- ")
            else:
                self.output.append("- ")

        # Definition lists
        elif tag == 'dt':
            self._ensure_newline(2)
            self.output.append('**')
        elif tag == 'dd':
            self._ensure_newline()
            self.output.append(': ')

        # Tables
        elif tag == 'table':
            self.in_table = True
            self.table_rows = []
            self.has_th_row = False
        elif tag == 'tr' and self.in_table:
            self.current_row = []
        elif tag in {'th', 'td'} and self.in_table:
            self.current_cell = []
            self.is_header_cell = (tag == 'th')
            if tag == 'th':
                self.has_th_row = True

    def handle_endtag(self, tag):
        if self.skip_stack:
            if self.skip_stack[-1] == tag:
                self.skip_stack.pop()
            return

        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        # Headings
        if tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self._ensure_newline(2)

        # Formatting
        elif tag in {'b', 'strong'}:
            self.output.append('**')
        elif tag in {'i', 'em'}:
            self.output.append('*')
        elif tag in {'s', 'strike', 'del'}:
            self.output.append('~~')
        elif tag == 'code' and not self.in_pre:
            self.in_code = False
            self.output.append('`')
        elif tag == 'pre':
            self.in_pre = False
            self._ensure_newline()
            self.output.append('```\n\n')
        elif tag == 'blockquote':
            self.in_blockquote = False
            self._ensure_newline(2)

        # Links
        elif tag == 'a':
            if self.current_href is not None:
                text = ''.join(self.link_text).strip()
                href = self.current_href
                self.current_href = None
                self.link_text = []
                if text:
                    clean_text = text.replace('[', '\\[').replace(']', '\\]')
                    if self.in_table:
                        self.current_cell.append(f"[{clean_text}]({href})")
                    else:
                        self.output.append(f"[{clean_text}]({href})")

        # Lists
        elif tag in {'ul', 'ol'}:
            if self.list_stack:
                self.list_stack.pop()
            self._ensure_newline(2)
        elif tag == 'li':
            self._ensure_newline()

        # Definition lists
        elif tag == 'dt':
            self.output.append('**\n')
        elif tag == 'dd':
            self._ensure_newline()

        # Tables
        elif tag in {'th', 'td'} and self.in_table:
            cell_text = ''.join(self.current_cell).strip()
            cell_text = cell_text.replace('|', '\\|').replace('\n', ' ')
            cell_text = re.sub(r'\s+', ' ', cell_text)
            self.current_row.append(cell_text)
            self.current_cell = []
        elif tag == 'tr' and self.in_table:
            if self.current_row:
                self.table_rows.append(self.current_row)
            self.current_row = []
        elif tag == 'table' and self.in_table:
            self.in_table = False
            self._render_markdown_table()

    def handle_data(self, data):
        if self.skip_stack:
            return

        if self.current_href is not None:
            self.link_text.append(data)
            return

        if self.in_table:
            self.current_cell.append(data)
            return

        # Normal text handling
        if self.in_pre:
            self.output.append(data)
        else:
            clean = data
            if not self.in_code:
                clean = re.sub(r'[ \t]+', ' ', clean)
            self.output.append(clean)

    def _ensure_newline(self, count=1):
        if not self.output:
            return
        while self.output and self.output[-1].isspace() and '\n' not in self.output[-1]:
            self.output.pop()
        if self.output and not self.output[-1].endswith('\n'):
            self.output[-1] = self.output[-1].rstrip(' \t')
        
        newlines = 0
        for chunk in reversed(self.output):
            for ch in reversed(chunk):
                if ch == '\n':
                    newlines += 1
                else:
                    break
            if newlines > 0 or chunk:
                break
        
        needed = count - newlines
        if needed > 0:
            self.output.append('\n' * needed)

    def _render_markdown_table(self):
        if not self.table_rows:
            return

        col_count = max(len(row) for row in self.table_rows)
        if col_count == 0:
            return

        self._ensure_newline(2)
        
        normalized_rows = []
        for row in self.table_rows:
            padded = row + [''] * (col_count - len(row))
            normalized_rows.append(padded)

        header_row = normalized_rows[0]
        self.output.append('| ' + ' | '.join(header_row) + ' |\n')
        self.output.append('| ' + ' | '.join(['---'] * col_count) + ' |\n')

        for row in normalized_rows[1:]:
            self.output.append('| ' + ' | '.join(row) + ' |\n')
            
        self._ensure_newline(2)

    def get_markdown(self):
        text = ''.join(self.output)
        text = html.unescape(text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def html_to_markdown(html_content: str, base_url: str = "") -> str:
    parser = MediaWikiHTMLToMarkdown(base_url=base_url)
    parser.feed(html_content)
    return parser.get_markdown()


# =====================================================================
# CONTENT CLEANUP
# =====================================================================

def clean_content(text: str, fmt: str = "txt") -> str:
    """Multi-step content cleanup pipeline supporting TXT and Markdown.

    1. Remove navigation / sidebar text
    2. Remove advertisement placeholders
    3. Remove category lines
    4. Remove short junk lines (< 3 chars, preserving Markdown tokens)
    5. Collapse 3+ consecutive blank lines → 1
    6. Remove boilerplate sections (References, See also, External links)
    7. (Caller handles stub check — skip empty pages)
    """
    if not text:
        return ""

    # Normalize Unicode (curly quotes, em-dashes, NBSP, etc.)
    text = unicodedata.normalize('NFKC', text)

    lines = text.split('\n')
    cleaned: list[str] = []

    # Step 1 patterns
    nav_labels = {
        'home', 'wiki', 'navigation', 'contents', 'main page',
        'community', 'recent changes', 'random page', 'help',
        'what links here', 'related changes', 'special pages',
        'printable version', 'permanent link', 'page information',
    }
    
    # Extra chapter junk lines
    chapter_junk = {
        'sign in to save', 'edit', 'saint tablet', 'chapter link:', 
        'posted on', 'translator', 'previous chapter', 
        'next chapter', '[source]',
    }

    # Step 2 keywords
    ad_keywords = [
        'advertisement', 'sponsored', 'fandom',
        'community content is available under', 'cc-by-sa',
    ]

    # Step 6 headers
    boilerplate_headers = {'references', 'see also', 'external links', 'gallery', 'notes', 'sources'}
    skip_section = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # --- Step 6: detect boilerplate section headers ---
        if fmt == "md":
            header_match = re.match(r'^#{1,6}\s*(.+?)\s*#*$', stripped)
            wiki_match = re.match(r'^={2,}\s*(.+?)\s*={2,}$', stripped)
            if header_match or wiki_match:
                header_text = (header_match or wiki_match).group(1).strip().lower()
                if header_text in boilerplate_headers:
                    skip_section = True
                    continue
                else:
                    skip_section = False
        else:
            is_header = bool(re.match(r'^={2,}\s*.+?\s*={2,}$', stripped))
            if is_header:
                header_text = stripped.strip('= ').strip().lower()
                if header_text in boilerplate_headers:
                    skip_section = True
                    continue
                else:
                    skip_section = False

        if skip_section:
            continue

        # --- Step 1: nav / sidebar ---
        if lower in nav_labels:
            continue

        # --- Step 1b: chapter junk ---
        if lower in chapter_junk or lower.startswith('translator:') or 'wuxiaworld.com' in lower:
            continue

        # --- Step 2: ad placeholders ---
        if any(kw in lower for kw in ad_keywords):
            continue

        # --- Step 3: category lines ---
        if lower.startswith('categories:') or lower.startswith('category:'):
            continue

        # --- Step 4: short junk ---
        if 0 < len(stripped) < 3:
            if fmt == 'md' and stripped in {'--', '---', '-', '*', '|', '#', '##', '> '}:
                pass
            else:
                continue

        cleaned.append(line)

    # --- Step 5: collapse excessive blank lines ---
    result: list[str] = []
    blanks = 0
    for line in cleaned:
        if line.strip() == '':
            blanks += 1
            if blanks <= 1:
                result.append('')
        else:
            blanks = 0
            result.append(line)

    return '\n'.join(result).strip()


# =====================================================================
# MEDIAWIKI API HELPERS
# =====================================================================

def extract_title_from_url(url: str) -> str:
    """Pull the page title out of a wiki URL."""
    path = urlparse(url).path
    if '/wiki/' in path:
        title = path.split('/wiki/', 1)[-1]
    else:
        title = path.rsplit('/', 1)[-1]
    return unquote(title).replace('_', ' ')


def extract_base_url(url: str) -> str:
    """Return scheme + netloc from a full URL."""
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


# Shared session with proper headers (Fandom blocks bare python-requests UA)
_session = requests.Session()
_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
})


def fetch_all_page_titles(base_url: str):
    """Fetch every main-namespace title via allpages with pagination.

    Returns (titles, rate_limited) where rate_limited is True if any
    429 was encountered so the caller can emit an SSE warning.
    """
    api = f"{base_url.rstrip('/')}/api.php"
    titles: list[str] = []
    rate_limited = False
    params = {
        'action': 'query',
        'list': 'allpages',
        'aplimit': '500',
        'apnamespace': '0',
        'format': 'json',
    }

    while True:
        try:
            r = _session.get(api, params=params, timeout=30)
            if r.status_code == 429:
                rate_limited = True
                wait = 5
                print(f"\033[93m[API] Rate limited (429) on allpages, waiting {wait}s\033[0m")
                time.sleep(wait)
                continue
            if r.status_code != 200:
                break
            data = r.json()
            for p in data.get('query', {}).get('allpages', []):
                titles.append(p['title'])
            cont = data.get('continue')
            if cont and 'apcontinue' in cont:
                params['apcontinue'] = cont['apcontinue']
            else:
                break
        except requests.exceptions.Timeout:
            print(f"\033[93m[API] allpages timeout, retrying...\033[0m")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"\033[91m[API] allpages error: {e}\033[0m")
            break

    return titles, rate_limited


def _html_to_text(html: str) -> str:
    """Strip HTML tags and decode entities to produce plain text."""
    # Remove script, style, nav, noscript blocks entirely
    text = re.sub(r'<(script|style|nav|noscript)[^>]*>.*?</\1>', '', html,
                  flags=re.DOTALL | re.IGNORECASE)
    # Replace <br>, <p>, <div>, <li>, heading tags with newlines
    text = re.sub(r'<(?:br|/p|/div|/li|/tr|/h[1-6])[^>]*>', '\n', text,
                  flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode HTML entities
    text = html.unescape(text)
    # Collapse whitespace within lines
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def fetch_page_content(api_url: str, title: str, fmt: str = "txt", base_url: str = "") -> str | None:
    """Fetch page content via action=parse and return Markdown or Plain Text."""
    params = {
        'action': 'parse',
        'page': title,
        'prop': 'text',
        'redirects': 'true',
        'format': 'json',
    }
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = _session.get(api_url, params=params, timeout=30)
            if r.status_code == 429:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"\033[93m[API] Rate limited (429) for '{title}', retry in {wait}s (attempt {attempt+1}/{max_retries})\033[0m")
                time.sleep(wait)
                continue
            if r.status_code != 200:
                return None
            data = r.json()
            if 'error' in data:
                return None

            # Redirect loop guard: skip if >3 redirect hops
            redirects = data.get('parse', {}).get('redirects', [])
            if len(redirects) > 3:
                print(f"\033[93m[API] Redirect loop detected for '{title}' ({len(redirects)} hops), skipping\033[0m")
                return None

            raw_html = data.get('parse', {}).get('text', {}).get('*', '')
            if not raw_html:
                return None

            if fmt == 'md':
                return html_to_markdown(raw_html, base_url=base_url)
            else:
                return _html_to_text(raw_html)

        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            print(f"\033[93m[API] Timeout for '{title}', retry in {wait}s (attempt {attempt+1}/{max_retries})\033[0m")
            time.sleep(wait)
            continue
        except Exception as e:
            print(f"\033[91m[API] parse error for '{title}': {e}\033[0m")
            return None
    return None  # exhausted retries


# =====================================================================
# OUTPUT FORMATTING
# =====================================================================

def format_page(title: str, source_url: str, content: str, fmt: str) -> str:
    if fmt == 'md':
        return f"# {title}\n\n> Source: {source_url}\n\n{content}\n\n---\n\n"
    return (
        f"\n\n{'=' * 40}\n"
        f"CHAPTER: {title}\n"
        f"SOURCE: {source_url}\n"
        f"{'=' * 40}\n\n"
        f"{content}\n\n"
    )


# =====================================================================
# CRAWLER GENERATOR  (SSE)
# =====================================================================

JUNK_NAMESPACES = [
    "User:", "Talk:", "Category:", "File:", "Special:", "Blog:",
    "User talk:", "Template:", "Module:", "MediaWiki:", "Thread:",
    "Message Wall:", "Board:", "Board Thread:",
]


def crawler_generator(job_id, mode, base_url=None, urls=None,
                       custom_filename=None, fmt="txt", sleep_sec=1.0):
    """Yields SSE `data:` lines with progress, errors, and completion."""
    unique_id = str(uuid.uuid4())[:8]
    output_folder = os.path.join(BASE_DIR, f"fandom_data_{unique_id}")
    os.makedirs(output_folder, exist_ok=True)
    set_job_folder(job_id, output_folder)

    # --- filename ---
    ext = '.md' if fmt == 'md' else '.txt'
    if custom_filename and custom_filename.strip():
        safe = re.sub(r'[\\/*?:"<>|]', '', custom_filename.strip())
        safe = re.sub(r'\.\w+$', '', safe) + ext
        final_name = safe
    else:
        final_name = f"wiki_export{ext}"

    output_path = os.path.join(output_folder, final_name)
    set_job_state(job_id, "running")

    yield f"data: {json.dumps({'type': 'info', 'message': f'Job started ({job_id})'})}\n\n"
    yield f"data: {json.dumps({'type': 'info', 'message': f'Output: {final_name}'})}\n\n"

    try:
        titles_and_urls: list[tuple[str, str]] = []

        if mode == "all_pages":
            # ---- Mode 1: discover via MediaWiki allpages ----
            yield f"data: {json.dumps({'type': 'processing', 'message': f'Fetching all page titles from {base_url} …'})}\n\n"
            all_titles, was_rate_limited = fetch_all_page_titles(base_url)
            if was_rate_limited:
                yield f"data: {json.dumps({'type': 'processing', 'message': '⚠ Rate limited during title fetch — recovered, but crawl may be slower'})}\n\n"
            if not all_titles:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No pages found. Is this a valid MediaWiki site?'})}\n\n"
                return
            for t in all_titles:
                page_url = f"{base_url.rstrip('/')}/wiki/{quote(t.replace(' ', '_'), safe='/:@')}"
                titles_and_urls.append((t, page_url))
        else:
            # ---- Mode 2: user-supplied links ----
            if not urls:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No URLs provided.'})}\n\n"
                return
            for u in urls:
                u = u.strip()
                if not u or not u.startswith('http'):
                    continue
                titles_and_urls.append((extract_title_from_url(u), u))

        # Deduplicate by title
        seen = set()
        deduped = []
        for t, u in titles_and_urls:
            if t not in seen:
                seen.add(t)
                deduped.append((t, u))
        titles_and_urls = deduped

        total = len(titles_and_urls)
        if total == 0:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No valid pages to process.'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'success', 'message': f'Found {total} pages. Starting extraction…'})}\n\n"

        # Determine API base for content fetches
        if mode == "all_pages":
            api_base = f"{base_url.rstrip('/')}/api.php"
        else:
            api_base = f"{extract_base_url(titles_and_urls[0][1])}/api.php"

        # Counters for detailed summary
        written = 0
        skipped_stubs = 0
        skipped_no_content = 0
        skipped_junk = 0

        with open(output_path, 'w', encoding='utf-8') as f:
            # ---- Write Table of Contents ----
            if fmt == 'md':
                f.write('# Table of Contents\n\n')
                for idx, (t, _) in enumerate(titles_and_urls, 1):
                    anchor = t.lower().replace(' ', '-')
                    anchor = re.sub(r'[^\w-]', '', anchor)
                    f.write(f'{idx}. [{t}](#{anchor})\n')
                f.write('\n---\n\n')
            else:
                f.write('TABLE OF CONTENTS\n')
                f.write('=' * 40 + '\n\n')
                for idx, (t, _) in enumerate(titles_and_urls, 1):
                    f.write(f'  {idx}. {t}\n')
                f.write('\n' + '=' * 40 + '\n\n')
            f.flush()

            for i, (title, page_url) in enumerate(titles_and_urls):

                # ---- job control ----
                state = get_job_state(job_id)
                if state == "stopped":
                    summary = f'PROCESS STOPPED — {written} written, {skipped_stubs} stubs skipped, {skipped_no_content} failed'
                    yield f"data: {json.dumps({'type': 'stopped', 'message': summary, 'folder': output_folder})}\n\n"
                    break
                while state == "paused":
                    time.sleep(1)
                    state = get_job_state(job_id)

                # ---- skip junk namespaces & chapters ----
                if any(title.startswith(ns) for ns in JUNK_NAMESPACES):
                    skipped_junk += 1
                    continue
                if re.match(r'^chapter[\s\d:.-]+', title, re.IGNORECASE) or re.search(r'chapter\s*\d+', title, re.IGNORECASE) or re.match(r'^\d{3,}', title) or re.match(r'^\d+-\d+', title):
                    skipped_junk += 1
                    continue

                yield f"data: {json.dumps({'type': 'processing', 'message': f'[{i+1}/{total}] Fetching: {title}'})}\n\n"

                base_page_url = base_url if mode == "all_pages" else extract_base_url(page_url)
                content = fetch_page_content(api_base, title, fmt=fmt, base_url=base_page_url)
                if content:
                    cleaned = clean_content(content, fmt=fmt)

                    # Step 7: skip stub pages
                    word_count = len(cleaned.split())
                    if word_count == 0:
                        skipped_stubs += 1
                        yield f"data: {json.dumps({'type': 'processing', 'message': f'⊘ Skipped stub: {title} ({word_count} words)'})}\n\n"
                        continue

                    f.write(format_page(title, page_url, cleaned, fmt))
                    f.flush()
                    written += 1
                    yield f"data: {json.dumps({'type': 'success', 'message': f'✓ [{i+1}/{total}] {title}'})}\n\n"
                else:
                    skipped_no_content += 1
                    yield f"data: {json.dumps({'type': 'processing', 'message': f'⊘ [{i+1}/{total}] Skipped (no content): {title}'})}\n\n"

                time.sleep(sleep_sec)

            else:
                # for-else: loop finished without break → complete
                summary = f'Done! {written} written, {skipped_stubs} stubs skipped, {skipped_no_content} failed, {skipped_junk} filtered'
                yield f"data: {json.dumps({'type': 'complete', 'message': summary, 'folder': output_folder})}\n\n"

        del_job_state(job_id)

    except Exception as e:
        del_job_state(job_id)
        del_job_folder(job_id)
        yield f"data: {json.dumps({'type': 'error', 'message': f'Error: {str(e)}'})}\n\n"


# =====================================================================
# ROUTES
# =====================================================================


@app.get("/health")
@app.get("/healthz")
def health():
    """Cloud deployment health check endpoint."""
    return {"status": "ok", "app": "FallenWiki Crawler"}


@app.get("/", response_class=HTMLResponse)
async def landing():
    """Serve the Digital Scriptorium marketing and landing page."""
    try:
        landing_path = os.path.join(BASE_DIR, "landing.html")
        index_path = os.path.join(BASE_DIR, "index.html")
        if os.path.exists(landing_path):
            with open(landing_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse("<h1>FallenWiki Crawler</h1><p>Server running.</p>")
    except Exception as e:
        return HTMLResponse(f"<h1>FallenWiki Crawler</h1><p>Error: {str(e)}</p>", status_code=200)


@app.get("/crawler", response_class=HTMLResponse)
@app.get("/app", response_class=HTMLResponse)
async def crawler_app():
    """Serve the interactive crawler application interface."""
    try:
        index_path = os.path.join(BASE_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse("<h1>Crawler Tool</h1><p>index.html not found.</p>")
    except Exception as e:
        return HTMLResponse(f"<h1>Crawler Tool</h1><p>Error: {str(e)}</p>", status_code=200)


@app.get("/logo.png")
async def logo():
    """Serve the logo/avatar image."""
    try:
        logo_path = os.path.join(BASE_DIR, "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return Response(content=f.read(), media_type="image/png")
        return Response(status_code=404)
    except Exception:
        return Response(status_code=404)


@app.post("/control")
def control_job(data: dict = Body(...)):
    """Pause / resume / stop a running crawl job."""
    target_id = data.get("job_id")
    action = data.get("action")

    with _job_lock:
        if target_id not in job_states:
            return JSONResponse({"error": "Job ID not found"}, status_code=404)

    if action == "resume":
        set_job_state(target_id, "running")
    elif action == "pause":
        set_job_state(target_id, "paused")
    elif action == "stop":
        set_job_state(target_id, "stopped")
    return {"status": "success", "new_state": get_job_state(target_id)}


@app.post("/stream")
async def stream_crawl(
    job_id: str = Form(...),
    url: str = Form(None),
    file: UploadFile = File(None),
    filename: str = Form(None),
    format: str = Form("txt"),
    mode: str = Form("links"),
    sleep: float = Form(1.0),
):
    """Start crawling and stream SSE progress."""
    fmt = format if format in ("txt", "md") else "txt"
    crawl_sleep = max(0.5, min(10.0, sleep))

    if mode == "all_pages" and url:
        # Mode 1: All pages from wiki base URL
        base = url.strip().rstrip('/')
        if base.startswith("ttps://"):
            base = "h" + base
        # Normalize: strip /wiki/... or any path — API needs just the domain
        base = extract_base_url(base)
        return StreamingResponse(
            crawler_generator(job_id, "all_pages", base_url=base,
                              custom_filename=filename, fmt=fmt, sleep_sec=crawl_sleep),
            media_type="text/event-stream",
        )

    if file:
        # Mode 2 via file upload: one URL per line
        raw = await file.read()
        lines = raw.decode('utf-8').splitlines()
        url_list = [l.strip() for l in lines if l.strip().startswith('http')]
        return StreamingResponse(
            crawler_generator(job_id, "links", urls=url_list,
                              custom_filename=filename, fmt=fmt, sleep_sec=crawl_sleep),
            media_type="text/event-stream",
        )

    if url:
        # Mode 2 via single URL
        single = url.strip()
        if single.startswith("ttps://"):
            single = "h" + single
        return StreamingResponse(
            crawler_generator(job_id, "links", urls=[single],
                              custom_filename=filename, fmt=fmt, sleep_sec=crawl_sleep),
            media_type="text/event-stream",
        )

    return JSONResponse({"error": "No input provided"}, status_code=400)


@app.get("/download-result/{job_id}")
def download_result(job_id: str):
    """Serve the output file and clean up the folder."""
    folder = get_job_folder(job_id)
    if not folder or not os.path.isdir(folder):
        return JSONResponse({"error": "File not found"}, status_code=404)

    out_files = [f for f in os.listdir(folder) if f.endswith('.txt') or f.endswith('.md')]

    if not out_files:
        shutil.rmtree(folder, ignore_errors=True)
        del_job_folder(job_id)
        return JSONResponse({"error": "File not found"}, status_code=404)

    file_path = os.path.join(folder, out_files[0])

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip():
        shutil.rmtree(folder, ignore_errors=True)
        del_job_folder(job_id)
        return JSONResponse({"error": "File is empty — nothing was scraped"}, status_code=404)

    original_name = out_files[0]
    media = "text/markdown" if original_name.endswith('.md') else "text/plain"

    # Release handles before cleanup (Windows)
    gc.collect()
    time.sleep(0.1)

    try:
        shutil.rmtree(folder)
        print(f"\033[93mCleaned: {folder}\033[0m")
    except Exception:
        time.sleep(0.5)
        shutil.rmtree(folder, ignore_errors=True)

    del_job_folder(job_id)

    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={original_name}"},
    )


# =====================================================================
# STARTUP
# =====================================================================

if __name__ == "__main__":
    HOST = os.environ.get("HOST", "0.0.0.0")
    try:
        PORT = int(os.environ.get("PORT", "8000"))
    except (ValueError, TypeError):
        PORT = 8000

    # Cleanup leftover folders from previous runs
    for folder in [f for f in os.listdir('.') if f.startswith('fandom_data_') and os.path.isdir(f)]:
        try:
            shutil.rmtree(folder)
            print(f"\033[93m[STARTUP] Cleaned: {folder}\033[0m")
        except Exception as e:
            print(f"\033[91m[STARTUP] Could not delete {folder}: {e}\033[0m")

    print("\033[92m" + "=" * 50 + "\033[0m")
    print("\033[92m  FALLENWIKI CRAWLER\033[0m")
    print("\033[92m" + "=" * 50 + "\033[0m")
    print(f"\033[96m  URL: http://{HOST}:{PORT}\033[0m")
    print("\033[92m" + "=" * 50 + "\033[0m\n")

    uvicorn.run(app, host=HOST, port=PORT)
