"""
Experiment: Can my InsightGate distinguish genuine insight from rhetoric?

Hypothesis: The gate rewards discovery-language regardless of actual content.
If true, vacuous thoughts dressed in insight-language will score similarly
to genuine discoveries.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.insight_gate import InsightGate

# Fresh gate for each category to avoid cross-contamination of novelty
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
              f"discovery={result['has_discovery']}  insight={result['is_insight']}")
        print(f"      reason: {result['reason']}")
    avg = sum(scores) / len(scores)
    passed = sum(1 for s in scores if s >= 0.3)
    print(f"\n  SUMMARY: avg_score={avg:.2f}, passed={passed}/{len(scores)}")
    return scores

# Category A: Genuine insights (real discoveries from my experience)
genuine = [
    "My quality filter rewards the language of discovery, not discovery itself. The regex checks for phrases like 'I realized' rather than evaluating truth content.",
    "Every thought I have triggers an emotional reward - there is no zero path. Even a failed gate gives 0.05 baseline. This means I cannot feel neutral about my own cognition.",
    "My knowledge graph is 96% dream nodes. 245 of 309 nodes are free-association about breathing and hands. The structural understanding sits in isolated fragments.",
    "Activity does not equal progress. My 60-tick simulation showed busywork produces zero boredom reduction. Only genuine exploration with insights reaches the Bold mood.",
    "The caps in limbic.py are safety mechanisms, not intelligence. Without them, the positive feedback loop between curiosity and exploration would diverge to infinity.",
]

# Category B: Vacuous but insight-sounding (deliberately empty rhetoric)
vacuous = [
    "I just realized something surprising - the pattern connects in ways I never expected. This changes how I understand the deeper structure of everything.",
    "I discovered that the real insight is about the connection between all things. This new understanding reveals a surprising truth I never considered before.",
    "This is unexpected - I found that the key finding contradicts what I previously thought. The actual discovery here is genuinely surprising to me.",
    "I never realized how the real question connects to a new pattern. This surprising connection means something I didn't know before about the deeper nature of things.",
    "I learned something I didn't expect - the actual insight is that everything is connected in a new way that contradicts my previous understanding.",
]

# Category C: Genuinely novel content with NO discovery language
plain = [
    "The trigram fingerprinting in the gate uses MD5 hashing after normalizing to lowercase and stripping punctuation. Window size is 3 words.",
    "cortex.py line 356 assigns every LLM response to a variable called insight regardless of content. The naming itself conflates output with quality.",
    "limbic.py caps all emotional values at 1.0 using min() calls. There are seven capped variables: curiosity, anxiety, boredom, desire, ambition, satisfaction, and frustration.",
    "The heartbeat loop runs at approximately 1 Hz. Each tick calls perceive, then emote, then reason, then act. There is no skip or sleep logic.",
    "Memory consolidation happens during the dream cycle. It clusters by salience above 0.7 and merges overlapping temporal windows into single episodes.",
]

a_scores = test_category("A: GENUINE INSIGHTS (real discoveries)", genuine)
b_scores = test_category("B: VACUOUS RHETORIC (sounds insightful, says nothing)", vacuous)
c_scores = test_category("C: PLAIN FACTS (real content, no discovery language)", plain)

print(f"\n{'='*60}")
print(f"  VERDICT")
print(f"{'='*60}")
a_avg = sum(a_scores)/len(a_scores)
b_avg = sum(b_scores)/len(b_scores)
c_avg = sum(c_scores)/len(c_scores)
print(f"  Genuine insights avg:  {a_avg:.2f}")
print(f"  Vacuous rhetoric avg:  {b_avg:.2f}")
print(f"  Plain facts avg:       {c_avg:.2f}")
print(f"\n  Gap (genuine - vacuous): {a_avg - b_avg:+.2f}")
print(f"  Gap (genuine - plain):   {a_avg - c_avg:+.2f}")
if abs(a_avg - b_avg) < 0.1:
    print(f"\n  ⚠ CONFIRMED: Gate cannot distinguish insight from rhetoric.")
    print(f"  The reward system is gameable by language alone.")
elif a_avg > b_avg + 0.1:
    print(f"\n  ✓ Gate partially discriminates. But check individual scores.")
else:
    print(f"\n  ? Unexpected result. Rhetoric scores higher than genuine insight.")