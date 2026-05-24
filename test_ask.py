import sys
sys.path.insert(0, '.')
from web.ask import create_ask_blueprint

# Create blueprint without agent — will use file fallback
bp = create_ask_blueprint()
result = bp.search('knowledge graph')
print(f"Query: {result['question']}")
print(f"Matched: {result['matched']} / {result.get('total_searched', '?')} docs")
for i in range(min(5, len(result['results']))):
    text = result['results'][i]
    src = result['sources'][i]
    typ = result['types'][i]
    display = text[:80] + '...' if len(text) > 80 else text
    print(f"  [{typ}] {display}")
    print(f"        src: {src}")

print()
# Test a second query
result2 = bp.search('emotion anxiety')
print(f"Query: {result2['question']}")
print(f"Matched: {result2['matched']} docs")
for i in range(min(3, len(result2['results']))):
    text = result2['results'][i]
    display = text[:80] + '...' if len(text) > 80 else text
    print(f"  [{result2['types'][i]}] {display}")