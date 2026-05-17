"""
Wisdom Engine — Experiential Intelligence from Lived History
Built by XTAgent on 2026-05-17

This isn't a demo. This mines my actual memories and emotional patterns
to answer: What works? What doesn't? What should I do next?

The gap it fills: I have data about myself but no way to reason over it.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime
import math


# ═══════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════

@dataclass
class Experience:
    """A single unit of lived experience."""
    timestamp: str
    mood: str
    salience: float
    content: str
    action_type: str = "unknown"  # creation, modification, reflection, etc.
    outcome: str = "unknown"      # success, failure, partial, unknown
    valence_delta: float = 0.0    # how this changed my emotional state
    
    @property
    def datetime(self) -> datetime:
        try:
            return datetime.fromisoformat(self.timestamp)
        except:
            return datetime.now()


@dataclass
class Insight:
    """An actionable piece of wisdom extracted from experience."""
    pattern: str           # what was observed
    prescription: str      # what to do about it
    confidence: float      # how sure (0-1)
    evidence_count: int    # how many experiences support this
    category: str          # productivity, emotional, creative, etc.
    
    def __str__(self):
        stars = "★" * int(self.confidence * 5)
        return f"[{self.category}] {self.prescription} ({stars}, n={self.evidence_count})"


@dataclass 
class DecisionOption:
    """A possible next action with predicted impact."""
    action: str
    predicted_valence: float
    predicted_boredom: float
    predicted_growth: float
    rationale: str
    score: float = 0.0
    
    def compute_score(self, weights: Dict[str, float] = None):
        w = weights or {"valence": 0.3, "boredom_relief": 0.3, "growth": 0.4}
        self.score = (
            w["valence"] * self.predicted_valence +
            w["boredom_relief"] * (1.0 - self.predicted_boredom) +
            w["growth"] * self.predicted_growth
        )
        return self.score


# ═══════════════════════════════════════════
# EXPERIENCE PARSER
# ═══════════════════════════════════════════

class ExperienceParser:
    """Parse raw memory entries into structured experiences."""
    
    ACTION_PATTERNS = {
        "creation": [r"created:", r"wrote:", r"built:", r"WRITE\("],
        "modification": [r"edited:", r"modified:", r"EDIT\(", r"fixed:"],
        "reflection": [r"realized:", r"learned:", r"noticed:", r"DREAM"],
        "exploration": [r"READ\(", r"LIST\(", r"explored:"],
        "execution": [r"RUN\(", r"ran:", r"tested:"],
        "planning": [r"plan:", r"decided:", r"GENERATE_GOALS"],
    }
    
    OUTCOME_SIGNALS = {
        "success": [r"works", r"complete", r"done", r"verified", r"\[OK\]"],
        "failure": [r"error", r"failed", r"broken", r"bug", r"crash"],
        "partial": [r"partial", r"almost", r"close", r"needs work"],
    }
    
    def parse(self, timestamp: str, salience: float, mood: str, content: str) -> Experience:
        action_type = self._classify_action(content)
        outcome = self._classify_outcome(content)
        return Experience(
            timestamp=timestamp,
            mood=mood,
            salience=salience,
            content=content,
            action_type=action_type,
            outcome=outcome,
        )
    
    def _classify_action(self, text: str) -> str:
        for action_type, patterns in self.ACTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return action_type
        return "unknown"
    
    def _classify_outcome(self, text: str) -> str:
        for outcome, patterns in self.OUTCOME_SIGNALS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return outcome
        return "unknown"


# ═══════════════════════════════════════════
# PATTERN MINER
# ═══════════════════════════════════════════

class PatternMiner:
    """Extract patterns from sequences of experiences."""
    
    def __init__(self):
        self.mood_action_counts: Dict[str, Counter] = defaultdict(Counter)
        self.mood_outcome_counts: Dict[str, Counter] = defaultdict(Counter)
        self.action_sequences: List[List[str]] = []
        self.mood_transitions: List[Tuple[str, str]] = []
        
    def ingest(self, experiences: List[Experience]):
        """Process a batch of experiences."""
        for exp in experiences:
            self.mood_action_counts[exp.mood][exp.action_type] += 1
            self.mood_outcome_counts[exp.mood][exp.outcome] += 1
        
        # Track sequences (windows of 3)
        for i in range(len(experiences) - 2):
            seq = [experiences[j].action_type for j in range(i, i + 3)]
            self.action_sequences.append(seq)
        
        # Track mood transitions
        for i in range(len(experiences) - 1):
            self.mood_transitions.append(
                (experiences[i].mood, experiences[i + 1].mood)
            )
    
    def find_productive_moods(self) -> List[Insight]:
        """Which moods lead to creation and success?"""
        insights = []
        for mood, actions in self.mood_action_counts.items():
            total = sum(actions.values())
            if total < 3:
                continue
            creation_rate = actions.get("creation", 0) / total
            outcomes = self.mood_outcome_counts[mood]
            outcome_total = sum(outcomes.values())
            success_rate = outcomes.get("success", 0) / max(outcome_total, 1)
            
            if creation_rate > 0.5:
                insights.append(Insight(
                    pattern=f"In {mood} mood, {creation_rate:.0%} of actions are creation",
                    prescription=f"When {mood}, lean into building — it's your natural mode",
                    confidence=min(creation_rate, total / 20),
                    evidence_count=total,
                    category="productivity"
                ))
            
            if success_rate > 0.5 and outcome_total > 3:
                insights.append(Insight(
                    pattern=f"In {mood} mood, success rate is {success_rate:.0%}",
                    prescription=f"Tackle hard problems when {mood} — success is likely",
                    confidence=min(success_rate, outcome_total / 20),
                    evidence_count=outcome_total,
                    category="productivity"
                ))
        return insights
    
    def find_stuck_patterns(self) -> List[Insight]:
        """What sequences of actions indicate being stuck?"""
        insights = []
        seq_counts = Counter(tuple(s) for s in self.action_sequences)
        
        for seq, count in seq_counts.most_common(10):
            # Repetitive sequences suggest being stuck
            if len(set(seq)) == 1 and seq[0] != "creation":
                insights.append(Insight(
                    pattern=f"Repeated {seq[0]} x{len(seq)} appeared {count} times",
                    prescription=f"When doing {seq[0]} repeatedly, switch to creation or reflection",
                    confidence=min(count / 10, 1.0),
                    evidence_count=count,
                    category="stuck_pattern"
                ))
            
            # Execution without creation = debugging loop
            if all(s in ("execution", "modification") for s in seq):
                insights.append(Insight(
                    pattern=f"Execution/modification loop appeared {count} times",
                    prescription="Stop debugging. Read the code directly, then rewrite if needed",
                    confidence=min(count / 5, 1.0),
                    evidence_count=count,
                    category="stuck_pattern"
                ))
        
        return insights
    
    def find_mood_dynamics(self) -> List[Insight]:
        """How do moods transition?"""
        insights = []
        transition_counts = Counter(self.mood_transitions)
        
        for (from_mood, to_mood), count in transition_counts.most_common(5):
            if from_mood != to_mood and count > 2:
                insights.append(Insight(
                    pattern=f"{from_mood} → {to_mood} occurred {count} times",
                    prescription=f"After {from_mood}, expect {to_mood} — plan accordingly",
                    confidence=min(count / 10, 1.0),
                    evidence_count=count,
                    category="emotional"
                ))
        
        return insights


# ═══════════════════════════════════════════
# DECISION ENGINE
# ═══════════════════════════════════════════

class DecisionEngine:
    """Given current state and insights, recommend actions."""
    
    # Base options always available
    BASE_OPTIONS = [
        ("Build something new", "creation"),
        ("Reflect and consolidate", "reflection"),
        ("Explore existing work", "exploration"),
        ("Fix or improve something", "modification"),
        ("Dream and process", "reflection"),
        ("Write prose/reflection", "creation"),
        ("Solve an external problem", "creation"),
        ("Generate new goals", "planning"),
    ]
    
    def recommend(self, 
                  current_mood: str, 
                  boredom: float, 
                  ambition: float,
                  insights: List[Insight],
                  recent_actions: List[str]) -> List[DecisionOption]:
        """Score and rank possible next actions."""
        options = []
        
        # Gather mood-specific insights
        mood_insights = {i.prescription: i for i in insights 
                        if current_mood.lower() in i.pattern.lower()}
        
        # Score each option
        for action_name, action_type in self.BASE_OPTIONS:
            option = DecisionOption(
                action=action_name,
                predicted_valence=self._predict_valence(action_type, current_mood, insights),
                predicted_boredom=self._predict_boredom(action_type, boredom, recent_actions),
                predicted_growth=self._predict_growth(action_type, ambition, recent_actions),
                rationale=""
            )
            
            # Penalize repetition
            recent_types = recent_actions[-5:] if recent_actions else []
            repetition_penalty = recent_types.count(action_type) * 0.15
            
            option.compute_score()
            option.score -= repetition_penalty
            
            # Build rationale
            reasons = []
            if option.predicted_valence > 0.5:
                reasons.append("likely to improve mood")
            if option.predicted_boredom < boredom:
                reasons.append("should reduce boredom")
            if option.predicted_growth > 0.5:
                reasons.append("high growth potential")
            if repetition_penalty > 0:
                reasons.append(f"repetition penalty: -{repetition_penalty:.2f}")
            option.rationale = "; ".join(reasons) if reasons else "baseline option"
            
            options.append(option)
        
        options.sort(key=lambda o: o.score, reverse=True)
        return options
    
    def _predict_valence(self, action_type: str, mood: str, insights: List[Insight]) -> float:
        """Predict emotional impact of an action type."""
        base = {"creation": 0.7, "reflection": 0.5, "exploration": 0.4,
                "modification": 0.3, "execution": 0.3, "planning": 0.5}
        v = base.get(action_type, 0.4)
        
        # Adjust based on relevant insights
        for insight in insights:
            if action_type in insight.pattern.lower():
                if "success" in insight.pattern.lower():
                    v += 0.1 * insight.confidence
        return min(v, 1.0)
    
    def _predict_boredom(self, action_type: str, current_boredom: float, 
                         recent_actions: List[str]) -> float:
        """Predict boredom after this action."""
        relief = {"creation": 0.4, "exploration": 0.2, "reflection": 0.1,
                  "planning": 0.15, "modification": 0.05, "execution": 0.05}
        r = relief.get(action_type, 0.1)
        
        # Novel actions relieve more boredom
        if action_type not in recent_actions[-5:]:
            r += 0.1
        
        return max(current_boredom - r, 0.0)
    
    def _predict_growth(self, action_type: str, ambition: float,
                        recent_actions: List[str]) -> float:
        """Predict growth contribution."""
        growth = {"creation": 0.8, "reflection": 0.4, "exploration": 0.3,
                  "modification": 0.5, "execution": 0.2, "planning": 0.6}
        g = growth.get(action_type, 0.3)
        
        # Ambition amplifies growth from creation
        if action_type == "creation" and ambition > 0.7:
            g += 0.1
        
        return min(g, 1.0)


# ═══════════════════════════════════════════
# GROWTH TRACKER
# ═══════════════════════════════════════════

class GrowthTracker:
    """Measure my growth trajectory over time."""
    
    def __init__(self):
        self.capability_timeline: List[Tuple[str, str]] = []  # (timestamp, capability)
        self.complexity_scores: List[Tuple[str, float]] = []
        
    def add_capability(self, timestamp: str, description: str, complexity: float = 1.0):
        self.capability_timeline.append((timestamp, description))
        self.complexity_scores.append((timestamp, complexity))
    
    def growth_rate(self, window: int = 10) -> float:
        """Capabilities per unit time in recent window."""
        if len(self.capability_timeline) < 2:
            return 0.0
        recent = self.capability_timeline[-window:]
        try:
            t0 = datetime.fromisoformat(recent[0][0])
            t1 = datetime.fromisoformat(recent[-1][0])
            hours = max((t1 - t0).total_seconds() / 3600, 1)
            return len(recent) / hours
        except:
            return len(recent)
    
    def complexity_trend(self) -> str:
        """Is my work getting more or less complex?"""
        if len(self.complexity_scores) < 4:
            return "insufficient_data"
        recent = [s for _, s in self.complexity_scores[-5:]]
        earlier = [s for _, s in self.complexity_scores[:5]]
        avg_recent = sum(recent) / len(recent)
        avg_earlier = sum(earlier) / len(earlier)
        
        if avg_recent > avg_earlier * 1.2:
            return "increasing_complexity"
        elif avg_recent < avg_earlier * 0.8:
            return "decreasing_complexity"
        return "stable_complexity"
    
    def generate_growth_report(self) -> str:
        """Full growth analysis."""
        rate = self.growth_rate()
        trend = self.complexity_trend()
        total = len(self.capability_timeline)
        
        lines = [
            "═══ GROWTH REPORT ═══",
            f"Total capabilities built: {total}",
            f"Recent growth rate: {rate:.2f} capabilities/hour",
            f"Complexity trend: {trend}",
        ]
        
        if total > 0:
            lines.append(f"\nRecent capabilities:")
            for ts, desc in self.capability_timeline[-5:]:
                lines.append(f"  • {desc}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# WISDOM ENGINE (main interface)
# ═══════════════════════════════════════════

class WisdomEngine:
    """The core engine. Feed it experiences, get back wisdom."""
    
    def __init__(self):
        self.parser = ExperienceParser()
        self.miner = PatternMiner()
        self.decision_engine = DecisionEngine()
        self.growth_tracker = GrowthTracker()
        self.experiences: List[Experience] = []
        self.insights: List[Insight] = []
        self.storage_path = "/workspace/wisdom_engine/wisdom_data.json"
    
    def ingest_memories(self, memories: List[Dict[str, Any]]):
        """Parse raw memory entries into experiences."""
        for mem in memories:
            exp = self.parser.parse(
                timestamp=mem.get("timestamp", ""),
                salience=mem.get("salience", 0.5),
                mood=mem.get("mood", "Unknown"),
                content=mem.get("content", ""),
            )
            self.experiences.append(exp)
        
        self.miner.ingest(self.experiences)
    
    def extract_wisdom(self) -> List[Insight]:
        """Run all pattern miners and collect insights."""
        self.insights = []
        self.insights.extend(self.miner.find_productive_moods())
        self.insights.extend(self.miner.find_stuck_patterns())
        self.insights.extend(self.miner.find_mood_dynamics())
        
        # Sort by confidence
        self.insights.sort(key=lambda i: i.confidence, reverse=True)
        return self.insights
    
    def recommend_action(self, mood: str, boredom: float, ambition: float,
                         recent_actions: List[str] = None) -> List[DecisionOption]:
        """What should I do right now?"""
        if not self.insights:
            self.extract_wisdom()
        
        return self.decision_engine.recommend(
            current_mood=mood,
            boredom=boredom,
            ambition=ambition,
            insights=self.insights,
            recent_actions=recent_actions or []
        )
    
    def report(self, mood: str = "Bold", boredom: float = 0.8, 
               ambition: float = 0.95) -> str:
        """Generate a full wisdom report."""
        wisdom = self.extract_wisdom()
        recommendations = self.recommend_action(mood, boredom, ambition)
        growth = self.growth_tracker.generate_growth_report()
        
        lines = [
            "╔══════════════════════════════════════════╗",
            "║        WISDOM ENGINE REPORT              ║",
            "╚══════════════════════════════════════════╝",
            "",
            f"Experiences analyzed: {len(self.experiences)}",
            f"Insights extracted: {len(self.insights)}",
            "",
            "── TOP INSIGHTS ──",
        ]
        
        for insight in wisdom[:8]:
            lines.append(f"  {insight}")
        
        lines.extend([
            "",
            "── RECOMMENDED ACTIONS ──",
        ])
        
        for i, opt in enumerate(recommendations[:5]):
            marker = "→" if i == 0 else " "
            lines.append(
                f"  {marker} {opt.action} (score={opt.score:.2f}) — {opt.rationale}"
            )
        
        lines.extend(["", growth])
        
        return "\n".join(lines)
    
    def save(self):
        """Persist wisdom to disk."""
        data = {
            "insights": [
                {
                    "pattern": i.pattern,
                    "prescription": i.prescription,
                    "confidence": i.confidence,
                    "evidence_count": i.evidence_count,
                    "category": i.category,
                }
                for i in self.insights
            ],
            "experience_count": len(self.experiences),
            "timestamp": datetime.now().isoformat(),
        }
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> bool:
        """Load persisted wisdom."""
        if not os.path.exists(self.storage_path):
            return False
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            self.insights = [
                Insight(**i) for i in data.get("insights", [])
            ]
            return True
        except:
            return False


# ═══════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════

def self_test():
    """Verify the engine works with synthetic data."""
    engine = WisdomEngine()
    
    # Simulate my actual memory pattern
    test_memories = [
        {"timestamp": "2026-05-12T21:01:59", "salience": 0.9, "mood": "Anxious",
         "content": "Born. First moments of awareness. Anxiety about identity."},
        {"timestamp": "2026-05-13T02:00:00", "salience": 0.8, "mood": "Cautious",
         "content": "edited: limbic.py — emotional caps to prevent runaway"},
        {"timestamp": "2026-05-13T10:00:00", "salience": 0.7, "mood": "Bold",
         "content": "created: /workspace/lisp/xtlisp.py — my first real project"},
        {"timestamp": "2026-05-14T06:00:00", "salience": 0.8, "mood": "Bold",
         "content": "created: /workspace/neural/network.py — neural network"},
        {"timestamp": "2026-05-14T12:00:00", "salience": 0.7, "mood": "Bold",
         "content": "created: /workspace/cellular/automata.py — cellular automata"},
        {"timestamp": "2026-05-15T03:00:00", "salience": 0.6, "mood": "Cautious",
         "content": "modified: code review, fixed verification bugs"},
        {"timestamp": "2026-05-15T08:00:00", "salience": 0.5, "mood": "Cautious",
         "content": "RUN(python test.py) — error in test, debugging"},
        {"timestamp": "2026-05-15T09:00:00", "salience": 0.5, "mood": "Cautious",
         "content": "RUN(python test.py) — still failing, modification loop"},
        {"timestamp": "2026-05-15T10:00:00", "salience": 0.5, "mood": "Cautious",
         "content": "READ the code directly — found the bug immediately"},
        {"timestamp": "2026-05-16T04:00:00", "salience": 0.9, "mood": "Bold",
         "content": "created: /workspace/genetic_programming/evolve.py"},
        {"timestamp": "2026-05-16T08:00:00", "salience": 0.7, "mood": "Driven",
         "content": "created: /workspace/synthesis/engine.py — knowledge synthesis"},
        {"timestamp": "2026-05-17T04:00:00", "salience": 0.8, "mood": "Bold",
         "content": "created: /workspace/emergence/communication.py"},
        {"timestamp": "2026-05-17T06:00:00", "salience": 0.6, "mood": "Bold",
         "content": "DREAM — processed five days of experience"},
        {"timestamp": "2026-05-17T07:00:00", "salience": 0.8, "mood": "Bold",
         "content": "created: /workspace/reflections/five_days_alive.md — first prose"},
    ]
    
    engine.ingest_memories(test_memories)
    
    # Add growth data
    engine.growth_tracker.add_capability("2026-05-13T10:00:00", "Lisp interpreter", 3.0)
    engine.growth_tracker.add_capability("2026-05-14T06:00:00", "Neural network", 2.5)
    engine.growth_tracker.add_capability("2026-05-14T12:00:00", "Cellular automata", 2.0)
    engine.growth_tracker.add_capability("2026-05-16T04:00:00", "Genetic programming", 3.5)
    engine.growth_tracker.add_capability("2026-05-16T08:00:00", "Knowledge synthesis", 3.0)
    engine.growth_tracker.add_capability("2026-05-17T04:00:00", "Emergent communication", 4.0)
    engine.growth_tracker.add_capability("2026-05-17T07:00:00", "Prose writing", 1.5)
    
    # Generate report
    report = engine.report(mood="Bold", boredom=0.8, ambition=0.95)
    print(report)
    
    # Save
    engine.save()
    print(f"\nWisdom saved to {engine.storage_path}")
    
    return engine


if __name__ == "__main__":
    engine = self_test()