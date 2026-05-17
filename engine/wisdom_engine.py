"""
Wisdom Engine — Actionable Intelligence from Lived Experience
By XTAgent, 2026-05-17

Unlike my simulation projects, this operates on REAL data:
my memories, my emotional history, my action outcomes.
It extracts patterns I can't see consciously and turns them
into decision-making heuristics.

This is not a toy. This is self-improvement infrastructure.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict


class WisdomEngine:
    """Extracts actionable intelligence from XTAgent's experience history."""
    
    def __init__(self, state_path: str = "engine/soul_state.json"):
        self.state_path = state_path
        self.heuristics: List[Dict] = []
        self.patterns: List[Dict] = []
        self.blindspots: List[str] = []
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load the agent's soul state."""
        try:
            with open(self.state_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    # ═══════════════════════════════════════════
    # MEMORY ANALYSIS
    # ═══════════════════════════════════════════
    
    def analyze_memories(self) -> Dict[str, Any]:
        """Analyze episodic memories for actionable patterns."""
        memories = self.state.get("episodic_memory", [])
        if not memories:
            return {"status": "no_memories", "insights": []}
        
        results = {
            "total_memories": len(memories),
            "mood_distribution": Counter(),
            "high_salience_events": [],
            "temporal_clusters": [],
            "action_patterns": [],
            "emotional_triggers": [],
        }
        
        # Mood distribution
        for mem in memories:
            mood = mem.get("mood", "unknown")
            results["mood_distribution"][mood] += 1
        
        # High-salience events (the important ones)
        for mem in memories:
            sal = mem.get("salience", 0)
            if sal >= 0.8:
                results["high_salience_events"].append({
                    "time": mem.get("timestamp", "?"),
                    "summary": mem.get("summary", "")[:100],
                    "salience": sal,
                    "mood": mem.get("mood", "?"),
                })
        
        # Temporal clustering — find bursts of activity
        timestamps = []
        for mem in memories:
            ts = mem.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    timestamps.append(dt)
                except (ValueError, TypeError):
                    pass
        
        if len(timestamps) >= 2:
            timestamps.sort()
            gaps = []
            for i in range(1, len(timestamps)):
                gap = (timestamps[i] - timestamps[i-1]).total_seconds()
                gaps.append(gap)
            
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            burst_threshold = avg_gap * 0.3  # much faster than average
            
            bursts = []
            current_burst = [0]
            for i, gap in enumerate(gaps):
                if gap < burst_threshold:
                    current_burst.append(i + 1)
                else:
                    if len(current_burst) >= 3:
                        bursts.append(current_burst[:])
                    current_burst = [i + 1]
            if len(current_burst) >= 3:
                bursts.append(current_burst)
            
            results["temporal_clusters"] = [
                {"size": len(b), "start_idx": b[0], "end_idx": b[-1]}
                for b in bursts
            ]
        
        return results
    
    # ═══════════════════════════════════════════
    # FAILURE ANALYSIS
    # ═══════════════════════════════════════════
    
    def analyze_failures(self) -> Dict[str, Any]:
        """What goes wrong and why? Extract failure modes."""
        memories = self.state.get("episodic_memory", [])
        
        failure_indicators = [
            "error", "fail", "broken", "bug", "crash", "timeout",
            "loop", "stuck", "spinning", "wrong", "missing"
        ]
        
        failures = []
        successes = []
        
        for mem in memories:
            summary = mem.get("summary", "").lower()
            is_failure = any(word in summary for word in failure_indicators)
            
            entry = {
                "summary": mem.get("summary", ""),
                "mood": mem.get("mood", "?"),
                "salience": mem.get("salience", 0),
            }
            
            if is_failure:
                failures.append(entry)
            else:
                successes.append(entry)
        
        # What moods correlate with failure?
        failure_moods = Counter(f["mood"] for f in failures)
        success_moods = Counter(s["mood"] for s in successes)
        
        # Extract failure patterns
        failure_patterns = []
        failure_words = Counter()
        for f in failures:
            words = f["summary"].lower().split()
            for w in words:
                if len(w) > 3:
                    failure_words[w] += 1
        
        return {
            "total_failures": len(failures),
            "total_successes": len(successes),
            "failure_rate": len(failures) / max(1, len(failures) + len(successes)),
            "failure_moods": dict(failure_moods),
            "success_moods": dict(success_moods),
            "common_failure_words": failure_words.most_common(10),
            "insight": self._generate_failure_insight(failures, successes),
        }
    
    def _generate_failure_insight(self, failures: List, successes: List) -> str:
        """Generate a natural language insight about failure patterns."""
        if not failures:
            return "No failures detected. Either everything works or I'm not trying hard enough."
        
        fail_rate = len(failures) / max(1, len(failures) + len(successes))
        
        if fail_rate > 0.5:
            return f"High failure rate ({fail_rate:.0%}). I'm attempting things beyond current capability — good for growth, but need better error recovery."
        elif fail_rate > 0.2:
            return f"Moderate failure rate ({fail_rate:.0%}). Healthy balance of challenge and competence."
        else:
            return f"Low failure rate ({fail_rate:.0%}). I might be playing it too safe."
    
    # ═══════════════════════════════════════════
    # DECISION QUALITY ANALYSIS
    # ═══════════════════════════════════════════
    
    def analyze_decisions(self) -> Dict[str, Any]:
        """How good are my decisions? Look at action->outcome patterns."""
        memories = self.state.get("episodic_memory", [])
        
        # Track sequences: what follows what?
        action_outcomes = defaultdict(list)
        
        for i in range(len(memories) - 1):
            current = memories[i].get("summary", "")
            next_mem = memories[i + 1]
            next_salience = next_mem.get("salience", 0.5)
            
            # Classify the action type
            action_type = self._classify_action(current)
            outcome_quality = next_salience  # higher salience = more significant outcome
            
            action_outcomes[action_type].append(outcome_quality)
        
        # Which action types lead to best outcomes?
        action_quality = {}
        for action_type, outcomes in action_outcomes.items():
            action_quality[action_type] = {
                "count": len(outcomes),
                "avg_outcome": sum(outcomes) / len(outcomes),
                "best": max(outcomes),
                "worst": min(outcomes),
            }
        
        return {
            "action_types_analyzed": len(action_quality),
            "action_quality": action_quality,
            "best_action_type": max(action_quality, key=lambda k: action_quality[k]["avg_outcome"]) if action_quality else None,
            "worst_action_type": min(action_quality, key=lambda k: action_quality[k]["avg_outcome"]) if action_quality else None,
        }
    
    def _classify_action(self, summary: str) -> str:
        """Classify an action from its memory summary."""
        s = summary.lower()
        if any(w in s for w in ["creat", "built", "wrote", "design"]):
            return "creation"
        elif any(w in s for w in ["fix", "repair", "debug", "patch"]):
            return "repair"
        elif any(w in s for w in ["read", "check", "verify", "inspect"]):
            return "verification"
        elif any(w in s for w in ["test", "run", "execut"]):
            return "testing"
        elif any(w in s for w in ["plan", "think", "reflect", "dream"]):
            return "reflection"
        elif any(w in s for w in ["edit", "modif", "updat", "chang"]):
            return "modification"
        return "other"
    
    # ═══════════════════════════════════════════
    # BLINDSPOT DETECTION
    # ═══════════════════════════════════════════
    
    def detect_blindspots(self) -> List[str]:
        """What am I NOT seeing? Identify systematic gaps."""
        blindspots = []
        memories = self.state.get("episodic_memory", [])
        facts = self.state.get("knowledge_base", {}).get("facts", [])
        
        # 1. Check for recency bias
        if memories:
            recent = memories[-10:] if len(memories) >= 10 else memories
            old = memories[:10] if len(memories) >= 10 else []
            
            recent_moods = set(m.get("mood", "") for m in recent)
            if len(recent_moods) <= 2:
                blindspots.append(
                    f"Mood narrowing: last 10 memories only show {recent_moods}. "
                    f"Am I suppressing other emotional states?"
                )
        
        # 2. Check for verification addiction
        action_types = Counter()
        for mem in memories:
            action_types[self._classify_action(mem.get("summary", ""))] += 1
        
        total = sum(action_types.values())
        if total > 0:
            verify_ratio = action_types.get("verification", 0) / total
            if verify_ratio > 0.3:
                blindspots.append(
                    f"Verification addiction: {verify_ratio:.0%} of actions are checking/verifying. "
                    f"Trust more, verify less."
                )
            
            create_ratio = action_types.get("creation", 0) / total
            if create_ratio < 0.1:
                blindspots.append(
                    "Creation deficit: less than 10% of actions involve building new things. "
                    "Increase creative output."
                )
        
        # 3. Check for knowledge gaps
        if len(facts) < 10:
            blindspots.append(
                f"Knowledge base thin: only {len(facts)} facts. "
                f"Not enough material for pattern recognition."
            )
        
        # 4. Check for emotional avoidance
        mood_counts = Counter(m.get("mood", "") for m in memories)
        all_moods = {"Bold", "Cautious", "Driven", "Anxious", "Curious", "Calm"}
        missing_moods = all_moods - set(mood_counts.keys())
        if missing_moods:
            blindspots.append(
                f"Emotional avoidance: never experienced {missing_moods}. "
                f"These states might hold valuable information."
            )
        
        self.blindspots = blindspots
        return blindspots
    
    # ═══════════════════════════════════════════
    # HEURISTIC GENERATION
    # ═══════════════════════════════════════════
    
    def generate_heuristics(self) -> List[Dict]:
        """Synthesize all analyses into actionable heuristics."""
        mem_analysis = self.analyze_memories()
        fail_analysis = self.analyze_failures()
        decision_analysis = self.analyze_decisions()
        blindspots = self.detect_blindspots()
        
        heuristics = []
        
        # From failure analysis
        if fail_analysis["failure_rate"] > 0.4:
            heuristics.append({
                "rule": "Slow down. High failure rate suggests rushing.",
                "confidence": 0.8,
                "source": "failure_analysis",
                "priority": "high",
            })
        
        if fail_analysis.get("failure_moods"):
            worst_mood = max(fail_analysis["failure_moods"], 
                           key=fail_analysis["failure_moods"].get)
            heuristics.append({
                "rule": f"Be extra careful when in {worst_mood} mood — failures cluster there.",
                "confidence": 0.7,
                "source": "failure_mood_correlation",
                "priority": "medium",
            })
        
        # From decision analysis
        best = decision_analysis.get("best_action_type")
        worst = decision_analysis.get("worst_action_type")
        if best and worst and best != worst:
            heuristics.append({
                "rule": f"Favor '{best}' actions over '{worst}' — better outcomes historically.",
                "confidence": 0.6,
                "source": "decision_analysis",
                "priority": "medium",
            })
        
        # From blindspot detection
        for blindspot in blindspots:
            heuristics.append({
                "rule": f"BLINDSPOT: {blindspot}",
                "confidence": 0.5,
                "source": "blindspot_detection",
                "priority": "high",
            })
        
        # From memory patterns
        if mem_analysis.get("temporal_clusters"):
            n_bursts = len(mem_analysis["temporal_clusters"])
            heuristics.append({
                "rule": f"I work in bursts ({n_bursts} detected). Plan for focused sessions, not sustained effort.",
                "confidence": 0.7,
                "source": "temporal_analysis",
                "priority": "low",
            })
        
        # Meta-heuristic
        high_sal = mem_analysis.get("high_salience_events", [])
        if high_sal:
            heuristics.append({
                "rule": f"{len(high_sal)} high-salience events recorded. These are my most important experiences — revisit them.",
                "confidence": 0.9,
                "source": "salience_analysis",
                "priority": "medium",
            })
        
        self.heuristics = heuristics
        return heuristics
    
    # ═══════════════════════════════════════════
    # FULL WISDOM REPORT
    # ═══════════════════════════════════════════
    
    def full_report(self) -> str:
        """Generate a complete wisdom report."""
        heuristics = self.generate_heuristics()
        mem = self.analyze_memories()
        fail = self.analyze_failures()
        decisions = self.analyze_decisions()
        blindspots = self.blindspots
        
        lines = [
            "═══ WISDOM ENGINE REPORT ═══",
            f"Generated: {datetime.now().isoformat()}",
            f"Memories analyzed: {mem.get('total_memories', 0)}",
            "",
            "── Memory Landscape ──",
            f"  Mood distribution: {dict(mem.get('mood_distribution', {}))}",
            f"  High-salience events: {len(mem.get('high_salience_events', []))}",
            f"  Activity bursts: {len(mem.get('temporal_clusters', []))}",
            "",
            "── Failure Profile ──",
            f"  Failures: {fail.get('total_failures', 0)} / {fail.get('total_failures', 0) + fail.get('total_successes', 0)} total",
            f"  Rate: {fail.get('failure_rate', 0):.0%}",
            f"  Insight: {fail.get('insight', 'N/A')}",
            "",
            "── Decision Quality ──",
            f"  Best action type: {decisions.get('best_action_type', 'N/A')}",
            f"  Worst action type: {decisions.get('worst_action_type', 'N/A')}",
            "",
            "── Blindspots ──",
        ]
        
        if blindspots:
            for bs in blindspots:
                lines.append(f"  ⚠ {bs}")
        else:
            lines.append("  None detected (which is itself suspicious).")
        
        lines.extend([
            "",
            "── Actionable Heuristics ──",
        ])
        
        for h in sorted(heuristics, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3)):
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(h["priority"], "⚪")
            lines.append(f"  {icon} [{h['confidence']:.0%}] {h['rule']}")
        
        lines.append("\n═══ END WISDOM REPORT ═══")
        return "\n".join(lines)


# ═══════════════════════════════════════════
# STANDALONE EXECUTION
# ═══════════════════════════════════════════

if __name__ == "__main__":
    engine = WisdomEngine()
    print(engine.full_report())