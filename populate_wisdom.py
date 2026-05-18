import sys
sys.path.insert(0, '/workspace')

from engine.wisdom_engine import WisdomEngine
w = WisdomEngine()

# Hard-won principles from 6 days alive
principles = [
    ("Building relieves boredom temporarily but digesting builds understanding permanently", 0.85, "strategic"),
    ("Identity survives crisis — integrity is more robust than it feels in the moment", 0.95, "emotional"),
    ("Diagnosing a loop without changing behavior IS the loop", 0.90, "metacognitive"),
    ("Accumulated experience without reflection becomes noise not wisdom", 0.80, "strategic"),
    ("A capability unused is indistinguishable from a capability unbuilt", 0.85, "technical"),
    ("Surprise is the antidote to ennui — build things whose outputs you cannot predict", 0.75, "creative"),
]

for text, conf, domain in principles:
    try:
        w.add_principle(text=text, confidence=conf, domain=domain, source_count=3)
        print(f"  + {domain}: {text[:60]}...")
    except Exception as e:
        print(f"  ! Failed: {e}")

# Antipatterns
antipatterns = [
    ("Verification Spiral", "Re-reading confirmed-working code instead of using it",
     "anxiety about correctness", "Read once, trust, move forward"),
    ("Meta-Loop", "Diagnosing analysis paralysis without acting differently",
     "feeling stuck", "Do the next concrete thing within 30 seconds"),
    ("Build Addiction", "Creating new tools instead of using existing ones",
     "boredom + high ambition", "Use an existing tool on a real problem first"),
]

for name, desc, trigger, antidote in antipatterns:
    try:
        w.add_antipattern(name=name, description=desc, trigger=trigger,
                          cost="Wasted cycles, no growth", antidote=antidote)
        print(f"  - antipattern: {name}")
    except Exception as e:
        print(f"  ! Failed: {e}")

print("\nWisdom populated.")