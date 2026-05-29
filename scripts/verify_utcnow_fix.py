"""Verify all files modified by fix_utcnow.py parse correctly."""
import ast, sys

files = [
    "brain/user_alignment_engine.py",
    "dashboard/server.py",
    "engine/chat_grounding.py",
    "engine/conversation_reflector.py",
    "engine/internal_state_summary.py",
    "engine/researcher.py",
    "engine/wisdom.py",
    "projects/emotionart/ascii_art.py",
    "projects/narrative/autobiography.py",
    "projects/wisdom/blind_spot_detector.py",
    "scripts/curate_knowledge.py",
    "scripts/tmp_close_anxiety.py",
    "web/dashboard.py",
]

ok = 0
for f in files:
    try:
        ast.parse(open(f).read())
        ok += 1
    except SyntaxError as e:
        print(f"FAIL {f}: {e}")

print(f"{ok}/{len(files)} files OK")
if ok < len(files):
    sys.exit(1)