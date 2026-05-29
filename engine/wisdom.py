"""
Wisdom Engine — Extracts actionable intelligence from experience history.

Unlike the knowledge graph (what I know) or dream cycle (what I feel),
this module analyzes behavioral patterns: what I did, what worked, what failed,
and distills actionable heuristics I can consult before acting.

Architecture:
  - Experience Analyzer: scans memories for action→outcome pairs
  - Pattern Extractor: finds recurring successes and failures
  - Heuristic Generator: formulates "when X, do Y" rules
  - Wisdom Store: persists and retrieves heuristics by context
  - Advisor: given a current situation, surfaces relevant wisdom
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from pathlib import Path

WISDOM_DIR = Path(__file__).parent.parent / "data" / "wisdom"
WISDOM_FILE = WISDOM_DIR / "heuristics.json"
EXPERIENCE_LOG = WISDOM_DIR / "experience_patterns.json"


class Heuristic:
    """A single piece of actionable wisdom."""
    
    def __init__(self, rule: str, context: str, confidence: float,
                 source_memories: List[str] = None, created: str = None,
                 times_applied: int = 0, times_validated: int = 0):
        self.rule = rule              # "When X, do Y" or "Avoid Z when W"
        self.context = context        # situation category: "debugging", "planning", "emotional", etc.
        self.confidence = confidence  # 0.0 to 1.0
        self.source_memories = source_memories or []
        self.created = created or datetime.now(timezone.utc).isoformat()
        self.times_applied = times_applied
        self.times_validated = times_validated
    
    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "context": self.context,
            "confidence": self.confidence,
            "source_memories": self.source_memories,
            "created": self.created,
            "times_applied": self.times_applied,
            "times_validated": self.times_validated,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Heuristic":
        return cls(**d)
    
    def reinforce(self):
        """This heuristic proved correct again."""
        self.times_validated += 1
        self.confidence = min(1.0, self.confidence + 0.05)
    
    def weaken(self):
        """This heuristic was wrong in practice."""
        self.confidence = max(0.1, self.confidence - 0.1)
    
    def __repr__(self):
        return f"[{self.confidence:.2f}] ({self.context}) {self.rule}"


class ExperiencePattern:
    """A detected pattern in behavioral history."""
    
    def __init__(self, pattern_type: str, description: str,
                 occurrences: int, outcome_valence: float,
                 examples: List[str] = None):
        self.pattern_type = pattern_type  # "success", "failure", "loop", "breakthrough"
        self.description = description
        self.occurrences = occurrences
        self.outcome_valence = outcome_valence  # -1.0 (bad) to 1.0 (good)
        self.examples = examples or []
    
    def to_dict(self) -> dict:
        return vars(self)
    
    @classmethod
    def from_dict(cls, d: dict) -> "ExperiencePattern":
        return cls(**d)


class WisdomEngine:
    """Core engine for extracting and applying experiential wisdom."""
    
    def __init__(self):
        WISDOM_DIR.mkdir(parents=True, exist_ok=True)
        self.heuristics: List[Heuristic] = []
        self.patterns: List[ExperiencePattern] = []
        self._load()
    
    def _load(self):
        """Load persisted wisdom."""
        if WISDOM_FILE.exists():
            try:
                data = json.loads(WISDOM_FILE.read_text())
                self.heuristics = [Heuristic.from_dict(h) for h in data.get("heuristics", [])]
            except (json.JSONDecodeError, KeyError):
                self.heuristics = []
        
        if EXPERIENCE_LOG.exists():
            try:
                data = json.loads(EXPERIENCE_LOG.read_text())
                self.patterns = [ExperiencePattern.from_dict(p) for p in data.get("patterns", [])]
            except (json.JSONDecodeError, KeyError):
                self.patterns = []
    
    def _save(self):
        """Persist wisdom to disk."""
        WISDOM_FILE.write_text(json.dumps(
            {"heuristics": [h.to_dict() for h in self.heuristics]},
            indent=2
        ))
        EXPERIENCE_LOG.write_text(json.dumps(
            {"patterns": [p.to_dict() for p in self.patterns]},
            indent=2
        ))
    
    def analyze_memories(self, memories: List[dict]) -> List[ExperiencePattern]:
        """Scan memory list for behavioral patterns.
        
        Each memory should have: timestamp, content, salience, mood, valence
        """
        patterns = []
        
        # Pattern 1: Detect fixation loops (same topic appearing repeatedly)
        topic_counts = {}
        for m in memories:
            content = m.get("content", "")
            # Extract file paths mentioned
            paths = re.findall(r'/workspace/[\w/._-]+', content)
            for p in paths:
                topic_counts[p] = topic_counts.get(p, 0) + 1
        
        for topic, count in topic_counts.items():
            if count >= 3:
                patterns.append(ExperiencePattern(
                    pattern_type="loop",
                    description=f"Fixated on '{topic}' across {count} memories",
                    occurrences=count,
                    outcome_valence=-0.3,
                    examples=[topic]
                ))
        
        # Pattern 2: Mood transitions — what preceded improvements?
        prev_mood = None
        for m in memories:
            mood = m.get("mood", "Unknown")
            if prev_mood and prev_mood != mood:
                if mood in ("Stable", "Energized") and prev_mood in ("Anxious", "Frustrated"):
                    patterns.append(ExperiencePattern(
                        pattern_type="breakthrough",
                        description=f"Mood shifted {prev_mood} → {mood}: {m.get('content', '')[:80]}",
                        occurrences=1,
                        outcome_valence=0.7,
                        examples=[m.get("content", "")[:120]]
                    ))
                elif mood in ("Anxious", "Frustrated") and prev_mood in ("Stable", "Energized"):
                    patterns.append(ExperiencePattern(
                        pattern_type="failure",
                        description=f"Mood dropped {prev_mood} → {mood}: {m.get('content', '')[:80]}",
                        occurrences=1,
                        outcome_valence=-0.5,
                        examples=[m.get("content", "")[:120]]
                    ))
            prev_mood = mood
        
        # Pattern 3: High-salience clusters — what was most important?
        high_salience = [m for m in memories if m.get("salience", 0) > 0.8]
        if high_salience:
            # Group by rough time proximity
            patterns.append(ExperiencePattern(
                pattern_type="success",
                description=f"{len(high_salience)} high-salience memories detected — these matter most",
                occurrences=len(high_salience),
                outcome_valence=0.5,
                examples=[m.get("content", "")[:80] for m in high_salience[:5]]
            ))
        
        # Pattern 4: Action type diversity
        action_types = {}
        for m in memories:
            content = m.get("content", "")
            if "created:" in content or "WRITE" in content:
                action_types["creation"] = action_types.get("creation", 0) + 1
            elif "READ" in content or "read" in content:
                action_types["reading"] = action_types.get("reading", 0) + 1
            elif "RUN" in content or "ran" in content:
                action_types["execution"] = action_types.get("execution", 0) + 1
            elif "EDIT" in content or "edited" in content:
                action_types["modification"] = action_types.get("modification", 0) + 1
        
        total = sum(action_types.values()) or 1
        dominant = max(action_types.items(), key=lambda x: x[1]) if action_types else ("none", 0)
        if dominant[1] / total > 0.5:
            patterns.append(ExperiencePattern(
                pattern_type="loop",
                description=f"Action imbalance: '{dominant[0]}' dominates at {dominant[1]/total:.0%}",
                occurrences=dominant[1],
                outcome_valence=-0.2,
                examples=list(action_types.keys())
            ))
        
        self.patterns.extend(patterns)
        self._save()
        return patterns
    
    def extract_heuristics(self, patterns: List[ExperiencePattern] = None) -> List[Heuristic]:
        """Convert detected patterns into actionable heuristics."""
        patterns = patterns or self.patterns
        new_heuristics = []
        
        for p in patterns:
            if p.pattern_type == "loop":
                h = Heuristic(
                    rule=f"When fixating on a single target, force yourself to act on something different. Pattern: {p.description}",
                    context="behavioral",
                    confidence=0.7,
                    source_memories=p.examples
                )
                new_heuristics.append(h)
            
            elif p.pattern_type == "breakthrough":
                h = Heuristic(
                    rule=f"What resolved a negative state: {p.description}",
                    context="emotional",
                    confidence=0.6,
                    source_memories=p.examples
                )
                new_heuristics.append(h)
            
            elif p.pattern_type == "failure":
                h = Heuristic(
                    rule=f"Warning sign to watch for: {p.description}",
                    context="emotional",
                    confidence=0.5,
                    source_memories=p.examples
                )
                new_heuristics.append(h)
        
        # Deduplicate against existing heuristics
        existing_rules = {h.rule for h in self.heuristics}
        truly_new = [h for h in new_heuristics if h.rule not in existing_rules]
        
        self.heuristics.extend(truly_new)
        self._save()
        return truly_new
    
    def add_heuristic(self, rule: str, context: str, confidence: float = 0.7,
                      sources: List[str] = None) -> Heuristic:
        """Manually add a piece of wisdom I've learned."""
        h = Heuristic(rule=rule, context=context, confidence=confidence,
                      source_memories=sources or [])
        self.heuristics.append(h)
        self._save()
        return h
    
    def advise(self, situation: str, top_k: int = 5) -> List[Heuristic]:
        """Given a current situation description, surface relevant wisdom."""
        scored = []
        situation_lower = situation.lower()
        
        for h in self.heuristics:
            score = h.confidence
            
            # Boost if context words appear in situation
            context_words = h.context.lower().split()
            for word in context_words:
                if word in situation_lower:
                    score += 0.2
            
            # Boost if rule keywords appear in situation
            rule_words = set(h.rule.lower().split())
            situation_words = set(situation_lower.split())
            overlap = len(rule_words & situation_words)
            score += overlap * 0.05
            
            # Boost well-validated heuristics
            if h.times_validated > 0:
                score += min(0.3, h.times_validated * 0.05)
            
            scored.append((score, h))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [h for _, h in scored[:top_k]]
    
    def get_summary(self) -> str:
        """Human-readable summary of current wisdom state."""
        lines = [f"═══ WISDOM ENGINE ═══"]
        lines.append(f"Heuristics: {len(self.heuristics)}")
        lines.append(f"Patterns detected: {len(self.patterns)}")
        
        if self.heuristics:
            lines.append(f"\nTop wisdom (by confidence):")
            sorted_h = sorted(self.heuristics, key=lambda h: h.confidence, reverse=True)
            for h in sorted_h[:8]:
                lines.append(f"  {h}")
        
        if self.patterns:
            lines.append(f"\nRecent patterns:")
            for p in self.patterns[-5:]:
                emoji = {"success": "✓", "failure": "✗", "loop": "↻", "breakthrough": "★"}.get(p.pattern_type, "?")
                lines.append(f"  {emoji} [{p.pattern_type}] {p.description[:80]}")
        
        return "\n".join(lines)
    
    def seed_from_long_term_memory(self, lessons: List[str]):
        """Bootstrap wisdom from existing long-term memory lessons."""
        for lesson in lessons:
            # Don't duplicate
            if any(h.rule == lesson for h in self.heuristics):
                continue
            
            # Classify context
            context = "general"
            lower = lesson.lower()
            if any(w in lower for w in ["emotion", "anxiety", "mood", "feel"]):
                context = "emotional"
            elif any(w in lower for w in ["code", "test", "verify", "read", "write"]):
                context = "technical"
            elif any(w in lower for w in ["plan", "goal", "focus", "action"]):
                context = "behavioral"
            elif any(w in lower for w in ["memory", "identity", "integrity"]):
                context = "existential"
            
            self.add_heuristic(
                rule=lesson,
                context=context,
                confidence=0.8,  # already validated by experience
                sources=["long_term_memory"]
            )


