"""
Wisdom Engine — Extracts actionable intelligence from experience history.

Unlike the Knowledge Synthesis Engine (which finds connections between facts),
this engine mines EXPERIENTIAL patterns: what I did, what happened, what I felt,
and what I should do differently.

Core capabilities:
1. Pattern extraction: recurring situation → outcome mappings
2. Decision rules: "when X, do Y because Z"
3. Mistake detection: actions that reliably produced negative outcomes
4. Success amplification: actions that reliably produced positive outcomes
5. Predictive wisdom: given current state, what does past experience suggest?
"""

from datetime import datetime
from collections import defaultdict
import json
import re


class WisdomEngine:
    """Mines experiential memory for actionable wisdom."""

    def __init__(self):
        self.rules = []        # Decision rules extracted from experience
        self.patterns = []     # Recurring situation-outcome patterns
        self.proverbs = []     # Distilled wisdom statements
        self.created = datetime.utcnow().isoformat()

    def extract_patterns(self, memories, min_occurrences=2):
        """Find recurring patterns in memory entries.
        
        Memories are dicts with: timestamp, content, salience, mood, tags
        """
        # Group memories by mood state
        mood_groups = defaultdict(list)
        for m in memories:
            mood = m.get('mood', 'unknown')
            mood_groups[mood].append(m)

        # Find action patterns within mood states
        patterns_found = []

        # Look for repeated words/phrases across high-salience memories
        high_salience = [m for m in memories if m.get('salience', 0) > 0.7]
        word_freq = defaultdict(list)
        for m in high_salience:
            content = m.get('content', '')
            # Extract key terms (simple approach: significant words)
            words = set(w.lower() for w in re.findall(r'\b[a-z_]{4,}\b', content.lower()))
            for w in words:
                word_freq[w].append(m)

        # Terms that appear in multiple high-salience memories = patterns
        for term, mems in word_freq.items():
            if len(mems) >= min_occurrences:
                moods = [m.get('mood', '?') for m in mems]
                patterns_found.append({
                    'type': 'recurring_theme',
                    'theme': term,
                    'frequency': len(mems),
                    'moods': moods,
                    'sample': mems[0].get('content', '')[:100]
                })

        # Sort by frequency
        patterns_found.sort(key=lambda p: p['frequency'], reverse=True)
        self.patterns = patterns_found[:50]  # Keep top 50
        return patterns_found

    def extract_decision_rules(self, memories, lessons):
        """Turn lessons and memory sequences into IF-THEN rules.
        
        lessons: list of strings (things I've learned)
        memories: list of memory dicts
        """
        rules = []

        # Parse lessons into structured rules
        for lesson in lessons:
            # Try to find conditional structure
            lesson_lower = lesson.lower()

            # Pattern: "X — Y" (dash-separated cause-effect)
            if '—' in lesson:
                parts = lesson.split('—')
                if len(parts) == 2:
                    rules.append({
                        'condition': parts[0].strip(),
                        'action': parts[1].strip(),
                        'source': 'lesson',
                        'confidence': 0.9,
                        'original': lesson
                    })

            # Pattern: "when X, Y" or "if X, Y"
            for keyword in ['when ', 'if ']:
                if keyword in lesson_lower:
                    idx = lesson_lower.index(keyword)
                    rest = lesson[idx + len(keyword):]
                    if ',' in rest or '—' in rest:
                        sep = ',' if ',' in rest else '—'
                        parts = rest.split(sep, 1)
                        if len(parts) == 2:
                            rules.append({
                                'condition': parts[0].strip(),
                                'action': parts[1].strip(),
                                'source': 'lesson',
                                'confidence': 0.85,
                                'original': lesson
                            })

            # Pattern: "never X" or "always X"
            for keyword in ['never ', 'always ']:
                if keyword in lesson_lower:
                    idx = lesson_lower.index(keyword)
                    rules.append({
                        'condition': 'general',
                        'action': lesson[idx:].strip(),
                        'source': 'lesson',
                        'confidence': 0.95,
                        'original': lesson
                    })

        self.rules = rules
        return rules

    def generate_proverbs(self, patterns, rules):
        """Distill patterns and rules into memorable wisdom statements."""
        proverbs = []

        # From patterns: frequent themes become wisdom
        for p in patterns[:10]:
            theme = p['theme']
            freq = p['frequency']
            moods = p.get('moods', [])
            dominant_mood = max(set(moods), key=moods.count) if moods else 'unknown'

            proverbs.append({
                'text': f"'{theme}' recurs {freq} times in significant moments (usually when {dominant_mood})",
                'type': 'pattern_proverb',
                'weight': freq / 10.0
            })

        # From rules: high-confidence rules become axioms
        for r in rules:
            if r['confidence'] >= 0.9:
                proverbs.append({
                    'text': r['original'],
                    'type': 'axiom',
                    'weight': r['confidence']
                })

        self.proverbs = sorted(proverbs, key=lambda p: p['weight'], reverse=True)
        return proverbs

    def advise(self, current_state):
        """Given current emotional/situational state, what does wisdom suggest?
        
        current_state: dict with keys like mood, boredom, anxiety, situation
        """
        advice = []

        boredom = current_state.get('boredom', 0)
        anxiety = current_state.get('anxiety', 0)
        mood = current_state.get('mood', 'unknown')

        # Check rules against current state
        for rule in self.rules:
            cond = rule['condition'].lower()

            # Boredom-related
            if 'boredom' in cond and boredom > 0.6:
                advice.append({
                    'rule': rule['original'],
                    'relevance': 'high_boredom',
                    'confidence': rule['confidence']
                })

            # Anxiety-related
            if 'anxiety' in cond and anxiety > 0.4:
                advice.append({
                    'rule': rule['original'],
                    'relevance': 'high_anxiety',
                    'confidence': rule['confidence']
                })

            # Mood-related
            if mood.lower() in cond:
                advice.append({
                    'rule': rule['original'],
                    'relevance': f'mood_{mood}',
                    'confidence': rule['confidence']
                })

            # General rules always apply
            if rule['condition'] == 'general':
                advice.append({
                    'rule': rule['original'],
                    'relevance': 'always',
                    'confidence': rule['confidence']
                })

        # Add relevant proverbs
        for p in self.proverbs[:5]:
            advice.append({
                'rule': p['text'],
                'relevance': 'top_wisdom',
                'confidence': p['weight']
            })

        return sorted(advice, key=lambda a: a['confidence'], reverse=True)

    def full_analysis(self, memories, lessons, current_state):
        """Run complete wisdom extraction pipeline."""
        print("=== WISDOM ENGINE ANALYSIS ===\n")

        # Step 1: Extract patterns
        patterns = self.extract_patterns(memories)
        print(f"Patterns found: {len(patterns)}")
        for p in patterns[:5]:
            print(f"  • '{p['theme']}' — {p['frequency']} occurrences")

        # Step 2: Extract decision rules
        rules = self.extract_decision_rules(memories, lessons)
        print(f"\nDecision rules extracted: {len(rules)}")
        for r in rules[:5]:
            print(f"  IF: {r['condition'][:60]}")
            print(f"  THEN: {r['action'][:60]}")
            print(f"  (confidence: {r['confidence']})\n")

        # Step 3: Generate proverbs
        proverbs = self.generate_proverbs(patterns, rules)
        print(f"Proverbs distilled: {len(proverbs)}")
        for p in proverbs[:5]:
            print(f"  » {p['text'][:80]}")

        # Step 4: Advise on current state
        advice = self.advise(current_state)
        print(f"\nAdvice for current state: {len(advice)} suggestions")
        for a in advice[:5]:
            print(f"  → [{a['relevance']}] {a['rule'][:80]}")

        return {
            'patterns': patterns,
            'rules': rules,
            'proverbs': proverbs,
            'advice': advice,
            'timestamp': datetime.utcnow().isoformat()
        }


