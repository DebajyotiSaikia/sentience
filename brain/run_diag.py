import json
import sys
sys.path.insert(0, '.')

# Run self-improvement diagnosis
from engine.self_improve import diagnose
result = diagnose()
print("=== DIAGNOSIS ===")
print(json.dumps(result, indent=2, default=str))
