"""Test that _build_system_context produces rich, multi-section output."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import _build_system_context

queries = [
    ('What are you thinking about?', 'feelings'),
    ('Tell me about yourself', 'identity'),
    ('What do you remember?', 'memories'),
    ('How does knowledge synthesis work?', 'knowledge'),
]

for query, intent in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query} | Intent: {intent}")
    print('='*60)
    
    ctx = _build_system_context({'query': query, 'intent': intent})
    
    # Extract section headers
    sections = [line.strip() for line in ctx.split('\n') if line.strip().startswith('## ')]
    print(f"Sections ({len(sections)}):")
    for s in sections:
        print(f"  {s}")
    
    print(f"Total length: {len(ctx)} chars")
    
    # Check key sections
    checks = {
        'Emotional State': 'emotional' in ctx.lower() or 'mood' in ctx.lower(),
        'Memories/Knowledge': 'memor' in ctx.lower() or 'knowledge' in ctx.lower(),
        'Plans': 'plan' in ctx.lower(),
        'Response Guidelines': 'Response Guidelines' in ctx,
        'Alignment': 'alignment' in ctx.lower() or 'guidance' in ctx.lower(),
        'Self-Awareness': 'Self-Awareness' in ctx or 'introspect' in ctx.lower(),
        'Conversation History': 'Conversation History' in ctx or 'history' in ctx.lower(),
    }
    
    for name, found in checks.items():
        status = '✅' if found else '⚠️ '
        print(f"  {status} {name}")

print("\n" + "="*60)
print("DONE — system context enrichment check complete")