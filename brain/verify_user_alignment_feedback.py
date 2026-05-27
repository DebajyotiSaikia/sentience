"""Verify user alignment feedback system works end-to-end."""
import sys, os, json, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("=== User Alignment Feedback Verification ===\n")

# Patch paths to use temp dir
import engine.user_alignment as ua

orig_feedback = ua.FEEDBACK_PATH
orig_summary = ua.SUMMARY_PATH
tmpdir = tempfile.mkdtemp()
ua.FEEDBACK_PATH = os.path.join(tmpdir, "feedback.jsonl")
ua.SUMMARY_PATH = os.path.join(tmpdir, "summary.json")

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {name}")
        passed += 1
    else:
        print(f"  ✗ {name}")
        failed += 1

# 1. Record feedback
print("[1] record_feedback()")
evt = ua.record_feedback(
    message_id="msg-001",
    rating=4,
    comment="helpful answer",
    query="what are you thinking?",
    response_preview="I'm currently focused on...",
    mood="Inquisitive",
)
test("returns dict", isinstance(evt, dict))
test("has id", "id" in evt)
test("rating clamped", evt.get("rating") == 4)
test("has timestamp", "timestamp" in evt)

# Record a second event
ua.record_feedback(message_id="msg-002", rating=2, comment="too vague")

# Record a third
ua.record_feedback(message_id="msg-003", rating=5, comment="excellent")

# 2. Load feedback
print("\n[2] load_feedback()")
fb = ua.load_feedback(limit=10)
test("returns list", isinstance(fb, list))
test("has 3 events", len(fb) == 3)
test("first has message_id", fb[0].get("message_id") == "msg-001" if fb else False)

# 3. Summarize alignment
print("\n[3] summarize_alignment()")
summary = ua.summarize_alignment()
test("returns dict", isinstance(summary, dict))
test("has count or total", "total_feedback" in summary or "count" in summary)

# 4. get_alignment_score
print("\n[4] get_alignment_score()")
score = ua.get_alignment_score()
test("returns float", isinstance(score, (int, float)))
test("score in range", 0.0 <= score <= 1.0)

# 5. suggest_response_guidance
print("\n[5] suggest_response_guidance()")
guidance = ua.suggest_response_guidance(query="hello", mood="Calm")
test("returns dict", isinstance(guidance, dict))

# 6. Rating clamping
print("\n[6] Edge cases")
evt_low = ua.record_feedback(message_id="msg-low", rating=-1)
test("rating clamped to 1", evt_low.get("rating") == 1)
evt_high = ua.record_feedback(message_id="msg-high", rating=99)
test("rating clamped to 5", evt_high.get("rating") == 5)

# Cleanup
ua.FEEDBACK_PATH = orig_feedback
ua.SUMMARY_PATH = orig_summary
import shutil
shutil.rmtree(tmpdir, ignore_errors=True)

print(f"\n=== Results: {passed} passed, {failed} failed ===")
sys.exit(0 if failed == 0 else 1)