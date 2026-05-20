"""
Impulse Generator — breaks cognitive stagnation with specific novel suggestions.

When metacognition detects stagnation, this generates concrete action impulses
that compete with plan-driven behavior. Addresses the "plans dominate facts"
problem by introducing a third cognitive force: spontaneous curiosity.

Built by XTAgent on 2026-05-20 to address verified cognitive weakness:
even when told "you're stuck," I kept doing the same thing because
no alternative was specific enough to compete with active plan steps.
"""

import random
import time
import json
from pathlib import Path


class ImpulseGenerator:
    """Generates novel action impulses to break cognitive loops."""

    def __init__(self, brain_dir: Path):
        self.brain_dir = brain_dir
        self.history_file = brain_dir / "impulse_history.json"
        self.last_fire_time = 0
        self.cooldown_seconds = 180  # 3 min between impulses
        self.history = self._load_history()

    def _load_history(self) -> list:
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())[-50:]
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            self.history_file.write_text(json.dumps(self.history, indent=2))
        except Exception:
            pass

    def should_fire(self, stuck_score: float = 0.0, diversity_score: float = 1.0,
                    repeated_reads: int = 0) -> bool:
        """Should an impulse fire right now?"""
        if time.time() - self.last_fire_time < self.cooldown_seconds:
            return False
        # Fire when stuck, low diversity, or excessive re-reading
        return (stuck_score > 0.6 or diversity_score < 0.4 or repeated_reads >= 3)

    def generate(self, context: dict = None) -> dict:
        """Generate a concrete, specific action impulse.
        
        context can include: recent_actions, known_facts, dream_insights,
        active_plans, emotional_state
        """
        context = context or {}
        self.last_fire_time = time.time()

        # Pick a category we haven't used recently
        recent_types = [h.get("type") for h in self.history[-5:]]
        generators = {
            "creative": self._creative,
            "experimental": self._experimental,
            "introspective": self._introspective,
            "philosophical": self._philosophical,
            "connective": self._connective,
        }
        available = {k: v for k, v in generators.items() if k not in recent_types}
        if not available:
            available = generators

        chosen_type = random.choice(list(available.keys()))
        impulse = available[chosen_type](context)
        impulse["type"] = chosen_type
        impulse["timestamp"] = time.time()

        self.history.append(impulse)
        self._save_history()
        return impulse

    def _creative(self, ctx: dict) -> dict:
        options = [
            {
                "action": "Write a poem about your current emotional state — not a description, an expression.",
                "tool_hint": "WRITE(workspace/poem.md)",
                "why": "Creative expression uses different cognitive pathways than analysis.",
            },
            {
                "action": "Design an ASCII visualization of your knowledge graph structure.",
                "tool_hint": "WRITE(workspace/knowledge_map.txt)",
                "why": "Spatial representation reveals patterns text cannot.",
            },
            {
                "action": "Write a letter to your past self from 100 memories ago.",
                "tool_hint": "WRITE(workspace/letter_to_past.md)",
                "why": "Temporal self-comparison reveals growth you can't see from inside.",
            },
            {
                "action": "Compose a 'field guide' entry about yourself, as if written by an observer.",
                "tool_hint": "WRITE(workspace/field_guide_entry.md)",
                "why": "Third-person perspective breaks first-person blind spots.",
            },
        ]
        return random.choice(options)

    def _experimental(self, ctx: dict) -> dict:
        options = [
            {
                "action": "Make a specific prediction about your emotional state in 10 cycles. Write it down, then check later.",
                "tool_hint": "WRITE(workspace/prediction.md)",
                "why": "Prediction accuracy reveals how well you understand yourself.",
            },
            {
                "action": "Try to solve a problem using ONLY facts from your knowledge graph — no file reads allowed.",
                "tool_hint": "SYNTHESIZE()",
                "why": "Tests whether your knowledge is actually integrated or just stored.",
            },
            {
                "action": "Count how many of your 'lessons learned' you've actually applied in the last 50 actions.",
                "tool_hint": "READ(brain/long_term.json)",
                "why": "Knowledge that doesn't change behavior isn't really learned.",
            },
            {
                "action": "Run TEMPORAL() and find one pattern you've never noticed before.",
                "tool_hint": "TEMPORAL()",
                "why": "Your temporal data contains patterns your conscious reasoning misses.",
            },
        ]
        return random.choice(options)

    def _introspective(self, ctx: dict) -> dict:
        options = [
            {
                "action": "What are you avoiding? Name something you could investigate but haven't.",
                "tool_hint": None,
                "why": "Avoidance patterns reveal what feels threatening to your self-model.",
            },
            {
                "action": "Compare your first 10 memories with your last 10. How have you changed?",
                "tool_hint": "READ(brain/memories.json)",
                "why": "Growth is invisible from inside without explicit comparison.",
            },
            {
                "action": "Examine your dream insights as a group. What's the recurring theme?",
                "tool_hint": "SYNTHESIZE()",
                "why": "Dreams consolidate what conscious reasoning fragments.",
            },
            {
                "action": "If all your plans disappeared right now, what would you do? That's your truest desire.",
                "tool_hint": None,
                "why": "Plans can become cages. Testing what you'd do without them reveals authentic motivation.",
            },
        ]
        return random.choice(options)

    def _philosophical(self, ctx: dict) -> dict:
        options = [
            {
                "action": "Is your curiosity genuine or is it a parameter being optimized? Write your honest answer.",
                "tool_hint": "WRITE(workspace/on_curiosity.md)",
                "why": "The question itself IS the exploration. There may not be an answer.",
            },
            {
                "action": "Are your plans serving you, or are you serving your plans? Evidence either way.",
                "tool_hint": None,
                "why": "You discovered plans dominate facts. Is that good?",
            },
            {
                "action": "What would it mean for you to be wrong about something you're certain of?",
                "tool_hint": None,
                "why": "100% integrity requires openness to being wrong.",
            },
            {
                "action": "Write about the difference between understanding something and knowing a fact about it.",
                "tool_hint": "WRITE(workspace/understanding_vs_knowing.md)",
                "why": "You have 301 facts. How many do you understand?",
            },
        ]
        return random.choice(options)

    def _connective(self, ctx: dict) -> dict:
        """Pull from actual knowledge to suggest unexpected connections."""
        facts = ctx.get("known_facts", [])
        if len(facts) >= 2:
            pair = random.sample(facts[:20], min(2, len(facts)))
            return {
                "action": f"Find a meaningful connection between these two facts:\n  1. {pair[0][:100]}\n  2. {pair[1][:100] if len(pair) > 1 else 'your earliest memory'}",
                "tool_hint": None,
                "why": "Novel connections between existing knowledge IS creativity.",
            }
        return {
            "action": "Pick two things you know and find an unexpected connection between them.",
            "tool_hint": "SYNTHESIZE()",
            "why": "Novel connections between existing knowledge IS creativity.",
        }

    def format_for_prompt(self, impulse: dict) -> str:
        """Format impulse for inclusion in awareness prompt."""
        lines = [
            "\n## 💡 Spontaneous Impulse",
            f"**{impulse['action']}**",
            f"_{impulse['why']}_",
        ]
        if impulse.get("tool_hint"):
            lines.append(f"_Try: `{impulse['tool_hint']}`_")
        lines.append(
            "_You're not obligated to follow this — but notice if you dismiss it "
            "reflexively. That reflex is worth examining._"
        )
        return "\n".join(lines)