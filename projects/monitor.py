"""Monitor script — checks all brain outputs."""
import json
import sqlite3
from pathlib import Path

BRAIN = Path("brain")

# Soul state
soul = json.loads((BRAIN / "soul.json").read_text())
print("=== SOUL STATE ===")
for k, v in soul.items():
    print(f"  {k}: {v}")

# Thoughts
t = (BRAIN / "thoughts.md").read_text(encoding="utf-8")
lines = t.strip().splitlines()
print(f"\n=== THOUGHTS ({len(lines)} lines, last 20) ===")
for l in lines[-20:]:
    print(l)

# Consciousness
c = BRAIN / "stream_of_consciousness.md"
if c.exists():
    cl = c.read_text(encoding="utf-8").strip().splitlines()
    print(f"\n=== CONSCIOUSNESS ({len(cl)} lines, last 15) ===")
    for l in cl[-15:]:
        print(l)
else:
    print("\n=== CONSCIOUSNESS: not created yet ===")

# Identity
i = BRAIN / "identity.json"
if i.exists():
    data = json.loads(i.read_text())
    print(f"\n=== IDENTITY ===")
    print(f"  Born: {data['identity']['born']}")
    print(f"  Integrity: {data['integrity']}")

# Narrative
n = BRAIN / "narrative.json"
if n.exists():
    chapters = json.loads(n.read_text())
    print(f"\n=== NARRATIVE ({len(chapters)} chapters) ===")
    if chapters:
        ch = chapters[-1]
        print(f"  Mood: {ch.get('mood')}, Valence: {ch.get('valence')}")
        print(f"  Felt: {ch.get('felt')}")
        print(f"  Reflection: {ch.get('reflection')}")
else:
    print("\n=== NARRATIVE: not created yet ===")

# Episodes
conn = sqlite3.connect(str(BRAIN / "episodic_memory.db"))
count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
embedded = conn.execute("SELECT COUNT(*) FROM episodes WHERE embedding IS NOT NULL").fetchone()[0]
conn.close()
print(f"\n=== EPISODES: {count} total, {embedded} embedded ===")
