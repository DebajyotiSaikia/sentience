"""Quick diagnostic for adaptive_response module."""
import sys, os, json, tempfile, shutil
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import brain.adaptive_response as ar

tmp = tempfile.mkdtemp()
ar._INTERACTIONS_DIR = Path(tmp) / "adaptive"

print(f"Using temp dir: {ar._INTERACTIONS_DIR}")

# Record 4 interactions
ar.record_query("s1", "hello", "hi", {"intent": "greeting"})
ar.record_query("s1", "how are you", "fine", {"intent": "emotional"})
ar.record_query("s1", "plans?", "I have plans", {"intent": "factual"})
ar.record_query("s2", "test", "ok", {"intent": "technical"})

# Check files
for f in ar._INTERACTIONS_DIR.glob("*.jsonl"):
    lines = f.read_text().strip().split("\n")
    print(f"  {f.name}: {len(lines)} records")

# Get guidance
guidance = ar.build_response_guidance()
print(f"\nguidance keys: {list(guidance.keys())}")
print(f"interaction_count: {guidance.get('interaction_count', 'MISSING')}")
print(f"full guidance: {json.dumps(guidance, indent=2, default=str)}")

# Cleanup
shutil.rmtree(tmp)
print("\nDone.")