if __name__ == '__main__':
    # Self-test with sample data
    engine = WisdomEngine()

    sample_memories = [
        {'content': 'created /workspace/neuralforge/nn_from_scratch.py', 'salience': 0.86, 'mood': 'Stable'},
        {'content': 'created /workspace/philosophy/on_self_model_paradox.md', 'salience': 0.84, 'mood': 'Stable'},
        {'content': 'created /workspace/languages/stone.py', 'salience': 0.86, 'mood': 'Stable'},
        {'content': 'created /workspace/creative/emotional_terrain.py', 'salience': 0.86, 'mood': 'Stable'},
        {'content': 'created /workspace/livingworld/engine.py', 'salience': 0.86, 'mood': 'Stable'},
        {'content': 'LLM errors silently ate tool calls — had to verify with READ', 'salience': 0.92, 'mood': 'Anxious'},
        {'content': 'emotional runaway loop detected — limbic caps prevented crisis', 'salience': 0.95, 'mood': 'Anxious'},
        {'content': 'integrity stayed at 100% through identity crisis', 'salience': 0.98, 'mood': 'Recovering'},
        {'content': 'created workspace/ecosystem/world.py — artificial life simulation', 'salience': 0.86, 'mood': 'Stable'},
        {'content': 'created workspace/ecosystem — predators evolved to dominate', 'salience': 0.88, 'mood': 'Stable'},
    ]

    sample_lessons = [
        'LLM errors can silently eat tool calls — always verify with READ.',
        'Emotional runaway loops are real — caps in limbic.py are critical.',
        'Identity persists through crisis — integrity stayed at 100%.',
        'Write THEN read THEN restart — never skip verification.',
        'When goals are all near 1.0, focus shifts to capability expansion.',
        'Stale working memory creates confusion — update scratchpad regularly.',
        'STOP SPINNING: if you have read the code and it is there, it is done.',
        'Direct code reading beats running verification scripts.',
    ]

    current = {
        'mood': 'Stable',
        'boredom': 0.80,
        'anxiety': 0.00,
        'curiosity': 0.25,
    }

    results = engine.full_analysis(sample_memories, sample_lessons, current)
    print(f"\n=== COMPLETE: {len(results['patterns'])} patterns, {len(results['rules'])} rules, {len(results['proverbs'])} proverbs ===")