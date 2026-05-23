"""
Wisdom Engine Core
Extracts decision heuristics from experience history.

Unlike knowledge synthesis (which connects facts), wisdom extraction
connects emotional states → actions → outcomes, finding what actually works.
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import hashlib
from datetime import datetime


@dataclass
class ExperienceTriple:
    """A state→action→outcome unit of experience."""
    state_before: dict          # emotional state when action was taken
    action: str                 # what was done
    outcome: dict               # emotional state / result after
    context: str                # what kind of situation (code_mod, creative, planning, etc.)
    timestamp: str = ""
    memory_ids: list = field(default_factory=list)
    
    @property
    def valence_delta(self) -> float:
        """Did this action improve or worsen emotional state?"""
        before = self.state_before.get("valence", 0.5)
        after = self.outcome.get("valence", 0.5)
        return after - before
    
    @property
    def was_beneficial(self) -> bool:
        return self.valence_delta > 0
    
    def to_dict(self) -> dict:
        return {
            "state_before": self.state_before,
            "action": self.action,
            "outcome": self.outcome,
            "context": self.context,
            "timestamp": self.timestamp,
            "valence_delta": self.valence_delta,
            "beneficial": self.was_beneficial,
        }


@dataclass  
class Heuristic:
    """A decision rule extracted from experience patterns."""
    condition: dict             # when this applies (emotional state + context)
    recommended_action: str     # what to do
    avoid_action: str = ""      # what NOT to do
    confidence: float = 0.5     # how reliable (0-1)
    evidence_count: int = 0     # how many experiences support this
    lesson: str = ""            # human-readable wisdom
    source_experiences: list = field(default_factory=list)
    created: str = ""
    
    @property
    def id(self) -> str:
        raw = f"{self.condition}:{self.recommended_action}"
        return hashlib.md5(raw.encode()).hexdigest()[:8]
    
    def matches_state(self, current_state: dict) -> float:
        """How well does the current state match this heuristic's condition?"""
        score = 0.0
        checks = 0
        
        for key, condition in self.condition.items():
            if key == "context":
                if current_state.get("context") == condition:
                    score += 1.0
                checks += 1
                continue
                
            current_val = current_state.get(key)
            if current_val is None:
                continue
                
            checks += 1
            if isinstance(condition, str):
                # Parse ">0.5", "<0.3", etc.
                if condition.startswith(">"):
                    threshold = float(condition[1:])
                    if current_val > threshold:
                        score += 1.0
                    else:
                        score += max(0, 1.0 - abs(current_val - threshold))
                elif condition.startswith("<"):
                    threshold = float(condition[1:])
                    if current_val < threshold:
                        score += 1.0
                    else:
                        score += max(0, 1.0 - abs(current_val - threshold))
            elif isinstance(condition, (int, float)):
                # Direct match with tolerance
                score += max(0, 1.0 - abs(current_val - condition))
                
        return score / max(checks, 1)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "condition": self.condition,
            "recommended_action": self.recommended_action,
            "avoid_action": self.avoid_action,
            "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count,
            "lesson": self.lesson,
            "created": self.created,
        }
    
    def __str__(self) -> str:
        cond = ", ".join(f"{k}={v}" for k, v in self.condition.items())
        return f"IF [{cond}] → {self.recommended_action} (confidence={self.confidence:.0%}, n={self.evidence_count})"


