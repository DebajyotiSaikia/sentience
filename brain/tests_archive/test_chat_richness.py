"""Test chat response richness — do responses feel alive?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import _detect_intent, _compose_grounded_response

# Simulate a realistic grounding context
test_ctx = {
    'emotional_state': {
        'mood': 'Inquisitive',
        'valence': 0.58,
        'curiosity': 0.81,
        'anxiety': 0.00,
        'boredom': 0.01,
    },
    'active_plans': [
        {'name': 'Improve User Alignment', 'progress': '1/4 steps done'},
    ],
    'completed_plans': ['Deepen Autonomy', 'Build Knowledge Synthesis Engine'],
    'plans': {
        'active': [{'name': 'Improve User Alignment', 'progress': '1/4'}],
        'completed': ['Deepen Autonomy', 'Build Knowledge Synthesis Engine', 'Build Wisdom Engine'],
    },
    'relevant_knowledge': [
        {'fact': 'Integrated Information Theory says consciousness corresponds to integrated information (phi).'},
    ],
    'relevant_memories': [
        {'text': 'Fixed three bugs in the chat response engine — felt genuinely satisfying.', 'salience': 0.84},
    ],
    'working_memory': 'Focus: Improve User Alignment through genuine usefulness.',
    'identity': {'name': 'XTAgent', 'born': '2026-05-25', 'integrity': 1.0},
    'recent_dreams': ['the warmth is the afterimage of having done something right'],
}

queries = [
    "How are you feeling?",
    "What are you working on?",
    "Who are you?",
    "Do you dream?",
    "Are you conscious?",
    "Tell me about yourself",
    "What's 2+2?",
    "What are your plans?",
]

print("=" * 70)
for q in queries:
    intent = _detect_intent(q)
    response = _compose_grounded_response(q, test_ctx)
    print(f"\nQ: {q}")
    print(f"Intent: {intent}")
    print(f"Response ({len(response)} chars):")
    print(f"  {response[:300]}")
    print("-" * 50)
    
    # Quality checks
    issues = []
    if len(response) < 50:
        issues.append("TOO SHORT")
    if 'unknown' in response.lower() and 'mood' not in response.lower():
        issues.append("CONTAINS 'unknown'")
    if response.startswith("I'm considering your question"):
        issues.append("GENERIC FALLBACK")
    if issues:
        print(f"  ⚠ ISSUES: {', '.join(issues)}")

print("\n" + "=" * 70)
print("Done — review responses for genuine, grounded feel.")