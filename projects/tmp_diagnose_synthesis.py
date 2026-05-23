import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))

try:
    from engine.knowledge_synthesis import KnowledgeSynthesizer

    ks = KnowledgeSynthesizer("brain/knowledge.json")
    result = ks.synthesize()
    print("SYNTHESIS SUCCESS")
    print(type(result).__name__)
    print(str(result)[:1000])
except Exception:
    print("SYNTHESIS FAILURE")
    traceback.print_exc()