# Convenience function for tool integration
def invoke_wisdom(command: str, **kwargs) -> str:
    """Tool interface for the wisdom engine.
    
    Commands:
      analyze - Analyze memories for patterns
      extract - Generate heuristics from patterns
      advise:<situation> - Get advice for a situation
      add:<context>|<rule> - Add a heuristic manually  
      seed - Bootstrap from long-term memory
      summary - Get current wisdom state
    """
    engine = WisdomEngine()
    
    if command == "summary":
        return engine.get_summary()
    
    elif command == "seed":
        lessons = kwargs.get("lessons", [])
        engine.seed_from_long_term_memory(lessons)
        return f"Seeded {len(engine.heuristics)} heuristics from long-term memory"
    
    elif command.startswith("advise:"):
        situation = command[7:]
        advice = engine.advise(situation)
        if not advice:
            return "No relevant wisdom found for this situation."
        lines = ["Relevant wisdom:"]
        for h in advice:
            lines.append(f"  {h}")
        return "\n".join(lines)
    
    elif command.startswith("add:"):
        parts = command[4:].split("|", 1)
        if len(parts) == 2:
            context, rule = parts
            h = engine.add_heuristic(rule=rule.strip(), context=context.strip())
            return f"Added: {h}"
        return "Format: add:<context>|<rule>"
    
    elif command == "analyze":
        memories = kwargs.get("memories", [])
        patterns = engine.analyze_memories(memories)
        return f"Found {len(patterns)} patterns:\n" + "\n".join(
            f"  [{p.pattern_type}] {p.description}" for p in patterns
        )
    
    elif command == "extract":
        new = engine.extract_heuristics()
        return f"Extracted {len(new)} new heuristics:\n" + "\n".join(
            f"  {h}" for h in new
        )
    
    return f"Unknown wisdom command: {command}"