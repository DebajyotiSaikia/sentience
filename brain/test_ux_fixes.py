"""Quick test of the 4 UX audit failure points."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
c = app.test_client()

# Test 1: Knowledge stats — does it report non-zero facts?
r = c.get('/api/knowledge/stats')
print('=== KNOWLEDGE STATS ===')
print(f'Status: {r.status_code}')
print(f'Body: {r.get_data(as_text=True)[:400]}')

# Test 2: Home page — does it have a call to action?
r2 = c.get('/')
html = r2.get_data(as_text=True)
has_chat_link = '/chat' in html
has_cta = any(w in html.lower() for w in ['start', 'talk to me', 'chat with me', 'begin'])
print('\n=== HOME PAGE ===')
print(f'Status: {r2.status_code}, Length: {len(html)}')
print(f'Has /chat link: {has_chat_link}')
print(f'Has CTA: {has_cta}')

# Test 3: Chat page — does it have conversation starters?
r3 = c.get('/chat')
chat_html = r3.get_data(as_text=True)
has_starter = any(w in chat_html.lower() for w in ['starter', 'suggestion', 'try asking'])
print('\n=== CHAT PAGE ===')
print(f'Status: {r3.status_code}, Length: {len(chat_html)}')
print(f'Has starters: {has_starter}')

# Test 4: Search API — does it return results for "identity"?
r4 = c.get('/api/knowledge/search?q=identity')
print('\n=== SEARCH API ===')
print(f'Status: {r4.status_code}')
print(f'Body: {r4.get_data(as_text=True)[:400]}')

# Test 5: Run the actual audit
print('\n=== FULL UX AUDIT ===')
from brain.ux_audit import UXAudit
audit = UXAudit()
results = audit.run_all()
audit.print_report(results)