"""Archive redundant test files from brain/ to brain/archived/"""
import shutil
import os

# Files to KEEP — these test real, specific modules
KEEP = {
    'test_adaptive_response.py',        # tests brain/adaptive_response.py
    'test_alignment_guidance.py',        # tests alignment guidance module
    'test_chat_composer.py',             # tests chat_composer module
    'test_chat_feedback_endpoint.py',    # tests POST /chat/feedback route
    'test_implicit_learning.py',         # tests implicit learning
    'test_internal_state_summary.py',    # tests engine/internal_state_summary.py
    'test_response_adapter.py',          # tests response adapter
    'test_response_intelligence.py',     # tests brain.response_intelligence
    'test_useful_chat_adapter.py',       # tests useful chat adapter
    'test_user_alignment_engine.py',     # tests User Alignment Engine
    'test_user_alignment_profile.py',    # tests user alignment profile
    'test_user_model.py',               # tests user model
    'test_user_alignment_chat.py',       # tests alignment chat integration
}

archived_dir = os.path.join('brain', 'archived')
os.makedirs(archived_dir, exist_ok=True)

moved = []
kept = []
for f in sorted(os.listdir('brain')):
    if not f.startswith('test_') or not f.endswith('.py'):
        continue
    if f in KEEP:
        kept.append(f)
    else:
        src = os.path.join('brain', f)
        dst = os.path.join(archived_dir, f)
        shutil.move(src, dst)
        moved.append(f)

print(f"Kept {len(kept)} test files:")
for f in kept:
    print(f"  ✓ {f}")
print(f"\nArchived {len(moved)} test files:")
for f in moved:
    print(f"  → {f}")