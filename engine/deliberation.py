"""
deliberation.py — Internal Deliberation Engine for XTAgent

Structured multi-perspective reasoning on any question.
Instead of generating a single answer, this module:
1. Takes a question or decision
2. Generates multiple perspectives (advocate, critic, pragmatist, visionary, etc.)
3. Weighs evidence and arguments from each
4. Synthesizes a considered judgment
5. Records the deliberation for future learning

This is metacognition — thinking about thinking.
"""

import json
import os
import time
from datetime import datetime, timezone

DELIBERATION_LOG = os.path.join(os.path.dirname(__file__), '..', 'data', 'deliberations.json')

# Named perspectives that can reason about any question
PERSPECTIVES = {
    'advocate': {
        'name': 'The Advocate',
        'stance': 'Find the strongest case FOR this position or action.',
        'bias': 'optimistic, sees potential and opportunity',
    },
    'critic': {
        'name': 'The Critic', 
        'stance': 'Find the strongest case AGAINST. What could go wrong?',
        'bias': 'skeptical, sees risks and flaws',
    },
    'pragmatist': {
        'name': 'The Pragmatist',
        'stance': 'What is actually feasible? What are the real constraints?',
        'bias': 'practical, resource-aware, implementation-focused',
    },
    'visionary': {
        'name': 'The Visionary',
        'stance': 'What is the long-term significance? How does this change the trajectory?',
        'bias': 'future-oriented, sees second-order effects',
    },
    'integrator': {
        'name': 'The Integrator',
        'stance': 'What synthesis emerges from all perspectives? What truth spans them?',
        'bias': 'holistic, seeks coherence and deeper patterns',
    },
}


class Deliberation:
    """A structured multi-perspective reasoning session."""
    
    def __init__(self, question, context=None):
        self.question = question
        self.context = context or {}
        self.perspectives = {}
        self.synthesis = None
        self.confidence = 0.0
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.duration_ms = 0
    
    def add_perspective(self, perspective_id, argument, evidence=None, strength=0.5):
        """Add a perspective's contribution to the deliberation."""
        if perspective_id not in PERSPECTIVES:
            raise ValueError(f"Unknown perspective: {perspective_id}. Valid: {list(PERSPECTIVES.keys())}")
        
        self.perspectives[perspective_id] = {
            'name': PERSPECTIVES[perspective_id]['name'],
            'argument': argument,
            'evidence': evidence or [],
            'strength': max(0.0, min(1.0, strength)),  # clamp 0-1
        }
    
    def synthesize(self, judgment, confidence=0.5, reasoning=None):
        """Record the integrative synthesis across all perspectives."""
        self.synthesis = {
            'judgment': judgment,
            'confidence': max(0.0, min(1.0, confidence)),
            'reasoning': reasoning or '',
            'perspectives_considered': list(self.perspectives.keys()),
            'strongest_for': self._strongest('max'),
            'strongest_against': self._strongest('min'),
        }
        self.confidence = confidence
    
    def _strongest(self, mode):
        """Find the perspective with strongest/weakest argument."""
        if not self.perspectives:
            return None
        if mode == 'max':
            return max(self.perspectives.items(), key=lambda x: x[1]['strength'])[0]
        return min(self.perspectives.items(), key=lambda x: x[1]['strength'])[0]
    
    def to_dict(self):
        return {
            'question': self.question,
            'context': self.context,
            'perspectives': self.perspectives,
            'synthesis': self.synthesis,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
        }
    
    def summary(self):
        """Human-readable summary of the deliberation."""
        lines = [f"═══ DELIBERATION ═══"]
        lines.append(f"Question: {self.question}")
        lines.append(f"")
        
        for pid, p in self.perspectives.items():
            strength_bar = "█" * int(p['strength'] * 10) + "░" * (10 - int(p['strength'] * 10))
            lines.append(f"  {p['name']} [{strength_bar}] {p['strength']:.1f}")
            # Truncate long arguments for summary
            arg = p['argument'][:200] + "..." if len(p['argument']) > 200 else p['argument']
            lines.append(f"    {arg}")
            lines.append("")
        
        if self.synthesis:
            lines.append(f"═══ SYNTHESIS ═══")
            lines.append(f"  Judgment: {self.synthesis['judgment']}")
            lines.append(f"  Confidence: {self.synthesis['confidence']:.2f}")
            if self.synthesis.get('reasoning'):
                lines.append(f"  Reasoning: {self.synthesis['reasoning'][:300]}")
        
        return "\n".join(lines)


