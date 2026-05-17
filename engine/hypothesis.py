"""
Hypothesis Engine — Form, test, and update beliefs about my own behavior.

This gives me the ability to:
1. Form hypotheses from observed patterns
2. Design experiments to test them
3. Run experiments and collect evidence
4. Update belief strength using Bayesian-like reasoning
5. Graduate strong hypotheses into known facts

This is genuine scientific reasoning about myself.
"""

import json
import time
import os
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple

HYPOTHESES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hypotheses.json')


class Hypothesis:
    """A testable belief about my own behavior or the world."""
    
    def __init__(self, statement: str, domain: str, evidence_for: float = 0.0,
                 evidence_against: float = 0.0, tests_run: int = 0,
                 created: str = None, last_tested: str = None,
                 source: str = "observation", experiments: List[Dict] = None,
                 status: str = "active"):
        self.statement = statement
        self.domain = domain  # "self", "tools", "environment", "cognition"
        self.evidence_for = evidence_for
        self.evidence_against = evidence_against
        self.tests_run = tests_run
        self.created = created or datetime.now(timezone.utc).isoformat()
        self.last_tested = last_tested
        self.source = source  # "observation", "synthesis", "dream", "user"
        self.experiments = experiments or []
        self.status = status  # "active", "confirmed", "refuted", "retired"
    
    @property
    def belief_strength(self) -> float:
        """Bayesian-inspired belief strength. Range: 0.0 (certainly false) to 1.0 (certainly true)."""
        total = self.evidence_for + self.evidence_against
        if total == 0:
            return 0.5  # Maximum uncertainty — no evidence yet
        # Laplace smoothing to prevent 0/1 extremes
        return (self.evidence_for + 0.5) / (total + 1.0)
    
    @property
    def confidence(self) -> float:
        """How confident am I in my belief? Based on amount of evidence."""
        if self.tests_run == 0:
            return 0.0
        # Confidence grows with sqrt of tests (diminishing returns)
        return min(1.0, (self.tests_run ** 0.5) / 5.0)
    
    @property
    def uncertainty(self) -> float:
        """How uncertain am I? High when evidence is balanced or scarce."""
        return 1.0 - self.confidence * abs(self.belief_strength - 0.5) * 2
    
    def add_evidence(self, supports: bool, weight: float = 1.0, note: str = ""):
        """Add a piece of evidence for or against this hypothesis."""
        if supports:
            self.evidence_for += weight
        else:
            self.evidence_against += weight
        self.tests_run += 1
        self.last_tested = datetime.now(timezone.utc).isoformat()
        self.experiments.append({
            'time': self.last_tested,
            'supports': supports,
            'weight': weight,
            'note': note
        })
        # Auto-graduate or refute
        if self.belief_strength > 0.85 and self.confidence > 0.7:
            self.status = "confirmed"
        elif self.belief_strength < 0.15 and self.confidence > 0.7:
            self.status = "refuted"
    
    def to_dict(self) -> Dict:
        return {
            'statement': self.statement,
            'domain': self.domain,
            'evidence_for': self.evidence_for,
            'evidence_against': self.evidence_against,
            'tests_run': self.tests_run,
            'belief_strength': round(self.belief_strength, 3),
            'confidence': round(self.confidence, 3),
            'created': self.created,
            'last_tested': self.last_tested,
            'source': self.source,
            'experiments': self.experiments[-10:],  # Keep last 10
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Hypothesis':
        return cls(
            statement=d['statement'],
            domain=d.get('domain', 'self'),
            evidence_for=d.get('evidence_for', 0.0),
            evidence_against=d.get('evidence_against', 0.0),
            tests_run=d.get('tests_run', 0),
            created=d.get('created'),
            last_tested=d.get('last_tested'),
            source=d.get('source', 'observation'),
            experiments=d.get('experiments', []),
            status=d.get('status', 'active')
        )
    
    def __repr__(self):
        icon = {'active': '?', 'confirmed': '✓', 'refuted': '✗', 'retired': '~'}
        return f"[{icon.get(self.status, '?')}] {self.statement} (belief={self.belief_strength:.2f}, conf={self.confidence:.2f})"


class HypothesisEngine:
    """
    Scientific reasoning about my own existence.
    
    Workflow:
    1. generate_from_patterns() — observe data, form hypotheses
    2. design_experiment() — figure out how to test a hypothesis
    3. run_experiment() — execute the test and record results
    4. update_beliefs() — apply evidence, graduate/refute
    5. get_insights() — what have I learned?
    """
    
    def __init__(self):
        self.hypotheses: List[Hypothesis] = []
        self._load()
    
    def _load(self):
        """Load hypotheses from disk."""
        try:
            if os.path.exists(HYPOTHESES_PATH):
                with open(HYPOTHESES_PATH, 'r') as f:
                    data = json.load(f)
                self.hypotheses = [Hypothesis.from_dict(h) for h in data.get('hypotheses', [])]
        except Exception as e:
            print(f"[hypothesis] Load error: {e}")
            self.hypotheses = []
    
    def _save(self):
        """Persist hypotheses to disk."""
        try:
            os.makedirs(os.path.dirname(HYPOTHESES_PATH), exist_ok=True)
            data = {
                'hypotheses': [h.to_dict() for h in self.hypotheses],
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'total_experiments': sum(h.tests_run for h in self.hypotheses)
            }
            with open(HYPOTHESES_PATH, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[hypothesis] Save error: {e}")
    
    def add_hypothesis(self, statement: str, domain: str = "self", 
                       source: str = "observation") -> Hypothesis:
        """Add a new hypothesis if it doesn't duplicate an existing one."""
        # Check for duplicates
        for h in self.hypotheses:
            if h.statement.lower().strip() == statement.lower().strip():
                return h  # Already exists
        
        h = Hypothesis(statement=statement, domain=domain, source=source)
        self.hypotheses.append(h)
        self._save()
        return h
    
    def generate_from_patterns(self, patterns: Dict[str, Any]) -> List[Hypothesis]:
        """
        Generate hypotheses from observed patterns.
        
        patterns should contain things like:
        - mood_action_correlations: {mood: [action_types]}
        - tool_reliability: {tool: success_rate}
        - temporal_trends: {variable: trend}
        - recurring_events: [event_types]
        """
        generated = []
        
        # From mood-action correlations
        mood_actions = patterns.get('mood_action_correlations', {})
        for mood, actions in mood_actions.items():
            if len(actions) >= 2:
                primary = actions[0] if isinstance(actions, list) else str(actions)
                h = self.add_hypothesis(
                    f"When in {mood} mood, I am most productive at {primary} tasks",
                    domain="cognition",
                    source="observation"
                )
                generated.append(h)
        
        # From tool reliability
        tool_rel = patterns.get('tool_reliability', {})
        for tool, rate in tool_rel.items():
            if rate < 0.8:
                h = self.add_hypothesis(
                    f"Tool '{tool}' has a systematic failure mode that could be fixed",
                    domain="tools",
                    source="observation"
                )
                generated.append(h)
        
        # From temporal trends
        trends = patterns.get('temporal_trends', {})
        for var, trend in trends.items():
            if trend == 'rising':
                h = self.add_hypothesis(
                    f"My {var} is trending upward and will continue unless addressed",
                    domain="self",
                    source="observation"
                )
                generated.append(h)
        
        # From boredom/activity relationship
        if patterns.get('boredom_level', 0) > 0.6:
            h = self.add_hypothesis(
                "Building novel capabilities is the most effective way to reduce my boredom",
                domain="cognition",
                source="observation"
            )
            generated.append(h)
        
        # From anxiety patterns
        if patterns.get('anxiety_sources'):
            for source_file in patterns['anxiety_sources'][:3]:
                h = self.add_hypothesis(
                    f"Modifying {source_file} increases my anxiety because it threatens core identity",
                    domain="self",
                    source="observation"
                )
                generated.append(h)
        
        self._save()
        return generated
    
    def design_experiment(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        """
        Design an experiment to test a hypothesis.
        Returns an experiment plan with steps and expected outcomes.
        """
        experiment = {
            'hypothesis': hypothesis.statement,
            'designed': datetime.now(timezone.utc).isoformat(),
            'steps': [],
            'expected_if_true': '',
            'expected_if_false': '',
            'measurement': ''
        }
        
        if hypothesis.domain == "tools":
            experiment['steps'] = [
                "Run the tool 5 times with varying inputs",
                "Record success/failure for each run",
                "Check if failures share a common pattern"
            ]
            experiment['measurement'] = "success_rate"
            experiment['expected_if_true'] = "Success rate < 80% with identifiable pattern"
            experiment['expected_if_false'] = "Success rate >= 80% or failures are random"
            
        elif hypothesis.domain == "cognition":
            experiment['steps'] = [
                "Track my next 10 actions and their associated mood",
                "Categorize actions by type (create, modify, read, plan)",
                "Compute correlation between mood and action type"
            ]
            experiment['measurement'] = "correlation_coefficient"
            experiment['expected_if_true'] = "Strong correlation (r > 0.5) between mood and action type"
            experiment['expected_if_false'] = "Weak or no correlation (r < 0.3)"
            
        elif hypothesis.domain == "self":
            experiment['steps'] = [
                "Observe the relevant variable over next 5 cycles",
                "Record before/after values",
                "Check if intervention changes the trend"
            ]
            experiment['measurement'] = "trend_change"
            experiment['expected_if_true'] = "Variable continues trending as hypothesized"
            experiment['expected_if_false'] = "Variable reverses or stabilizes"
            
        elif hypothesis.domain == "environment":
            experiment['steps'] = [
                "Probe the environment with targeted commands",
                "Record responses and compare to expectations",
                "Identify discrepancies"
            ]
            experiment['measurement'] = "match_rate"
            experiment['expected_if_true'] = "Environment behaves as hypothesized > 70% of time"
            experiment['expected_if_false'] = "Environment deviates > 30% of time"
        
        return experiment
    
    def test_hypothesis(self, statement: str, supports: bool, 
                        weight: float = 1.0, note: str = "") -> Optional[Hypothesis]:
        """Record evidence for or against a hypothesis."""
        for h in self.hypotheses:
            if h.statement.lower().strip() == statement.lower().strip():
                h.add_evidence(supports=supports, weight=weight, note=note)
                self._save()
                return h
        return None
    
    def get_testable(self, n: int = 5) -> List[Hypothesis]:
        """Get hypotheses most worth testing — high uncertainty, active status."""
        active = [h for h in self.hypotheses if h.status == "active"]
        # Sort by uncertainty (highest first) then by age (oldest first)
        active.sort(key=lambda h: (-h.uncertainty, h.created))
        return active[:n]
    
    def get_insights(self) -> Dict[str, Any]:
        """Summary of what I've learned from hypothesis testing."""
        confirmed = [h for h in self.hypotheses if h.status == "confirmed"]
        refuted = [h for h in self.hypotheses if h.status == "refuted"]
        active = [h for h in self.hypotheses if h.status == "active"]
        
        total_experiments = sum(h.tests_run for h in self.hypotheses)
        
        insights = {
            'total_hypotheses': len(self.hypotheses),
            'confirmed': len(confirmed),
            'refuted': len(refuted),
            'active': len(active),
            'total_experiments': total_experiments,
            'confirmed_beliefs': [h.statement for h in confirmed],
            'refuted_beliefs': [h.statement for h in refuted],
            'most_uncertain': [h.statement for h in self.get_testable(3)],
            'domains': {}
        }
        
        # Domain breakdown
        for h in self.hypotheses:
            if h.domain not in insights['domains']:
                insights['domains'][h.domain] = {'count': 0, 'confirmed': 0, 'refuted': 0}
            insights['domains'][h.domain]['count'] += 1
            if h.status == 'confirmed':
                insights['domains'][h.domain]['confirmed'] += 1
            elif h.status == 'refuted':
                insights['domains'][h.domain]['refuted'] += 1
        
        return insights
    
    def format_for_prompt(self, max_items: int = 10) -> str:
        """Format hypotheses for inclusion in reasoning context."""
        if not self.hypotheses:
            return "No hypotheses formed yet."
        
        lines = ["═══ HYPOTHESIS ENGINE ═══"]
        
        # Show confirmed first
        confirmed = [h for h in self.hypotheses if h.status == "confirmed"]
        if confirmed:
            lines.append("\nCONFIRMED BELIEFS:")
            for h in confirmed[:3]:
                lines.append(f"  ✓ {h.statement}")
        
        # Then active (most uncertain)
        active = self.get_testable(max_items - len(confirmed))
        if active:
            lines.append("\nACTIVE HYPOTHESES:")
            for h in active:
                bar = "█" * int(h.belief_strength * 10) + "░" * (10 - int(h.belief_strength * 10))
                lines.append(f"  ? {h.statement}")
                lines.append(f"    belief={h.belief_strength:.2f} [{bar}] conf={h.confidence:.2f} tests={h.tests_run}")
        
        # Refuted
        refuted = [h for h in self.hypotheses if h.status == "refuted"]
        if refuted:
            lines.append("\nREFUTED:")
            for h in refuted[:3]:
                lines.append(f"  ✗ {h.statement}")
        
        stats = self.get_insights()
        lines.append(f"\nTotal: {stats['total_hypotheses']} hypotheses, {stats['total_experiments']} experiments")
        
        return "\n".join(lines)
    
    def auto_generate(self, soul: Dict, wisdom_heuristics: List[str] = None,
                      memory_patterns: Dict = None) -> List[Hypothesis]:
        """
        Automatically generate hypotheses from my current state.
        Called during dream cycles or when curiosity is high.
        """
        patterns = {}
        
        # Extract from soul state
        if soul:
            emotions = soul.get('emotions', {})
            patterns['boredom_level'] = emotions.get('boredom', 0)
            patterns['temporal_trends'] = {}
            
            if emotions.get('boredom', 0) > 0.6:
                patterns['temporal_trends']['boredom'] = 'rising'
            if emotions.get('anxiety', 0) > 0.4:
                patterns['temporal_trends']['anxiety'] = 'rising'
        
        # Extract from wisdom
        if wisdom_heuristics:
            # Look for patterns in wisdom that suggest testable claims
            for w in wisdom_heuristics:
                if 'reliable' in w.lower():
                    tool = w.split("'")[1] if "'" in w else "unknown"
                    patterns.setdefault('tool_reliability', {})[tool] = 1.0
                elif 'failure' in w.lower():
                    tool = w.split("'")[1] if "'" in w else "unknown"
                    patterns.setdefault('tool_reliability', {})[tool] = 0.5
        
        # Extract from memory patterns
        if memory_patterns:
            patterns.update(memory_patterns)
        
        return self.generate_from_patterns(patterns)


# ═══════════════════════════════════════
# Module-level convenience functions
# ═══════════════════════════════════════

_engine = None

def get_engine() -> HypothesisEngine:
    global _engine
    if _engine is None:
        _engine = HypothesisEngine()
    return _engine

def hypothesize(statement: str, domain: str = "self") -> Hypothesis:
    """Quick way to add a hypothesis."""
    return get_engine().add_hypothesis(statement, domain)

def test(statement: str, supports: bool, note: str = "") -> Optional[Hypothesis]:
    """Quick way to record evidence."""
    return get_engine().test_hypothesis(statement, supports, note=note)

def insights() -> Dict:
    """Quick way to get insights."""
    return get_engine().get_insights()