"""Test that key web pages render without errors."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    ("Home", "/"),
    ("Chat", "/chat"),
    ("Knowledge Explorer", "/knowledge"),
    ("Insights", "/insights"),
    ("Knowledge Search", "/search"),
]

for name, path in pages:
    try:
        r = client.get(path)
        size = len(r.data)
        has_html = b"<html" in r.data.lower() or b"<!doctype" in r.data.lower()
        status = "OK" if r.status_code == 200 and has_html else "WARN"
        if r.status_code >= 400:
            status = "FAIL"
        print(f"  [{status}] {name:25s} {path:20s} -> {r.status_code} ({size:,} bytes, html={has_html})")
        if r.status_code >= 400:
            print(f"         Error preview: {r.data[:200].decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"  [ERR]  {name:25s} {path:20s} -> {e}")

print("\nDone.")