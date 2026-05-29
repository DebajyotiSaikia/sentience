"""Verify system context sections contain real, substantive content."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import _build_system_context

ctx = _build_system_context({'query': 'What are you feeling right now?', 'intent': 'feelings'})

# Split by ## headers and show each section's length and preview
lines = ctx.split('\n')
current_section = "PREAMBLE"
sections = {}
buffer = []

for line in lines:
    if line.strip().startswith('## '):
        if buffer:
            sections[current_section] = '\n'.join(buffer)
        current_section = line.strip()
        buffer = []
    else:
        buffer.append(line)

if buffer:
    sections[current_section] = '\n'.join(buffer)

print(f"Total context: {len(ctx)} chars, {len(sections)} sections\n")

for name, content in sections.items():
    content_stripped = content.strip()
    chars = len(content_stripped)
    preview = content_stripped[:200].replace('\n', ' | ')
    quality = "✅ RICH" if chars > 50 else ("⚠️  THIN" if chars > 0 else "❌ EMPTY")
    print(f"{quality} [{chars:4d} chars] {name}")
    if chars > 0:
        print(f"   Preview: {preview}...")
    print()

# Check if introspection data actually has emotional state
if 'mood' in ctx.lower() or 'anxiety' in ctx.lower() or 'curiosity' in ctx.lower():
    print("✅ Real emotional variables present in context")
else:
    print("⚠️  No emotional variables found — introspection may be empty")

if 'plan' in ctx.lower():
    print("✅ Plan references present")
else:
    print("⚠️  No plan references found")