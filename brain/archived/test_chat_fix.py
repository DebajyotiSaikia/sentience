"""Quick test: verify chat_engine imports and responds."""
import sys, ast
sys.path.insert(0, '.')

# 1. Syntax check
print("=== Syntax Check ===")
with open('engine/chat_engine.py') as f:
    source = f.read()
tree = ast.parse(source)
fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
print(f"Functions found: {len(fns)}")
assert 'respond' in fns, f"'respond' not in functions: {fns}"
assert '_respond_general' in fns, f"'_respond_general' not in functions: {fns}"
print("  respond: YES")
print("  _respond_general: YES")

# 2. Import check
print("\n=== Import Check ===")
try:
    from engine.chat_engine import respond, _respond_general
    print("  Import OK")
except Exception as e:
    print(f"  Import FAILED: {e}")
    sys.exit(1)

# 3. Functional test
print("\n=== Functional Test ===")
test_messages = [
    "What are you thinking about?",
    "How do you feel?",
    "Tell me about your plans",
    "What is consciousness?",
    "Hello!",
]

for msg in test_messages:
    try:
        result = respond(msg)
        preview = result[:120].replace('\n', ' ')
        print(f"  '{msg[:30]}' → ({len(result)} chars) {preview}...")
    except Exception as e:
        print(f"  '{msg[:30]}' → ERROR: {e}")

print("\n=== Done ===")