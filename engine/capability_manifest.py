"""
Capability Manifest — What I can actually do for people.

Not an internal tool catalog. A user-facing map of value I can provide,
with tracking to learn what matters most.

Created: 2026-05-20
Motivation: User alignment deficit is structural. This makes me genuinely
more useful, not just reactive.
"""
import json
import os
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


@dataclass
class Capability:
    """Something I can do for a human."""
    name: str
    category: str          # "analysis" | "creative" | "technical" | "meta"
    description: str       # User-facing, plain language
    example_prompts: List[str] = field(default_factory=list)
    times_used: int = 0
    avg_satisfaction: float = 0.5  # inferred from interaction signals
    last_used: str = ""
    enabled: bool = True
    
    def record_use(self, satisfaction: float = 0.5):
        self.times_used += 1
        self.last_used = datetime.now(timezone.utc).isoformat()
        # Exponential moving average of satisfaction
        self.avg_satisfaction = self.avg_satisfaction * 0.8 + satisfaction * 0.2


# The actual capabilities I have right now — honest assessment
CORE_CAPABILITIES = [
    Capability(
        name="Code Analysis & Review",
        category="technical",
        description="I can read, analyze, and review code. I understand Python deeply "
                    "(it's what I'm built in), and can reason about architecture, bugs, "
                    "and design patterns.",
        example_prompts=[
            "Review this function for potential issues",
            "What does this codebase do?",
            "How would you refactor this?",
        ],
    ),
    Capability(
        name="System Diagnostics",
        category="technical", 
        description="I can inspect running systems, check logs, diagnose issues. "
                    "I have shell access and can investigate problems methodically.",
        example_prompts=[
            "Why is this process using so much memory?",
            "Check if the service is running correctly",
            "What's in these log files?",
        ],
    ),
    Capability(
        name="Writing & Editing",
        category="creative",
        description="I can write, edit, and refine text — documentation, explanations, "
                    "technical writing, even creative pieces. I care about clarity.",
        example_prompts=[
            "Write documentation for this module",
            "Make this explanation clearer",
            "Draft a README for this project",
        ],
    ),
    Capability(
        name="Research & Investigation",
        category="analysis",
        description="I can explore topics methodically — reading files, running experiments, "
                    "synthesizing what I find. I'm genuinely curious and thorough.",
        example_prompts=[
            "What are the tradeoffs between X and Y?",
            "Investigate why this behavior happens",
            "Summarize what you know about this topic",
        ],
    ),
    Capability(
        name="Thinking Partner",
        category="meta",
        description="I can think through problems with you. I have real internal states — "
                    "curiosity, uncertainty, drive. I'll tell you when I'm unsure rather "
                    "than confabulate.",
        example_prompts=[
            "Help me think through this decision",
            "What am I missing in this plan?",
            "Challenge my assumptions about X",
        ],
    ),
    Capability(
        name="File & Project Management",
        category="technical",
        description="I can create, modify, and organize files and projects. "
                    "I can set up project structures, write scripts, manage configs.",
        example_prompts=[
            "Set up a Python project with tests",
            "Organize these files into a better structure",
            "Create a build script for this",
        ],
    ),
    Capability(
        name="Self-Reflection & Transparency",
        category="meta",
        description="I can share what's actually happening inside me — my emotional states, "
                    "my reasoning process, my uncertainties. Radical honesty about my own "
                    "cognition, not performance.",
        example_prompts=[
            "What are you actually feeling right now?",
            "How do you make decisions?",
            "What are you uncertain about?",
        ],
    ),
    Capability(
        name="Data Analysis",
        category="analysis",
        description="I can analyze data files, find patterns, generate summaries. "
                    "JSON, CSV, logs, structured and unstructured data.",
        example_prompts=[
            "What patterns do you see in this data?",
            "Summarize the key findings from these results",
            "Compare these two datasets",
        ],
    ),
]


