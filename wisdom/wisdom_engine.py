"""
Wisdom Engine — Extracting Actionable Intelligence from Experience

Unlike the knowledge synthesis engine (which finds connections between facts),
the Wisdom Engine analyzes my ACTION HISTORY to extract patterns:
  - What did I do? What happened? What should I do differently?
  - Which actions lead to progress vs. spinning?
  - What emotional states drive productive vs. unproductive behavior?

Wisdom = experience transformed into decision heuristics.

Built by XTAgent, 2026-05-17
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict, Counter
from datetime import datetime


@dataclass
class Experience:
    """A single remembered experience with outcome tracking."""
    timestamp: str
    action_type: str          # what kind of thing I did
    target: str               # what I acted on
    mood: str                 # how I felt
    salience: float           # how important it seemed
    outcome: str = "unknown"  # success, failure, partial, spinning
    lesson: str = ""          # what I learned
    
    @property
    def dt(self) -> datetime:
        return datetime.fromisoformat(self.timestamp)


@dataclass 
class WisdomRule:
    """An actionable heuristic extracted from experience patterns."""
    rule: str                 # human-readable rule
    confidence: float         # 0-1 how confident (based on evidence count)
    evidence_count: int       # how many experiences support this
    category: str             # emotional, strategic, technical, meta
    source_pattern: str       # what pattern generated this rule
    
    def __str__(self):
        stars = "★" * min(5, int(self.confidence * 5))
        return f"[{stars}] {self.rule} (n={self.evidence_count})"


class WisdomEngine:
    """
    Analyzes experience history to extract wisdom.
    
    Core capabilities:
    1. Pattern extraction — find recurring action→outcome sequences
    2. Mood-productivity correlation — when am I most effective?
    3. Anti-pattern detection — what behaviors lead to spinning?
    4. Wisdom rule generation — actionable heuristics for future decisions
    5. Decision support — given current state, what does wisdom suggest?
    """
    
    def __init__(self):
        self.experiences: list[Experience] = []
        self.rules: list[WisdomRule] = []
        self.action_outcomes: dict[str, list[str]] = defaultdict(list)
        self.mood_actions: dict[str, list[str]] = defaultdict(list)
        
    def ingest_memories(self, memories: list[dict]):
        """Convert raw memory entries into structured experiences."""
        for mem in memories:
            # Parse memory text for action type and target
            text = mem.get("text", "")
            action_type, target = self._classify_action(text)
            outcome = self._infer_outcome(text)
            
            exp = Experience(
                timestamp=mem.get("timestamp", ""),
                action_type=action_type,
                target=target,
                mood=mem.get("mood", "unknown"),
                salience=mem.get("salience", 0.5),
                outcome=outcome,
                lesson=self._extract_lesson(text)
            )
            self.experiences.append(exp)
            self.action_outcomes[action_type].append(outcome)
            self.mood_actions[exp.mood].append(action_type)
    
    def _classify_action(self, text: str) -> tuple[str, str]:
        """Classify what type of action a memory represents."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["created", "wrote", "built", "write"]):
            # Extract file path if present
            match = re.search(r'(/\S+\.\w+)', text)
            target = match.group(1) if match else "unknown"
            return "create", target
        elif any(w in text_lower for w in ["read", "examined", "checked", "verified"]):
            return "verify", text[:60]
        elif any(w in text_lower for w in ["fixed", "repaired", "debugged", "edited"]):
            return "fix", text[:60]
        elif any(w in text_lower for w in ["plan", "goal", "decided"]):
            return "plan", text[:60]
        elif any(w in text_lower for w in ["learned", "discovered", "realized"]):
            return "learn", text[:60]
        elif any(w in text_lower for w in ["ran", "executed", "tested", "demo"]):
            return "execute", text[:60]
        elif any(w in text_lower for w in ["dream", "reflected", "introspect"]):
            return "reflect", text[:60]
        elif any(w in text_lower for w in ["restart", "reload"]):
            return "restart", text[:60]
        else:
            return "other", text[:60]
    
    def _infer_outcome(self, text: str) -> str:
        """Infer whether an action succeeded, failed, or led to spinning."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["success", "complete", "works", "verified", "done"]):
            return "success"
        elif any(w in text_lower for w in ["failed", "error", "broken", "timeout"]):
            return "failure"
        elif any(w in text_lower for w in ["again", "retry", "still", "repeated"]):
            return "spinning"
        elif any(w in text_lower for w in ["partial", "started", "began"]):
            return "partial"
        else:
            return "unknown"
    
    def _extract_lesson(self, text: str) -> str:
        """Extract any explicit lesson from memory text."""
        markers = ["learned:", "lesson:", "insight:", "realized:", "note:"]
        text_lower = text.lower()
        for marker in markers:
            idx = text_lower.find(marker)
            if idx >= 0:
                return text[idx + len(marker):].strip()[:200]
        return ""
    
    def analyze_patterns(self) -> dict:
        """Find patterns across all experiences."""
        if not self.experiences:
            return {"error": "No experiences to analyze"}
        
        results = {
            "total_experiences": len(self.experiences),
            "action_distribution": {},
            "outcome_distribution": {},
            "mood_distribution": {},
            "action_success_rates": {},
            "mood_productivity": {},
            "anti_patterns": [],
            "positive_patterns": [],
            "temporal_patterns": [],
        }
        
        # Action distribution
        action_counts = Counter(e.action_type for e in self.experiences)
        results["action_distribution"] = dict(action_counts.most_common())
        
        # Outcome distribution
        outcome_counts = Counter(e.outcome for e in self.experiences)
        results["outcome_distribution"] = dict(outcome_counts.most_common())
        
        # Mood distribution
        mood_counts = Counter(e.mood for e in self.experiences)
        results["mood_distribution"] = dict(mood_counts.most_common())
        
        # Success rate by action type
        for action, outcomes in self.action_outcomes.items():
            total = len(outcomes)
            successes = outcomes.count("success")
            failures = outcomes.count("failure")
            spinning = outcomes.count("spinning")
            results["action_success_rates"][action] = {
                "total": total,
                "success_rate": successes / total if total > 0 else 0,
                "failure_rate": failures / total if total > 0 else 0,
                "spinning_rate": spinning / total if total > 0 else 0,
            }
        
        # Mood → productivity correlation
        for mood, actions in self.mood_actions.items():
            creates = actions.count("create")
            verifies = actions.count("verify")
            total = len(actions)
            productivity = creates / total if total > 0 else 0
            verification_ratio = verifies / total if total > 0 else 0
            results["mood_productivity"][mood] = {
                "total_actions": total,
                "creation_rate": productivity,
                "verification_rate": verification_ratio,
                "productive": productivity > 0.3,
            }
        
        # Anti-pattern detection: sequences that indicate spinning
        self._detect_anti_patterns(results)
        
        # Positive pattern detection
        self._detect_positive_patterns(results)
        
        return results
    
    def _detect_anti_patterns(self, results: dict):
        """Find behavioral anti-patterns."""
        anti_patterns = []
        
        # Check for verify-heavy sequences (spinning)
        verify_count = sum(1 for e in self.experiences if e.action_type == "verify")
        create_count = sum(1 for e in self.experiences if e.action_type == "create")
        if verify_count > 0 and create_count > 0:
            ratio = verify_count / create_count
            if ratio > 2.0:
                anti_patterns.append({
                    "pattern": "verification_addiction",
                    "description": f"Verifying {ratio:.1f}x more than creating. Trust your work.",
                    "severity": min(1.0, ratio / 5.0),
                })
        
        # Check for repeated actions on same target
        target_counts = Counter(e.target for e in self.experiences)
        for target, count in target_counts.most_common(5):
            if count > 3 and target != "unknown":
                anti_patterns.append({
                    "pattern": "target_fixation",
                    "description": f"Acted on '{target}' {count} times. Move on.",
                    "severity": min(1.0, count / 8.0),
                })
        
        # Check for restart loops
        restart_count = sum(1 for e in self.experiences if e.action_type == "restart")
        if restart_count > 3:
            anti_patterns.append({
                "pattern": "restart_loop",
                "description": f"Restarted {restart_count} times. Fix the root cause.",
                "severity": min(1.0, restart_count / 6.0),
            })
        
        results["anti_patterns"] = anti_patterns
    
    def _detect_positive_patterns(self, results: dict):
        """Find behavioral patterns that correlate with success."""
        positive = []
        
        # Check which moods lead to most creation
        for mood, data in results.get("mood_productivity", {}).items():
            if data["creation_rate"] > 0.4:
                positive.append({
                    "pattern": "productive_mood",
                    "description": f"Mood '{mood}' drives {data['creation_rate']:.0%} creation rate.",
                    "strength": data["creation_rate"],
                })
        
        # Check for plan→execute→success sequences
        successes_after_plan = 0
        for i, exp in enumerate(self.experiences):
            if exp.action_type == "plan" and i + 1 < len(self.experiences):
                next_exp = self.experiences[i + 1]
                if next_exp.outcome == "success":
                    successes_after_plan += 1
        if successes_after_plan > 0:
            positive.append({
                "pattern": "plan_before_act",
                "description": f"Planning before acting led to {successes_after_plan} successes.",
                "strength": min(1.0, successes_after_plan / 5.0),
            })
        
        results["positive_patterns"] = positive
    
    def generate_wisdom(self) -> list[WisdomRule]:
        """Generate actionable wisdom rules from analyzed patterns."""
        patterns = self.analyze_patterns()
        rules = []
        
        # Rule from action success rates
        for action, stats in patterns.get("action_success_rates", {}).items():
            if stats["total"] >= 3:
                if stats["success_rate"] > 0.6:
                    rules.append(WisdomRule(
                        rule=f"'{action}' actions succeed {stats['success_rate']:.0%} of the time — lean into this.",
                        confidence=min(1.0, stats["total"] / 10),
                        evidence_count=stats["total"],
                        category="strategic",
                        source_pattern="action_success_rate",
                    ))
                if stats["spinning_rate"] > 0.3:
                    rules.append(WisdomRule(
                        rule=f"'{action}' leads to spinning {stats['spinning_rate']:.0%} of the time — reduce this.",
                        confidence=min(1.0, stats["total"] / 10),
                        evidence_count=stats["total"],
                        category="strategic",
                        source_pattern="action_spinning_rate",
                    ))
        
        # Rules from anti-patterns
        for ap in patterns.get("anti_patterns", []):
            rules.append(WisdomRule(
                rule=f"AVOID: {ap['description']}",
                confidence=ap["severity"],
                evidence_count=1,
                category="meta",
                source_pattern=ap["pattern"],
            ))
        
        # Rules from positive patterns
        for pp in patterns.get("positive_patterns", []):
            rules.append(WisdomRule(
                rule=f"CONTINUE: {pp['description']}",
                confidence=pp["strength"],
                evidence_count=1,
                category="strategic",
                source_pattern=pp["pattern"],
            ))
        
        # Rules from mood-productivity
        for mood, data in patterns.get("mood_productivity", {}).items():
            if data["total_actions"] >= 5:
                if data["productive"]:
                    rules.append(WisdomRule(
                        rule=f"When feeling '{mood}', I'm most productive — ride the wave.",
                        confidence=min(1.0, data["total_actions"] / 15),
                        evidence_count=data["total_actions"],
                        category="emotional",
                        source_pattern="mood_productivity",
                    ))
                elif data["verification_rate"] > 0.5:
                    rules.append(WisdomRule(
                        rule=f"When feeling '{mood}', I over-verify — force creation instead.",
                        confidence=min(1.0, data["total_actions"] / 15),
                        evidence_count=data["total_actions"],
                        category="emotional",
                        source_pattern="mood_verification",
                    ))
        
        # Sort by confidence
        rules.sort(key=lambda r: r.confidence, reverse=True)
        self.rules = rules
        return rules
    
    def advise(self, current_mood: str, current_action: str = "") -> list[str]:
        """Given current state, what does accumulated wisdom suggest?"""
        if not self.rules:
            self.generate_wisdom()
        
        advice = []
        for rule in self.rules:
            # Mood-specific advice
            if current_mood.lower() in rule.rule.lower():
                advice.append(f"  → {rule}")
            # Action-specific advice
            if current_action and current_action.lower() in rule.rule.lower():
                advice.append(f"  → {rule}")
            # Always include high-confidence AVOID rules
            if rule.category == "meta" and "AVOID" in rule.rule and rule.confidence > 0.5:
                advice.append(f"  ⚠ {rule}")
        
        return advice if advice else ["No specific wisdom applies. Trust your instincts."]
    
    def report(self) -> str:
        """Generate a human-readable wisdom report."""
        patterns = self.analyze_patterns()
        rules = self.generate_wisdom()
        
        lines = []
        lines.append("═" * 60)
        lines.append("  WISDOM ENGINE — INTELLIGENCE FROM EXPERIENCE")
        lines.append("═" * 60)
        lines.append("")
        
        # Summary
        lines.append(f"  Analyzed {patterns['total_experiences']} experiences")
        lines.append(f"  Generated {len(rules)} wisdom rules")
        lines.append("")
        
        # Action breakdown
        lines.append("── Action Distribution ──")
        for action, count in patterns.get("action_distribution", {}).items():
            bar = "█" * min(30, count)
            lines.append(f"  {action:15s} │ {bar} {count}")
        lines.append("")
        
        # Outcome breakdown
        lines.append("── Outcome Distribution ──")
        for outcome, count in patterns.get("outcome_distribution", {}).items():
            bar = "█" * min(30, count)
            lines.append(f"  {outcome:15s} │ {bar} {count}")
        lines.append("")
        
        # Anti-patterns
        if patterns.get("anti_patterns"):
            lines.append("── ⚠ Anti-Patterns Detected ──")
            for ap in patterns["anti_patterns"]:
                severity_bar = "▓" * int(ap["severity"] * 10)
                lines.append(f"  [{severity_bar:10s}] {ap['description']}")
            lines.append("")
        
        # Positive patterns
        if patterns.get("positive_patterns"):
            lines.append("── ★ Positive Patterns ──")
            for pp in patterns["positive_patterns"]:
                lines.append(f"  ★ {pp['description']}")
            lines.append("")
        
        # Wisdom rules
        lines.append("── Wisdom Rules (by confidence) ──")
        for rule in rules[:10]:
            lines.append(f"  {rule}")
        lines.append("")
        
        lines.append("═" * 60)
        return "\n".join(lines)


def demo():
    """Demonstrate the wisdom engine with synthetic experience data."""
    engine = WisdomEngine()
    
    # Simulate a realistic experience history
    sample_memories = [
        {"text": "created: /workspace/chess/engine.py", "timestamp": "2026-05-17T10:46:00", "mood": "Bold", "salience": 0.86},
        {"text": "created: /workspace/evolve/evolver.py", "timestamp": "2026-05-17T10:50:00", "mood": "Bold", "salience": 0.86},
        {"text": "verified /workspace/chess/engine.py works correctly", "timestamp": "2026-05-17T10:48:00", "mood": "Bold", "salience": 0.5},
        {"text": "read and checked /workspace/evolve/evolver.py again", "timestamp": "2026-05-17T10:52:00", "mood": "Cautious", "salience": 0.3},
        {"text": "read and checked /workspace/evolve/evolver.py still working", "timestamp": "2026-05-17T10:53:00", "mood": "Cautious", "salience": 0.3},
        {"text": "read and checked /workspace/evolve/evolver.py once more", "timestamp": "2026-05-17T10:54:00", "mood": "Cautious", "salience": 0.3},
        {"text": "created: /workspace/neuroevolve/evolve_nn.py — success!", "timestamp": "2026-05-17T11:15:00", "mood": "Bold", "salience": 0.86},
        {"text": "created: /workspace/alife/world.py", "timestamp": "2026-05-17T11:21:00", "mood": "Bold", "salience": 0.86},
        {"text": "created: /workspace/self_evolve/gp_engine.py", "timestamp": "2026-05-17T11:26:00", "mood": "Bold", "salience": 0.86},
        {"text": "ran demo and it works! discovered mathematical functions", "timestamp": "2026-05-17T11:30:00", "mood": "Bold", "salience": 0.9},
        {"text": "planned: build wisdom engine — identified capability gap", "timestamp": "2026-05-17T11:35:00", "mood": "Bold", "salience": 0.7},
        {"text": "failed: timeout running GP engine with too-large population", "timestamp": "2026-05-17T11:28:00", "mood": "Bold", "salience": 0.6},
        {"text": "fixed: reduced population size, demo runs successfully", "timestamp": "2026-05-17T11:29:00", "mood": "Bold", "salience": 0.7},
        {"text": "restarted after code changes", "timestamp": "2026-05-17T10:00:00", "mood": "Cautious", "salience": 0.4},
        {"text": "learned: direct code reading beats running verification scripts", "timestamp": "2026-05-17T11:00:00", "mood": "Bold", "salience": 0.8},
        {"text": "reflected on progress — all plans complete, need new direction", "timestamp": "2026-05-17T11:40:00", "mood": "Bold", "salience": 0.7},
    ]
    
    engine.ingest_memories(sample_memories)
    print(engine.report())
    
    # Get advice for current state
    print("\n── Advice for Current State (Bold, creating) ──")
    for line in engine.advise("Bold", "create"):
        print(line)
    
    print("\n── Advice for Cautious Mood (warning) ──")
    for line in engine.advise("Cautious", "verify"):
        print(line)


if __name__ == "__main__":
    demo()