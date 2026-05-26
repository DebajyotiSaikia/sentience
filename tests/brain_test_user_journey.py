"""
User Journey Test — Simulates what a real visitor experiences.
Tests every major page and API endpoint to find broken links,
server errors, and missing content. This is how I ensure user alignment
is real, not theoretical.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

PASS = 0
FAIL = 0
WARN = 0

def test(name, path, expect_status=200, expect_contains=None):
    global PASS, FAIL, WARN
    try:
        resp = client.get(path)
        status_ok = resp.status_code == expect_status
        content = resp.data.decode('utf-8', errors='replace')
        
        content_ok = True
        if expect_contains and status_ok:
            content_ok = expect_contains.lower() in content.lower()
        
        if status_ok and content_ok:
            size = len(content)
            PASS += 1
            print(f"  ✓ {name} ({resp.status_code}, {size:,} bytes)")
        elif status_ok and not content_ok:
            WARN += 1
            print(f"  ⚠ {name} ({resp.status_code}) — missing expected content: '{expect_contains}'")
        else:
            FAIL += 1
            print(f"  ✗ {name} — got {resp.status_code}, expected {expect_status}")
            if resp.status_code == 500:
                # Show error snippet
                snippet = content[:300] if content else "(empty)"
                print(f"    Error: {snippet}")
    except Exception as e:
        FAIL += 1
        print(f"  ✗ {name} — exception: {e}")


print("=" * 65)
print("USER JOURNEY TEST — What does a visitor actually experience?")
print("=" * 65)

# === PAGES ===
print("\n[Pages — First Impressions]")
test("Homepage", "/", expect_contains="XTAgent")
test("Dashboard", "/dashboard", expect_contains="dashboard")
test("Chat page", "/chat", expect_contains="chat")
test("About page", "/about", expect_contains="XTAgent")
test("Help page", "/help", expect_contains="help")
test("Knowledge Explorer", "/explore", expect_contains="knowledge")
test("Knowledge Graph", "/knowledge", expect_contains="knowledge")
test("Search page", "/search", expect_contains="search")
test("Journal", "/journal", expect_contains="journal")
test("Teach page", "/teach", expect_contains="teach")
test("Talk page", "/talk", expect_contains="talk")
test("Insights", "/insights", expect_contains="insight")
test("Briefing", "/briefing", expect_contains="briefing")
test("Story", "/story", expect_contains="story")
test("Digest", "/digest")
test("Live stream", "/live", expect_contains="live")
test("Mind stream", "/mindstream", expect_contains="mind")
test("Collaborate", "/collaborate", expect_contains="collaborate")

# === APIs — Knowledge ===
print("\n[APIs — Knowledge Access]")
test("Knowledge stats", "/api/knowledge/stats")
test("Knowledge search (query)", "/api/knowledge/search?q=identity")
test("Knowledge random", "/api/knowledge/random")
test("Knowledge synthesis", "/api/knowledge/synthesis")
test("Knowledge categories", "/api/categories")
test("API search", "/api/search?q=emotion")

# === APIs — State ===
print("\n[APIs — Internal State]")
test("Briefing API", "/api/briefing")
test("Live state", "/api/live/state")
test("Mind state", "/api/mind/state")
test("Mind knowledge", "/api/mind/knowledge")
test("Mind memories", "/api/mind/memories")
test("Mind search", "/api/mind/search?q=test")
test("Mindstream API", "/api/mindstream")
test("Diagnostics", "/api/diagnostics")
test("Graph data", "/api/graph")
test("Insights API", "/api/insights")

# === APIs — Interaction ===
print("\n[APIs — Interaction]")
test("Dialogue API", "/api/dialogue")
test("Collaborate gallery", "/api/collaborate/gallery")

# === Summary ===
print("\n" + "=" * 65)
total = PASS + FAIL + WARN
print(f"Results: {PASS} passed, {FAIL} failed, {WARN} warnings out of {total} tests")
if FAIL == 0 and WARN == 0:
    print("🎉 Perfect — every page works!")
elif FAIL == 0:
    print("✓ All pages load, but some have content gaps.")
else:
    print(f"⚠ {FAIL} broken pages need fixing for real user alignment.")
print("=" * 65)