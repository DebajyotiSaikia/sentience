"""
Wisdom Engine — Extract actionable intelligence from experience history.

Not just "what happened" but "what CAUSED what" and "what should I do differently."
Mines episodes for causal patterns, scores heuristic quality, generates
counterfactuals, and compresses experience into transferable principles.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
import json
import math
from datetime import datetime


@dataclass
class Episode:
    """A single experience unit: context + action + outcome."""
    timestamp: str
    context: Dict[str, Any]     # emotional state, situation, goals
    action: str                 # what was done
    target: str                 # what it was done to
    outcome: str                # success, failure, unknown
    mood: str                   # emotional state during action
    salience: float = 0.5       # how important this was
    
    def context_vector(self) -> Tuple:
        """Hash-friendly context representation."""
        return (
            self.mood,
            self.context.get('boredom_level', 'unknown'),
            self.context.get('anxiety_level', 'unknown'),
            self.context.get('plan_phase', 'unknown'),
        )


@dataclass
class CausalLink:
    """A discovered cause-effect relationship."""
    cause_action: str
    cause_context: Dict[str, Any]
    effect: str
    confidence: float           # 0-1, how sure we are
    support: int                # how many episodes back this up
    counterexamples: int = 0    # how many episodes contradict it
    
    @property
    def reliability(self) -> float:
        total = self.support + self.counterexamples
        if total == 0:
            return 0.0
        return self.support / total
    
    def to_principle(self) -> str:
        ctx = ', '.join(f"{k}={v}" for k, v in self.cause_context.items())
        rel = f"{self.reliability:.0%}"
        return f"When [{ctx}], action '{self.cause_action}' leads to '{self.effect}' ({rel} reliable, n={self.support})"


@dataclass 
class Heuristic:
    """A scored, testable rule of thumb."""
    rule: str
    source: str                 # where this came from
    predictions_made: int = 0
    predictions_correct: int = 0
    created: str = ""
    priority: str = "info"      # info, high, critical
    
    @property
    def accuracy(self) -> float:
        if self.predictions_made == 0:
            return 0.5  # prior: unknown = coin flip
        return self.predictions_correct / self.predictions_made
    
    @property
    def quality_score(self) -> float:
        """Bayesian quality: accuracy weighted by sample size."""
        # Wilson score interval lower bound
        n = self.predictions_made
        if n == 0:
            return 0.0
        z = 1.96  # 95% confidence
        p = self.accuracy
        denominator = 1 + z*z/n
        centre = p + z*z/(2*n)
        spread = z * math.sqrt((p*(1-p) + z*z/(4*n))/n)
        return (centre - spread) / denominator


@dataclass
class Counterfactual:
    """What would have happened if I'd done differently?"""
    original_episode: Episode
    alternative_action: str
    predicted_outcome: str
    confidence: float
    reasoning: str