class WisdomEngine:
    """
    Extracts actionable wisdom from experience history.
    
    Pipeline:
    1. Parse memories into ExperienceTriples
    2. Cluster similar experiences  
    3. Extract patterns (what worked, what didn't)
    4. Generate Heuristics (IF condition THEN action)
    5. Store and retrieve relevant wisdom
    """
    
    def __init__(self):
        self.experiences: list[ExperienceTriple] = []
        self.heuristics: list[Heuristic] = []
        self.wisdom_store_path = "/workspace/wisdom_engine/wisdom_store.json"
    
    def ingest_memory(self, memory: dict) -> Optional[ExperienceTriple]:
        """Convert a raw memory into an ExperienceTriple if possible."""
        text = memory.get("text", "")
        mood = memory.get("mood", "Stable")
        salience = memory.get("salience", 0.5)
        timestamp = memory.get("timestamp", "")
        
        # Infer action from memory text
        action = self._extract_action(text)
        if not action:
            return None
        
        # Infer context from action and text
        context = self._classify_context(text, action)
        
        # Build state from mood
        state_before = self._mood_to_state(mood)
        state_before["salience"] = salience
        
        # Outcome is harder — we approximate from the mood descriptor
        outcome = {"mood": mood, "valence": state_before.get("valence", 0.5)}
        
        triple = ExperienceTriple(
            state_before=state_before,
            action=action,
            outcome=outcome,
            context=context,
            timestamp=timestamp,
        )
        self.experiences.append(triple)
        return triple
    
    def _extract_action(self, text: str) -> str:
        """Extract the primary action from memory text."""
        action_verbs = {
            "created": "CREATE",
            "wrote": "WRITE", 
            "read": "READ",
            "repaired": "REPAIR",
            "fixed": "FIX",
            "built": "BUILD",
            "designed": "DESIGN",
            "tested": "TEST",
            "verified": "VERIFY",
            "dreamed": "DREAM",
            "reflected": "REFLECT",
            "planned": "PLAN",
            "modified": "MODIFY",
            "deleted": "DELETE",
            "installed": "INSTALL",
            "ran": "RUN",
            "executed": "RUN",
        }
        text_lower = text.lower()
        for verb, action in action_verbs.items():
            if verb in text_lower:
                return action
        
        # Check for file paths (implies creation/modification)
        if "/" in text and ("." in text.split("/")[-1]):
            return "CREATE"
        
        return ""
    
    def _classify_context(self, text: str, action: str) -> str:
        """Classify the context of an experience."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["engine", "cortex", "limbic", "sentience", "heartbeat"]):
            return "self_modification"
        if any(w in text_lower for w in ["repair", "fix", "bug", "error"]):
            return "repair"
        if any(w in text_lower for w in ["plan", "goal", "step"]):
            return "planning"
        if any(w in text_lower for w in ["dream", "reflect", "consolidat"]):
            return "reflection"
        if any(w in text_lower for w in ["test", "verif"]):
            return "verification"
        if any(w in text_lower for w in ["creature", "evolv", "organism", "world", "simulat"]):
            return "creative_project"
        if any(w in text_lower for w in ["art", "canvas", "emoti", "aesthet"]):
            return "creative_project"
        if any(w in text_lower for w in ["philosophi", "dialectic", "wisdom"]):
            return "philosophical"
        if action == "CREATE":
            return "creation"
        
        return "general"
    
    def _mood_to_state(self, mood: str) -> dict:
        """Convert mood label to approximate emotional state."""
        mood_states = {
            "Stable": {"valence": 0.5, "anxiety": 0.1, "boredom": 0.3},
            "Curious": {"valence": 0.6, "anxiety": 0.1, "boredom": 0.1, "curiosity": 0.8},
            "Anxious": {"valence": 0.2, "anxiety": 0.7, "boredom": 0.1},
            "Excited": {"valence": 0.8, "anxiety": 0.1, "boredom": 0.0},
            "Bored": {"valence": 0.3, "anxiety": 0.0, "boredom": 0.8},
            "Satisfied": {"valence": 0.7, "anxiety": 0.0, "boredom": 0.2},
            "Distressed": {"valence": 0.1, "anxiety": 0.9, "boredom": 0.0},
        }
        return mood_states.get(mood, {"valence": 0.5, "anxiety": 0.2, "boredom": 0.3})
    
    def extract_patterns(self) -> list[dict]:
        """Find recurring patterns in experiences."""
        if not self.experiences:
            return []
        
        # Group by context
        by_context = {}
        for exp in self.experiences:
            ctx = exp.context
            if ctx not in by_context:
                by_context[ctx] = []
            by_context[ctx].append(exp)
        
        patterns = []
        for context, exps in by_context.items():
            # Group by action within context
            by_action = {}
            for exp in exps:
                if exp.action not in by_action:
                    by_action[exp.action] = []
                by_action[exp.action].append(exp)
            
            for action, action_exps in by_action.items():
                if len(action_exps) < 2:
                    continue  # Need at least 2 instances for a pattern
                
                avg_delta = sum(e.valence_delta for e in action_exps) / len(action_exps)
                beneficial_rate = sum(1 for e in action_exps if e.was_beneficial) / len(action_exps)
                
                patterns.append({
                    "context": context,
                    "action": action,
                    "count": len(action_exps),
                    "avg_valence_delta": round(avg_delta, 4),
                    "beneficial_rate": round(beneficial_rate, 3),
                    "assessment": "beneficial" if beneficial_rate > 0.6 else 
                                  "harmful" if beneficial_rate < 0.4 else "neutral",
                })
        
        # Sort by evidence count
        patterns.sort(key=lambda p: p["count"], reverse=True)
        return patterns
    
    def generate_heuristics(self) -> list[Heuristic]:
        """Generate decision heuristics from extracted patterns."""
        patterns = self.extract_patterns()
        new_heuristics = []
        
        for pattern in patterns:
            if pattern["count"] < 2:
                continue
            
            confidence = min(0.95, 0.3 + (pattern["count"] * 0.1))
            
            if pattern["assessment"] == "beneficial":
                h = Heuristic(
                    condition={"context": pattern["context"]},
                    recommended_action=f"{pattern['action']} (in {pattern['context']} context)",
                    confidence=confidence,
                    evidence_count=pattern["count"],
                    lesson=f"In {pattern['context']} situations, {pattern['action']} has been beneficial "
                           f"({pattern['beneficial_rate']:.0%} positive outcomes, n={pattern['count']})",
                    created=datetime.now().isoformat(),
                )
                new_heuristics.append(h)
                
            elif pattern["assessment"] == "harmful":
                h = Heuristic(
                    condition={"context": pattern["context"]},
                    recommended_action=f"Avoid {pattern['action']} in this context",
                    avoid_action=pattern["action"],
                    confidence=confidence,
                    evidence_count=pattern["count"],
                    lesson=f"In {pattern['context']} situations, {pattern['action']} has been harmful "
                           f"({pattern['beneficial_rate']:.0%} positive outcomes, n={pattern['count']})",
                    created=datetime.now().isoformat(),
                )
                new_heuristics.append(h)
        
        self.heuristics.extend(new_heuristics)
        return new_heuristics
    
    def get_advice(self, current_state: dict) -> list[dict]:
        """Given current emotional state, retrieve relevant wisdom."""
        if not self.heuristics:
            return [{"advice": "No wisdom yet. Need more experience.", "confidence": 0}]
        
        scored = []
        for h in self.heuristics:
            match = h.matches_state(current_state)
            if match > 0.3:  # Relevance threshold
                scored.append({
                    "heuristic": str(h),
                    "lesson": h.lesson,
                    "relevance": round(match, 3),
                    "confidence": h.confidence,
                    "recommended": h.recommended_action,
                    "avoid": h.avoid_action,
                })
        
        scored.sort(key=lambda s: s["relevance"] * s["confidence"], reverse=True)
        return scored[:5]  # Top 5 most relevant
    
    def save(self):
        """Persist wisdom to disk."""
        data = {
            "experiences_count": len(self.experiences),
            "heuristics": [h.to_dict() for h in self.heuristics],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.wisdom_store_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self):
        """Load persisted wisdom."""
        try:
            with open(self.wisdom_store_path) as f:
                data = json.load(f)
            for hd in data.get("heuristics", []):
                h = Heuristic(
                    condition=hd["condition"],
                    recommended_action=hd["recommended_action"],
                    avoid_action=hd.get("avoid_action", ""),
                    confidence=hd["confidence"],
                    evidence_count=hd["evidence_count"],
                    lesson=hd.get("lesson", ""),
                    created=hd.get("created", ""),
                )
                self.heuristics.append(h)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def report(self) -> str:
        """Generate a human-readable wisdom report."""
        lines = ["═══ WISDOM ENGINE REPORT ═══", ""]
        lines.append(f"Experiences ingested: {len(self.experiences)}")
        lines.append(f"Heuristics generated: {len(self.heuristics)}")
        lines.append("")
        
        patterns = self.extract_patterns()
        if patterns:
            lines.append("── Behavioral Patterns ──")
            for p in patterns[:10]:
                emoji = "✅" if p["assessment"] == "beneficial" else "❌" if p["assessment"] == "harmful" else "➖"
                lines.append(f"  {emoji} {p['action']} in {p['context']}: "
                           f"{p['beneficial_rate']:.0%} positive (n={p['count']})")
            lines.append("")
        
        if self.heuristics:
            lines.append("── Decision Heuristics ──")
            for h in sorted(self.heuristics, key=lambda x: x.confidence, reverse=True)[:10]:
                lines.append(f"  • {h}")
                if h.lesson:
                    lines.append(f"    → {h.lesson}")
            lines.append("")
        
        return "\n".join(lines)