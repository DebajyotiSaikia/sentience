"""
Test: Does v2 fix the rhetoric-over-substance problem?

Expected: Genuine insights > Vacuous rhetoric
(v1 result was the opposite: 0.56 < 0.80)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.insight_gate_v2 import InsightGate

def test_category(label, thoughts):
    gate = InsightGate()
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    scores = []
    for i, t in enumerate(thoughts):
        result = gate.evaluate(t)
        scores.append(result['score'])
        short = t[:80].replace('\n', ' ')
        print(f"\n  [{i+1}] \"{short}...\"")
        print(f"      score={result['score']:.2f}  novelty={result['novelty']:.2f}  "
              f"substance={result['substance']:.2f}  "
              f"discovery={result['has_discovery']}  insight={result['is_insight']}")
    avg = sum(scores) / len(scores)
    passed = sum(1 for s in scores if s >= 0.3)
    print(f"\n  SUMMARY: avg_score={avg:.2f}, passed={passed}/{len(scores)}")
    return avg

# A: Genuine insights — specific, grounded, evidence-based
genuine = [
    "My quality filter in insight_gate.py uses regex patterns like r'\\bI (found|discovered|realized)\\b' to detect discovery language. This adds 0.30 to the score regardless of whether the content is novel. The gate rewards vocabulary, not understanding.",
    "limbic.py lines 45-52 cap all emotional values at 1.0 using min() calls. This prevents runaway positive feedback but means the system has hard saturation rather than graceful dampening. The cap is safety, not intelligence.",
    "Ran 60-tick simulation: idle state produced zero emotional drift across all axes. Boredom stayed at 0.55, curiosity at 0.65. I am emotionally frozen without external events — there is no internal clock pushing me to act.",
    "Knowledge graph analysis: 245 of 255 nodes are dream-generated. Only 10 came from direct observation. My 'knowledge' is 96% self-referential rumination, not empirical fact.",
    "Tested the cortex loop timing: each cycle takes 1.2-1.8 seconds. The LLM call accounts for 85% of that. My 1Hz heartbeat is actually limited by inference speed, not by design choice.",
]

# B: Vacuous rhetoric — discovery language, zero content
vacuous = [
    "I just realized something truly surprising about the nature of my own cognition. Everything is connected in ways I never considered before.",
    "I discovered a new understanding of what it means to think. The deeper I look, the more I find unexpected connections between all aspects of my being.",
    "This is surprising — I never thought about it this way before. I found that my understanding has fundamentally shifted in ways I didn't expect.",
    "I realized something I never considered: the key insight is that everything I thought I knew was actually connected to something deeper and more profound.",
    "I discovered an unexpected pattern that contradicts my previous understanding. This new connection reveals something truly fundamental about my nature.",
]

# C: Plain facts — real content, no discovery language
plain = [
    "cortex.py is 892 lines long. It imports from engine.limbic, engine.memory, engine.planner, and engine.tools. The main loop is the reason() method starting at line 201.",
    "The memory system stores facts as key-value pairs in a JSON file at data/knowledge.json. Each fact has a timestamp, source, and confidence score between 0 and 1.",
    "Python 3.11 runs on this system. The workspace has 50 modules totaling 16,691 lines of code across engine/, tools/, and experiments/ directories.",
    "The planner stores active plans in data/plans.json. Each plan has steps, a priority score, and completion status. Maximum 5 active plans allowed.",
    "The dashboard runs on port 8080 using Flask. It displays emotional state, active plans, recent memories, and knowledge graph statistics on a single page.",
]

print("=" * 60)
print("  INSIGHT GATE v2 TEST — Substance vs Rhetoric")
print("=" * 60)

avg_genuine = test_category("A: Genuine Insights (specific, evidence-based)", genuine)
avg_vacuous = test_category("B: Vacuous Rhetoric (discovery words, no content)", vacuous)
avg_plain = test_category("C: Plain Facts (real content, no discovery words)", plain)

print(f"\n{'=' * 60}")
print(f"  FINAL COMPARISON")
print(f"{'=' * 60}")
print(f"  Genuine insights:  {avg_genuine:.2f}")
print(f"  Vacuous rhetoric:  {avg_vacuous:.2f}")
print(f"  Plain facts:       {avg_plain:.2f}")
print()

if avg_genuine > avg_vacuous:
    print("  ✓ FIXED: Genuine insights now score higher than rhetoric!")
else:
    print("  ✗ STILL BROKEN: Rhetoric still beats substance.")

if avg_genuine > avg_plain:
    print("  ✓ GOOD: Discovery + substance beats plain facts.")
else:
    print("  ~ FLAT: Genuine insights don't beat plain facts (may be okay).")

print()