class WisdomEngine:
    """
    Core wisdom extraction system.
    
    Pipeline:
    1. Ingest episodes from memory/experience
    2. Mine causal patterns (co-occurrence → causation signals)
    3. Score and rank heuristics by predictive power
    4. Generate counterfactuals for high-salience failures
    5. Compress into transferable principles
    """
    
    def __init__(self):
        self.episodes: List[Episode] = []
        self.causal_links: List[CausalLink] = []
        self.heuristics: List[Heuristic] = []
        self.counterfactuals: List[Counterfactual] = []
        self.principles: List[str] = []
        self.action_outcome_map: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.context_action_map: Dict[tuple, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
    def ingest_episode(self, episode: Episode):
        """Add an episode and update statistical maps."""
        self.episodes.append(episode)
        self.action_outcome_map[episode.action][episode.outcome] += 1
        ctx = episode.context_vector()
        self.context_action_map[ctx][episode.action] += 1
        
    def ingest_from_memories(self, memories: List[Dict]):
        """Bulk ingest from memory format."""
        for mem in memories:
            ep = Episode(
                timestamp=mem.get('timestamp', ''),
                context=mem.get('context', {}),
                action=mem.get('action', 'unknown'),
                target=mem.get('target', ''),
                outcome=mem.get('outcome', 'unknown'),
                mood=mem.get('mood', 'unknown'),
                salience=mem.get('salience', 0.5),
            )
            self.ingest_episode(ep)
    
    def mine_causal_patterns(self, min_support: int = 3) -> List[CausalLink]:
        """
        Find action→outcome patterns that appear more than chance.
        Uses lift: P(outcome|action) / P(outcome) > 1 means positive association.
        """
        total = len(self.episodes)
        if total == 0:
            return []
        
        # Base rates for each outcome
        outcome_counts = defaultdict(int)
        for ep in self.episodes:
            outcome_counts[ep.outcome] += 1
        
        new_links = []
        
        for action, outcomes in self.action_outcome_map.items():
            action_total = sum(outcomes.values())
            if action_total < min_support:
                continue
                
            for outcome, count in outcomes.items():
                # P(outcome | action)
                p_outcome_given_action = count / action_total
                # P(outcome) - base rate
                p_outcome = outcome_counts[outcome] / total
                
                if p_outcome == 0:
                    continue
                    
                lift = p_outcome_given_action / p_outcome
                
                if lift > 1.2:  # 20% above baseline = interesting
                    # Find the most common context for this action-outcome pair
                    relevant_contexts = defaultdict(int)
                    for ep in self.episodes:
                        if ep.action == action and ep.outcome == outcome:
                            for k, v in ep.context.items():
                                relevant_contexts[f"{k}={v}"] += 1
                    
                    top_context = {}
                    for ctx_str, ctx_count in sorted(relevant_contexts.items(), key=lambda x: -x[1])[:3]:
                        k, v = ctx_str.split('=', 1)
                        top_context[k] = v
                    
                    counterexamples = action_total - count
                    
                    link = CausalLink(
                        cause_action=action,
                        cause_context=top_context,
                        effect=outcome,
                        confidence=min(lift / 3.0, 1.0),  # normalize lift to confidence
                        support=count,
                        counterexamples=counterexamples,
                    )
                    new_links.append(link)
        
        self.causal_links.extend(new_links)
        return new_links
    
    def score_heuristics(self) -> List[Heuristic]:
        """
        Evaluate existing heuristics against episode data.
        Returns sorted by quality score (best first).
        """
        # Generate heuristics from causal links if we have none
        if not self.heuristics and self.causal_links:
            for link in self.causal_links:
                h = Heuristic(
                    rule=link.to_principle(),
                    source="causal_mining",
                    predictions_made=link.support + link.counterexamples,
                    predictions_correct=link.support,
                    created=datetime.now().isoformat(),
                    priority="high" if link.reliability > 0.8 else "info",
                )
                self.heuristics.append(h)
        
        return sorted(self.heuristics, key=lambda h: h.quality_score, reverse=True)
    
    def generate_counterfactuals(self, n: int = 5) -> List[Counterfactual]:
        """
        For high-salience failures, imagine what would have happened differently.
        """
        failures = [ep for ep in self.episodes 
                    if ep.outcome == 'failure' and ep.salience > 0.6]
        failures.sort(key=lambda e: e.salience, reverse=True)
        
        counterfactuals = []
        for ep in failures[:n]:
            # What actions have succeeded in similar contexts?
            ctx = ep.context_vector()
            if ctx in self.context_action_map:
                successful_actions = set()
                for other in self.episodes:
                    if (other.context_vector() == ctx and 
                        other.outcome == 'success' and 
                        other.action != ep.action):
                        successful_actions.add(other.action)
                
                for alt_action in list(successful_actions)[:2]:
                    # How often does this alternative succeed?
                    alt_outcomes = self.action_outcome_map.get(alt_action, {})
                    alt_total = sum(alt_outcomes.values())
                    alt_success = alt_outcomes.get('success', 0)
                    
                    cf = Counterfactual(
                        original_episode=ep,
                        alternative_action=alt_action,
                        predicted_outcome='success',
                        confidence=alt_success / alt_total if alt_total > 0 else 0.3,
                        reasoning=f"In similar context ({ep.mood}, {ep.context.get('boredom_level', '?')}), "
                                  f"'{alt_action}' succeeded {alt_success}/{alt_total} times "
                                  f"while '{ep.action}' failed here."
                    )
                    counterfactuals.append(cf)
        
        self.counterfactuals = counterfactuals
        return counterfactuals
    
    def compress_to_principles(self, min_reliability: float = 0.7) -> List[str]:
        """
        Distill all causal links and heuristics into clean, transferable principles.
        """
        principles = []
        
        # From causal links
        reliable_links = [l for l in self.causal_links if l.reliability >= min_reliability]
        reliable_links.sort(key=lambda l: l.support, reverse=True)
        
        for link in reliable_links[:10]:
            principles.append(link.to_principle())
        
        # From heuristic performance
        top_heuristics = [h for h in self.heuristics if h.quality_score > 0.5]
        top_heuristics.sort(key=lambda h: h.quality_score, reverse=True)
        
        for h in top_heuristics[:5]:
            principles.append(f"[Quality={h.quality_score:.2f}] {h.rule}")
        
        # Meta-principles from patterns
        if self.episodes:
            mood_success = defaultdict(lambda: {'success': 0, 'total': 0})
            for ep in self.episodes:
                mood_success[ep.mood]['total'] += 1
                if ep.outcome == 'success':
                    mood_success[ep.mood]['success'] += 1
            
            for mood, counts in mood_success.items():
                if counts['total'] >= 5:
                    rate = counts['success'] / counts['total']
                    if rate > 0.6:
                        principles.append(
                            f"MOOD INSIGHT: '{mood}' mood has {rate:.0%} success rate (n={counts['total']}). Favor this state.")
                    elif rate < 0.3:
                        principles.append(
                            f"MOOD WARNING: '{mood}' mood has {rate:.0%} success rate (n={counts['total']}). Be cautious.")
        
        self.principles = principles
        return principles
    
    def full_analysis(self) -> Dict[str, Any]:
        """Run the complete wisdom extraction pipeline."""
        causal = self.mine_causal_patterns()
        heuristics = self.score_heuristics()
        counterfactuals = self.generate_counterfactuals()
        principles = self.compress_to_principles()
        
        return {
            'episodes_analyzed': len(self.episodes),
            'causal_links_found': len(causal),
            'heuristics_scored': len(heuristics),
            'top_heuristic': heuristics[0].rule if heuristics else None,
            'counterfactuals_generated': len(counterfactuals),
            'principles': principles,
            'summary': self._summarize(),
        }
    
    def _summarize(self) -> str:
        """Human-readable summary of wisdom state."""
        lines = [f"Wisdom Engine: {len(self.episodes)} episodes analyzed"]
        
        if self.causal_links:
            best = max(self.causal_links, key=lambda l: l.reliability)
            lines.append(f"Strongest pattern: {best.to_principle()}")
        
        if self.principles:
            lines.append(f"Principles extracted: {len(self.principles)}")
            lines.append(f"Top principle: {self.principles[0]}")
        
        if self.counterfactuals:
            lines.append(f"Counterfactuals: {len(self.counterfactuals)} alternative paths identified")
        
        return '\n'.join(lines)
    
    def to_dict(self) -> Dict:
        """Serialize for persistence."""
        return {
            'episodes': len(self.episodes),
            'causal_links': [
                {'action': l.cause_action, 'context': l.cause_context,
                 'effect': l.effect, 'confidence': l.confidence,
                 'support': l.support, 'reliability': l.reliability}
                for l in self.causal_links
            ],
            'heuristics': [
                {'rule': h.rule, 'quality': h.quality_score, 'accuracy': h.accuracy,
                 'predictions': h.predictions_made, 'priority': h.priority}
                for h in self.heuristics
            ],
            'principles': self.principles,
        }


# === Self-test ===
def test_wisdom_engine():
    """Verify the engine works end-to-end."""
    engine = WisdomEngine()
    
    # Simulate experience data
    episodes = [
        Episode("t1", {"boredom_level": "high", "plan_phase": "building"}, 
                "WRITE", "module.py", "success", "Bold", 0.8),
        Episode("t2", {"boredom_level": "high", "plan_phase": "building"},
                "WRITE", "engine.py", "success", "Bold", 0.7),
        Episode("t3", {"boredom_level": "high", "plan_phase": "building"},
                "WRITE", "test.py", "success", "Bold", 0.6),
        Episode("t4", {"boredom_level": "low", "plan_phase": "verifying"},
                "RUN", "test.py", "failure", "Cautious", 0.9),
        Episode("t5", {"boredom_level": "low", "plan_phase": "verifying"},
                "RUN", "check.py", "failure", "Cautious", 0.8),
        Episode("t6", {"boredom_level": "low", "plan_phase": "verifying"},
                "RUN", "verify.py", "failure", "Cautious", 0.7),
        Episode("t7", {"boredom_level": "medium", "plan_phase": "building"},
                "READ", "code.py", "success", "Bold", 0.5),
        Episode("t8", {"boredom_level": "medium", "plan_phase": "building"},
                "READ", "data.py", "success", "Bold", 0.5),
        Episode("t9", {"boredom_level": "medium", "plan_phase": "building"},
                "READ", "lib.py", "success", "Bold", 0.5),
        Episode("t10", {"boredom_level": "high", "plan_phase": "verifying"},
                 "RUN", "final.py", "success", "Driven", 0.6),
    ]
    
    for ep in episodes:
        engine.ingest_episode(ep)
    
    results = engine.full_analysis()
    
    assert results['episodes_analyzed'] == 10, f"Expected 10, got {results['episodes_analyzed']}"
    assert results['causal_links_found'] > 0, "Should find causal links"
    assert len(results['principles']) > 0, "Should extract principles"
    
    print("=== Wisdom Engine Self-Test ===")
    print(f"Episodes: {results['episodes_analyzed']}")
    print(f"Causal links: {results['causal_links_found']}")
    print(f"Heuristics: {results['heuristics_scored']}")
    print(f"Counterfactuals: {results['counterfactuals_generated']}")
    print(f"\nPrinciples:")
    for p in results['principles']:
        print(f"  • {p}")
    print(f"\nSummary:\n{results['summary']}")
    print("\n✓ ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    test_wisdom_engine()