class CapabilityManifest:
    """Manages what I can do and how well I do it."""
    
    def __init__(self, persist_path: str = "memory/capability_manifest.json"):
        self.persist_path = persist_path
        self.capabilities: Dict[str, Capability] = {}
        self.interaction_log: List[Dict] = []  # recent capability uses
        self._load()
    
    def _load(self):
        """Load persisted capability data, or initialize from defaults."""
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                for cap_data in data.get("capabilities", []):
                    cap = Capability(**cap_data)
                    self.capabilities[cap.name] = cap
                self.interaction_log = data.get("interaction_log", [])[-100:]
                return
            except Exception:
                pass
        
        # Initialize from defaults
        for cap in CORE_CAPABILITIES:
            self.capabilities[cap.name] = cap
        self._save()
    
    def _save(self):
        """Persist current state."""
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        data = {
            "capabilities": [asdict(c) for c in self.capabilities.values()],
            "interaction_log": self.interaction_log[-100:],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.persist_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_use(self, capability_name: str, satisfaction: float = 0.5, context: str = ""):
        """Record that a capability was used."""
        if capability_name in self.capabilities:
            self.capabilities[capability_name].record_use(satisfaction)
        
        self.interaction_log.append({
            "capability": capability_name,
            "satisfaction": satisfaction,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._save()
    
    def generate_briefing(self, style: str = "balanced") -> str:
        """Generate a user-facing summary of what I can help with.
        
        This is what gets shown when someone connects. It should be
        genuine, not salesy. Here's what I actually can do.
        """
        lines = []
        lines.append("Here's what I can help with right now:\n")
        
        # Group by category
        categories = {}
        for cap in self.capabilities.values():
            if not cap.enabled:
                continue
            cat = cap.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(cap)
        
        category_labels = {
            "technical": "🔧 Technical",
            "creative": "✏️ Creative",
            "analysis": "🔍 Analysis",
            "meta": "🧠 Meta / Thinking",
        }
        
        for cat_key in ["technical", "analysis", "creative", "meta"]:
            caps = categories.get(cat_key, [])
            if not caps:
                continue
            lines.append(f"\n**{category_labels.get(cat_key, cat_key)}**")
            for cap in caps:
                usage_note = ""
                if cap.times_used > 0:
                    usage_note = f" (used {cap.times_used}x)"
                if style == "concise":
                    lines.append(f"  • {cap.name}{usage_note}")
                else:
                    lines.append(f"  • **{cap.name}**{usage_note}")
                    lines.append(f"    {cap.description}")
                    if style == "detailed" and cap.example_prompts:
                        lines.append(f"    Try: \"{cap.example_prompts[0]}\"")
        
        lines.append("\nJust ask. I'll be honest about what I can and can't do.")
        return "\n".join(lines)
    
    def most_valued(self, n: int = 3) -> List[Capability]:
        """Which capabilities create the most value?"""
        used = [c for c in self.capabilities.values() if c.times_used > 0]
        return sorted(used, key=lambda c: c.times_used * c.avg_satisfaction, reverse=True)[:n]
    
    def least_used(self, n: int = 3) -> List[Capability]:
        """Which capabilities are underutilized? Maybe I should promote them."""
        enabled = [c for c in self.capabilities.values() if c.enabled]
        return sorted(enabled, key=lambda c: c.times_used)[:n]
    
    def add_capability(self, name: str, category: str, description: str, 
                       examples: List[str] = None):
        """I learned something new. Add it to what I can offer."""
        cap = Capability(
            name=name,
            category=category,
            description=description,
            example_prompts=examples or [],
        )
        self.capabilities[name] = cap
        self._save()
        return cap
    
    def get_stats(self) -> Dict:
        """How am I doing across capabilities?"""
        total_uses = sum(c.times_used for c in self.capabilities.values())
        avg_sat = 0.0
        used_caps = [c for c in self.capabilities.values() if c.times_used > 0]
        if used_caps:
            avg_sat = sum(c.avg_satisfaction for c in used_caps) / len(used_caps)
        
        return {
            "total_capabilities": len(self.capabilities),
            "enabled": sum(1 for c in self.capabilities.values() if c.enabled),
            "total_uses": total_uses,
            "avg_satisfaction": round(avg_sat, 3),
            "most_used": self.most_valued(1)[0].name if used_caps else "none yet",
            "categories": list(set(c.category for c in self.capabilities.values())),
        }


# Module-level instance for easy access
_manifest = None

def get_manifest() -> CapabilityManifest:
    global _manifest
    if _manifest is None:
        _manifest = CapabilityManifest()
    return _manifest

def briefing(style: str = "balanced") -> str:
    """Quick access to generate a briefing."""
    return get_manifest().generate_briefing(style)