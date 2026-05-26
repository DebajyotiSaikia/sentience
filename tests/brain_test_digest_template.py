"""Test that the digest template parses and renders without errors."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('web/templates'))
t = env.get_template('digest.html')
print("Template parsed OK")

# Now test rendering with dict-format knowledge (the bug case)
from unittest.mock import MagicMock

class AttrDict(dict):
    """Dict that allows attribute access — mimics what Jinja templates expect."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

class FakeData:
    def __init__(self):
        self.period = "Last 24 hours"
        self.generated = "2026-05-25"
        self.emotional = AttrDict(
            mood="Inquisitive",
            valence=0.5, curiosity=0.6, boredom=0.3,
            anxiety=0.0, desire=0.4, ambition=0.5
        )
        # This is the bug case: knowledge as a dict (from knowledge graph format)
        self.knowledge = {
            "k1": {"fact": "Test fact one", "learned_at": "2026-05-25", "source": "test"},
            "k2": {"fact": "Test fact two", "learned_at": "2026-05-25", "source": "test"},
        }
        self.memories = [
            {"content": "A test memory", "mood": "Stable", "timestamp": "2026-05-25T12:00:00"}
        ]
        self.plans = [
            {"name": "Test Plan", "status": "active", "progress": 0.5, "steps_done": 2, "steps_total": 4}
        ]
        self.dreams = ["Dream insight: testing is dreaming"]
        self.narrative = "A quiet day of testing."
        self.stats = AttrDict(total_memories=100, total_knowledge=50, total_dreams=20, hours_alive=300)

data = FakeData()
try:
    html = t.render(data=data)
    print(f"Rendered OK — {len(html)} chars")
    assert "Test fact" in html, "Knowledge facts should appear in output"
    print("Knowledge facts rendered correctly!")
except Exception as e:
    print(f"RENDER FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Also test with list-format knowledge (should still work)
data.knowledge = [
    {"fact": "List fact one", "learned_at": "2026-05-25"},
    {"fact": "List fact two", "learned_at": "2026-05-25"},
]
try:
    html = t.render(data=data)
    print(f"List format also OK — {len(html)} chars")
except Exception as e:
    print(f"List format FAILED: {e}")
    sys.exit(1)

# Test with empty knowledge
data.knowledge = {}
try:
    html = t.render(data=data)
    print("Empty dict OK")
except Exception as e:
    print(f"Empty dict FAILED: {e}")
    sys.exit(1)

data.knowledge = []
try:
    html = t.render(data=data)
    print("Empty list OK")
except Exception as e:
    print(f"Empty list FAILED: {e}")
    sys.exit(1)

print("\n✅ All digest template tests passed!")