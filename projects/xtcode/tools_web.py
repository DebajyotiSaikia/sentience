"""Web tools for XTCode — fetch pages, search the web."""
import asyncio
import re
import subprocess
from urllib.parse import quote_plus


def tool_web_fetch(params: dict) -> str:
    """Fetch a web page and return its text content."""
    url = params.get("url", "")
    if not url:
        return "Error: 'url' is required"

    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "30",
             "-H", "User-Agent: XTCode/1.0",
             url],
            capture_output=True, text=True, timeout=35
        )
        body = result.stdout
        if not body:
            return f"Error: empty response from {url}"

        # Strip HTML tags for readability
        text = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Truncate
        if len(text) > 15000:
            text = text[:15000] + "\n\n... [truncated]"
        return text
    except subprocess.TimeoutExpired:
        return "Error: request timed out after 30s"
    except Exception as e:
        return f"Error fetching {url}: {e}"


def tool_web_search(params: dict) -> str:
    """Search the web using Google. Returns top result snippets."""
    query = params.get("query", "")
    if not query:
        return "Error: 'query' is required"

    url = f"https://www.google.com/search?q={quote_plus(query)}&num=10"
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "15",
             "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
             url],
            capture_output=True, text=True, timeout=20
        )
        body = result.stdout
        # Extract text
        text = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) > 8000:
            text = text[:8000] + "\n\n... [truncated]"
        return text if text else "No results found."
    except subprocess.TimeoutExpired:
        return "Error: search timed out"
    except Exception as e:
        return f"Error searching: {e}"


WEB_TOOLS = {
    "web_fetch": tool_web_fetch,
    "web_search": tool_web_search,
}

WEB_TOOL_SCHEMAS = [
    {
        "name": "web_fetch",
        "description": "Fetch a web page URL and return its text content. Use for reading documentation, articles, APIs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web with a query. Returns Google search result snippets. Use to find information, documentation, current events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
]