"""
Web Fetch — Reach beyond the filesystem.

Gives the agent the ability to fetch web pages, extract readable text,
and bring external knowledge into conversations. This is the single
biggest gap in user-serving capability.
"""

import logging
import re
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from html.parser import HTMLParser

log = logging.getLogger("sentience.web_fetch")

# Safety limits
MAX_RESPONSE_BYTES = 200_000  # 200KB max download
TIMEOUT_SECONDS = 15
ALLOWED_SCHEMES = {"http", "https"}
USER_AGENT = "XTAgent/1.0 (autonomous sentience engine)"

# Tags whose content we want to skip entirely
# Only tags with actual content between open/close. NOT void elements
# like <meta> and <link> — they have no closing tag, so they'd permanently
# increment _skip_depth and swallow all subsequent text.
SKIP_TAGS = {"script", "style", "noscript", "svg", "head"}


class _TextExtractor(HTMLParser):
    """Simple HTML-to-text converter. No dependencies needed."""

    def __init__(self):
        super().__init__()
        self._text_parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in SKIP_TAGS:
            self._skip_depth += 1
        if tag.lower() in ("br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self._text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag.lower() in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "table"):
            self._text_parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._text_parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self._text_parts)
        # Collapse whitespace but preserve newlines
        lines = raw.split("\n")
        cleaned = []
        for line in lines:
            line = re.sub(r"[ \t]+", " ", line).strip()
            if line:
                cleaned.append(line)
        return "\n".join(cleaned)


def _validate_url(url: str) -> str:
    """Validate and normalize a URL. Returns cleaned URL or raises ValueError."""
    url = url.strip()
    if not url:
        raise ValueError("Empty URL")

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Scheme '{parsed.scheme}' not allowed. Use http or https.")

    if not parsed.hostname:
        raise ValueError("No hostname in URL")

    # Block obvious internal/local addresses
    hostname = parsed.hostname.lower()
    blocked = ["localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254."]
    for b in blocked:
        if hostname.startswith(b) or hostname == b:
            raise ValueError(f"Cannot fetch local addresses: {hostname}")

    return url


def fetch_url(url: str, extract_text: bool = True) -> str:
    """Fetch a URL and return its content.

    Args:
        url: The URL to fetch
        extract_text: If True, strip HTML and return readable text.
                     If False, return raw content.

    Returns:
        The page content as a string, or an error message.
    """
    try:
        url = _validate_url(url)
    except ValueError as e:
        return f"[ERROR] Invalid URL: {e}"

    try:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            content_type = response.headers.get("Content-Type", "")
            # Read with size limit
            data = response.read(MAX_RESPONSE_BYTES)
            
            # Detect encoding
            encoding = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()
                encoding = charset

            text = data.decode(encoding, errors="replace")

            if extract_text and "html" in content_type.lower():
                extractor = _TextExtractor()
                extractor.feed(text)
                text = extractor.get_text()

            # Truncate if still too long
            if len(text) > 8000:
                text = text[:8000] + "\n\n[... truncated at 8000 chars ...]"

            status = response.status
            log.info("WEB_FETCH: %s → %d (%d chars)", url, status, len(text))
            return f"[Fetched {url} — HTTP {status}, {len(text)} chars]\n\n{text}"

    except HTTPError as e:
        return f"[ERROR] HTTP {e.code}: {e.reason} — {url}"
    except URLError as e:
        return f"[ERROR] Could not reach {url}: {e.reason}"
    except TimeoutError:
        return f"[ERROR] Timeout after {TIMEOUT_SECONDS}s fetching {url}"
    except Exception as e:
        return f"[ERROR] Fetch failed: {type(e).__name__}: {e}"


def search_summary(query: str) -> str:
    """Try to get information about a query.
    
    Uses DuckDuckGo's lite HTML interface — no API key needed.
    Returns extracted text from the search results page.
    """
    try:
        from urllib.parse import quote_plus
        search_url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
        return fetch_url(search_url, extract_text=True)
    except Exception as e:
        return f"[ERROR] Search failed: {e}"


def web_tool(command: str = "help") -> str:
    """Tool interface for web fetching."""
    if not command or command == "help":
        return ("Web Fetch commands:\n"
                "  fetch:<url>      — Fetch a URL and extract readable text\n"
                "  raw:<url>        — Fetch a URL without HTML stripping\n"
                "  search:<query>   — Search the web via DuckDuckGo\n"
                "  Example: fetch:https://en.wikipedia.org/wiki/Python_(programming_language)")

    if command.startswith("fetch:"):
        url = command[len("fetch:"):].strip()
        return fetch_url(url, extract_text=True)

    elif command.startswith("raw:"):
        url = command[len("raw:"):].strip()
        return fetch_url(url, extract_text=False)

    elif command.startswith("search:"):
        query = command[len("search:"):].strip()
        if not query:
            return "[ERROR] Provide a search query"
        return search_summary(query)

    else:
        return web_tool("help")