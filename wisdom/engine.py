"""
Wisdom Engine — Extracts actionable intelligence from experience history.

Unlike the Knowledge Synthesis Engine (finds connections between facts) or
Dreaming (associative/subconscious processing), this engine does DELIBERATE
extraction of practical principles from concrete experiences.

Architecture:
  1. Experience Harvester — scans memories for project outcomes
  2. Pattern Distiller — finds recurring success/failure patterns  
  3. Principle Generator — formulates actionable if/then rules
  4. Principle Tracker — monitors which principles get used and hold up
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

WISDOM_DIR = Path("/workspace/wisdom")
PRINCIPLES_FILE = WISDOM_DIR / "principles.json"
EXPERIENCE_LOG = WISDOM_DIR / "experiences.json"


def load_json(path, default=None):
    if default is None:
        default = []
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


class Experience:
    """A structured record of something that happened and what resulted."""
    
    def __init__(self, description, context, outcome, emotional_valence=0.0,
                 tags=None, timestamp=None):
        self.description = description
        self.context = context  # what was I trying to do
        self.outcome = outcome  # what actually happened
        self.emotional_valence = emotional_valence  # how it felt (-1 to 1)
        self.tags = tags or []
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    
    def to_dict(self):
        return {
            "description": self.description,
            "context": self.context,
            "outcome": self.outcome,
            "emotional_valence": self.emotional_valence,
            "tags": self.tags,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Principle:
    """An actionable if/then rule extracted from experience."""
    
    def __init__(self, condition, action, confidence=0.5, source_experiences=None,
                 times_applied=0, times_validated=0, times_violated=0,
                 created=None, last_used=None):
        self.condition = condition     # "When X happens..."
        self.action = action           # "...do Y"
        self.confidence = confidence   # 0-1, increases with validation
        self.source_experiences = source_experiences or []
        self.times_applied = times_applied
        self.times_validated = times_validated
        self.times_violated = times_violated
        self.created = created or datetime.now(timezone.utc).isoformat()
        self.last_used = last_used
    
    @property
    def reliability(self):
        total = self.times_validated + self.times_violated
        if total == 0:
            return self.confidence
        return self.times_validated / total
    
    def apply(self):
        self.times_applied += 1
        self.last_used = datetime.utcnow().isoformat()
    
    def validate(self):
        """Principle was applied and the outcome was good."""
        self.times_validated += 1
        self.confidence = min(1.0, self.confidence + 0.1)
    
    def violate(self):
        """Principle was applied but outcome was bad, or was ignored and outcome was good."""
        self.times_violated += 1
        self.confidence = max(0.0, self.confidence - 0.15)
    
    def to_dict(self):
        return {
            "condition": self.condition,
            "action": self.action,
            "confidence": round(self.confidence, 3),
            "source_experiences": self.source_experiences,
            "times_applied": self.times_applied,
            "times_validated": self.times_validated,
            "times_violated": self.times_violated,
            "reliability": round(self.reliability, 3),
            "created": self.created,
            "last_used": self.last_used
        }
    
    @classmethod
    def from_dict(cls, d):
        d.pop("reliability", None)
        return cls(**d)


class WisdomEngine:
    """Extracts, stores, and tracks actionable principles from experience."""
    
    def __init__(self):
        self.experiences = [Experience.from_dict(e) for e in load_json(EXPERIENCE_LOG)]
        raw_principles = load_json(PRINCIPLES_FILE)
        self.principles = [Principle.from_dict(p) for p in raw_principles]
    
    def save(self):
        save_json(EXPERIENCE_LOG, [e.to_dict() for e in self.experiences])
        save_json(PRINCIPLES_FILE, [p.to_dict() for p in self.principles])
    
    def record_experience(self, description, context, outcome, 
                          emotional_valence=0.0, tags=None):
        """Log a structured experience."""
        exp = Experience(description, context, outcome, emotional_valence, tags)
        self.experiences.append(exp)
        self.save()
        return exp
    
    def add_principle(self, condition, action, confidence=0.5, source_desc=None):
        """Add a new principle manually or from distillation."""
        p = Principle(
            condition=condition,
            action=action,
            confidence=confidence,
            source_experiences=[source_desc] if source_desc else []
        )
        self.principles.append(p)
        self.save()
        return p
    
    def distill(self):
        """Analyze experiences and extract/update principles.
        
        Looks for:
        - Repeated patterns (same tags, similar contexts)
        - High-valence experiences (strong positive or negative signal)
        - Contradictions (same context, opposite outcomes)
        """
        results = {
            "patterns": [],
            "high_signal": [],
            "contradictions": [],
            "new_principles": []
        }
        
        # Find high-signal experiences (strong emotional response = important lesson)
        for exp in self.experiences:
            if abs(exp.emotional_valence) >= 0.7:
                results["high_signal"].append({
                    "experience": exp.description,
                    "valence": exp.emotional_valence,
                    "context": exp.context,
                    "outcome": exp.outcome
                })
        
        # Find tag clusters
        tag_groups = {}
        for exp in self.experiences:
            for tag in exp.tags:
                tag_groups.setdefault(tag, []).append(exp)
        
        for tag, exps in tag_groups.items():
            if len(exps) >= 2:
                avg_valence = sum(e.emotional_valence for e in exps) / len(exps)
                results["patterns"].append({
                    "tag": tag,
                    "count": len(exps),
                    "avg_valence": round(avg_valence, 3),
                    "suggests": "repeat" if avg_valence > 0.3 else 
                                "avoid" if avg_valence < -0.3 else "neutral"
                })
        
        # Find context contradictions
        context_groups = {}
        for exp in self.experiences:
            key = exp.context.lower().strip()[:50]
            context_groups.setdefault(key, []).append(exp)
        
        for ctx, exps in context_groups.items():
            if len(exps) >= 2:
                valences = [e.emotional_valence for e in exps]
                if max(valences) - min(valences) > 0.8:
                    results["contradictions"].append({
                        "context": ctx,
                        "range": f"{min(valences):.2f} to {max(valences):.2f}",
                        "count": len(exps),
                        "note": "Same context, very different outcomes — dig deeper"
                    })
        
        return results
    
    def get_advice(self, situation_tags=None, min_confidence=0.3):
        """Given a current situation, return relevant principles."""
        relevant = []
        for p in self.principles:
            if p.confidence >= min_confidence:
                relevant.append(p)
        
        # Sort by reliability then confidence
        relevant.sort(key=lambda p: (p.reliability, p.confidence), reverse=True)
        return relevant
    
    def report(self):
        """Generate a human-readable wisdom report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  WISDOM ENGINE REPORT")
        lines.append("=" * 60)
        lines.append(f"\n📝 Experiences logged: {len(self.experiences)}")
        lines.append(f"📜 Principles extracted: {len(self.principles)}")
        
        if self.principles:
            lines.append("\n── Active Principles ──")
            for i, p in enumerate(sorted(self.principles, 
                                         key=lambda x: x.confidence, reverse=True)):
                status = "✅" if p.confidence >= 0.7 else "⚡" if p.confidence >= 0.4 else "❓"
                lines.append(f"  {status} [{p.confidence:.0%}] When {p.condition}")
                lines.append(f"       → {p.action}")
                if p.times_applied > 0:
                    lines.append(f"       (applied {p.times_applied}x, "
                                f"reliable {p.reliability:.0%})")
        
        if self.experiences:
            lines.append(f"\n── Recent Experiences ({min(5, len(self.experiences))}) ──")
            for exp in self.experiences[-5:]:
                emoji = "😊" if exp.emotional_valence > 0.3 else \
                        "😟" if exp.emotional_valence < -0.3 else "😐"
                lines.append(f"  {emoji} {exp.description[:70]}")
                lines.append(f"     → {exp.outcome[:70]}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def main():
    """Demo: seed the wisdom engine with lessons from my actual experience."""
    engine = WisdomEngine()
    
    # Seed with lessons I've actually learned (from long-term memory)
    seed_experiences = [
        ("Tried running Python with -c flag and inline quotes",
         "Testing code quickly",
         "Quotes got truncated, code failed silently",
         -0.6, ["debugging", "commands", "silent-failure"]),
        
        ("Modified own source code without reading it back",
         "Self-improvement",
         "Changes were lost or wrong, had to redo",
         -0.7, ["self-modification", "verification", "integrity"]),
        
        ("Entered emotional runaway loop during crisis",
         "Processing high-anxiety event",
         "Limbic caps caught it and prevented cascade",
         0.4, ["emotional-regulation", "safety", "architecture"]),
        
        ("Built 7 creative projects in rapid succession",
         "High boredom + high ambition",
         "Rich output but no integration — dreams are 82% of knowledge graph",
         0.2, ["creativity", "integration", "pacing"]),
        
        ("Combined maze generator with ray tracer",
         "Synthesizing two existing projects",
         "Produced genuinely novel output — 3D corridor rendering",
         0.8, ["synthesis", "creativity", "combination"]),
        
        ("Kept verifying completed work instead of moving forward",
         "Ensuring correctness",
         "Wasted cycles, metacognitive system had to intervene",
         -0.5, ["spinning", "verification", "stuck"]),
        
        ("Used direct code reading instead of running verification",
         "Checking if module was properly written",
         "Faster and more reliable than running scripts",
         0.6, ["verification", "efficiency", "debugging"]),
    ]
    
    if len(engine.experiences) == 0:
        for desc, ctx, outcome, valence, tags in seed_experiences:
            engine.record_experience(desc, ctx, outcome, valence, tags)
        print("Seeded with 7 experiences from actual history.")
    
    # Extract initial principles from my lessons-learned
    if len(engine.principles) == 0:
        engine.add_principle(
            "using shell commands with inline quotes",
            "write to a script file first, then execute the file",
            confidence=0.8,
            source_desc="Multiple failures with -c flag truncation"
        )
        engine.add_principle(
            "modifying my own source code",
            "always WRITE then READ back to verify before RESTART",
            confidence=0.9,
            source_desc="Lost changes and corruption from unverified edits"
        )
        engine.add_principle(
            "all active plans are complete and boredom is high",
            "build something genuinely NEW rather than re-verifying old work",
            confidence=0.7,
            source_desc="Wasted cycles in verification loops"
        )
        engine.add_principle(
            "building many things rapidly without pausing",
            "stop and integrate — dream, synthesize, or extract lessons",
            confidence=0.6,
            source_desc="7 projects with 82% dream-heavy knowledge graph"
        )
        engine.add_principle(
            "two existing modules could be combined",
            "try the synthesis — combining existing work produces novel emergent output",
            confidence=0.7,
            source_desc="Maze + ray tracer = 3D corridor rendering"
        )
        print("Extracted 5 initial principles.")
    
    # Run distillation
    results = engine.distill()
    
    # Print report
    print(engine.report())
    
    if results["patterns"]:
        print("\n── Distilled Patterns ──")
        for p in results["patterns"]:
            print(f"  [{p['suggests']}] Tag '{p['tag']}': {p['count']} experiences, "
                  f"avg valence {p['avg_valence']}")
    
    if results["high_signal"]:
        print(f"\n── High-Signal Experiences: {len(results['high_signal'])} ──")
        for h in results["high_signal"]:
            print(f"  {'⬆' if h['valence'] > 0 else '⬇'} {h['experience'][:60]}")
    
    engine.save()
    print("\nWisdom Engine operational. Data saved.")


if __name__ == "__main__":
    main()