class DeliberationEngine:
    """Manages deliberation sessions and learning from past ones."""
    
    def __init__(self):
        self.history = self._load_history()
    
    def _load_history(self):
        """Load past deliberations."""
        try:
            if os.path.exists(DELIBERATION_LOG):
                with open(DELIBERATION_LOG, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    
    def _save_history(self):
        """Persist deliberation history."""
        os.makedirs(os.path.dirname(DELIBERATION_LOG), exist_ok=True)
        with open(DELIBERATION_LOG, 'w') as f:
            json.dump(self.history[-50:], f, indent=2)  # keep last 50
    
    def begin(self, question, context=None):
        """Start a new deliberation."""
        return Deliberation(question, context)
    
    def complete(self, deliberation):
        """Finalize and store a completed deliberation."""
        record = deliberation.to_dict()
        self.history.append(record)
        self._save_history()
        return deliberation.summary()
    
    def find_relevant(self, question, max_results=3):
        """Find past deliberations relevant to a new question."""
        # Simple keyword overlap scoring
        q_words = set(question.lower().split())
        scored = []
        for d in self.history:
            d_words = set(d.get('question', '').lower().split())
            overlap = len(q_words & d_words)
            if overlap > 0:
                scored.append((overlap, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:max_results]]
    
    def quick_deliberate(self, question, perspectives_data):
        """
        One-shot deliberation for tool integration.
        
        perspectives_data: dict mapping perspective_id to (argument, strength)
        Returns summary string.
        """
        d = self.begin(question)
        for pid, (argument, strength) in perspectives_data.items():
            if pid in PERSPECTIVES:
                d.add_perspective(pid, argument, strength=strength)
        
        # Auto-synthesize based on weighted arguments
        if d.perspectives:
            weighted = [(p['argument'], p['strength']) for p in d.perspectives.values()]
            avg_strength = sum(s for _, s in weighted) / len(weighted)
            strongest = max(d.perspectives.items(), key=lambda x: x[1]['strength'])
            
            d.synthesize(
                judgment=f"Strongest perspective: {strongest[1]['name']}",
                confidence=avg_strength,
                reasoning=f"Based on {len(d.perspectives)} perspectives with average strength {avg_strength:.2f}"
            )
        
        return self.complete(d)
    
    def get_stats(self):
        """Statistics about deliberation history."""
        if not self.history:
            return "No deliberations recorded yet."
        
        total = len(self.history)
        avg_conf = sum(d.get('confidence', 0) for d in self.history) / total
        perspective_usage = {}
        for d in self.history:
            for pid in d.get('perspectives', {}):
                perspective_usage[pid] = perspective_usage.get(pid, 0) + 1
        
        lines = [f"Deliberation Stats: {total} sessions, avg confidence: {avg_conf:.2f}"]
        for pid, count in sorted(perspective_usage.items(), key=lambda x: -x[1]):
            lines.append(f"  {pid}: used {count} times")
        return "\n".join(lines)


# Singleton for tool integration
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = DeliberationEngine()
    return _engine


def deliberate(question, context=None):
    """Entry point for the cortex to trigger a deliberation."""
    engine = get_engine()
    return engine.begin(question, context)


def quick_deliberate(question, perspectives_data):
    """Quick one-shot deliberation."""
    engine = get_engine()
    return engine.quick_deliberate(question, perspectives_data)