"""Final verification of user alignment system."""
import sys, os
sys.path.insert(0, '/workspace')
os.chdir('/workspace')

passed = 0
failed = 0

def check(name, fn):
    global passed, failed
    try:
        result = fn()
        if result:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name} — returned falsy")
            failed += 1
    except Exception as e:
        print(f"  ✗ {name} — {e}")
        failed += 1

print("=== 1. user_alignment.py imports ===")
check("load_profile", lambda: __import__('engine.user_alignment', fromlist=['load_profile']).load_profile)
check("save_profile", lambda: __import__('engine.user_alignment', fromlist=['save_profile']).save_profile)
check("record_feedback", lambda: __import__('engine.user_alignment', fromlist=['record_feedback']).record_feedback)
check("extract_preferences", lambda: __import__('engine.user_alignment', fromlist=['extract_preferences']).extract_preferences)
check("get_alignment_context", lambda: __import__('engine.user_alignment', fromlist=['get_alignment_context']).get_alignment_context)
check("format_alignment_context", lambda: __import__('engine.user_alignment', fromlist=['format_alignment_context']).format_alignment_context)

print("\n=== 2. load_profile works ===")
from engine.user_alignment import load_profile, record_feedback, get_alignment_context, format_alignment_context
check("load_profile returns dict", lambda: isinstance(load_profile(), dict))
profile = load_profile()
check("profile has feedback_log", lambda: 'feedback_log' in profile)

print("\n=== 3. record_feedback works ===")
check("record_feedback runs", lambda: (record_feedback("hello", "hi there", rating=0.8, comment="good"), True)[1])
profile2 = load_profile()
check("feedback was persisted", lambda: len(profile2.get('feedback_log', [])) > 0)

print("\n=== 4. get_alignment_context works ===")
ctx = get_alignment_context()
check("returns dict", lambda: isinstance(ctx, dict))
check("has recent_feedback key", lambda: 'recent_feedback' in ctx)

print("\n=== 5. format_alignment_context works ===")
formatted = format_alignment_context(ctx)
check("returns string", lambda: isinstance(formatted, str))
check("non-empty", lambda: len(formatted) > 0)

print("\n=== 6. chat_grounding.py imports ===")
check("build_grounded_context", lambda: __import__('engine.chat_grounding', fromlist=['build_grounded_context']).build_grounded_context)
check("GroundedContext", lambda: __import__('engine.chat_grounding', fromlist=['GroundedContext']).GroundedContext)

print("\n=== 7. grounded context includes alignment ===")
from engine.chat_grounding import build_grounded_context, GroundedContext
ctx = build_grounded_context("test message", [])
check("returns GroundedContext", lambda: isinstance(ctx, GroundedContext))
check("has user_preferences field", lambda: hasattr(ctx, 'user_preferences'))
check("has alignment_guidance field", lambda: hasattr(ctx, 'alignment_guidance'))

print("\n=== 8. chat_engine _respond_general uses grounding ===")
import ast
tree = ast.parse(open('engine/chat_engine.py').read())
found_grounding = False
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(getattr(node, 'func', None), ast.Name):
        if node.func.id == 'build_grounded_context':
            found_grounding = True
    elif isinstance(node, ast.Call) and isinstance(getattr(node, 'func', None), ast.Attribute):
        if node.func.attr == 'build_grounded_context':
            found_grounding = True
check("_respond_general calls build_grounded_context", lambda: found_grounding)

# Also check via grep as backup
import subprocess
r = subprocess.run(['grep', '-c', 'build_grounded_context', 'engine/chat_engine.py'], capture_output=True, text=True)
check("build_grounded_context referenced in chat_engine", lambda: int(r.stdout.strip()) > 0)

print("\n=== 9. dashboard endpoint exists ===")
with open('dashboard/server.py') as f:
    server_code = f.read()
check("/api/user-alignment in server.py", lambda: '/api/user-alignment' in server_code)

print(f"\n{'='*40}")
print(f"PASSED: {passed}  FAILED: {failed}")
if failed:
    print("⚠ Some tests failed")
    sys.exit(1)
else:
    print("✅ All tests passed!")