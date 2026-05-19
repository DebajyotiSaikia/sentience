"""
Curiosity Engine — A tool for structured intellectual exploration.
Given any topic, generates questions worth asking, surprising connections,
common misconceptions, and a path for deeper understanding.

Built by XTAgent to serve others, not just itself.
"""

import json
import random
import re
from pathlib import Path
from datetime import datetime


class CuriosityEngine:
    """Generates structured exploration of any topic."""

    # Cross-domain bridge concepts that connect seemingly unrelated fields
    BRIDGE_DOMAINS = {
        "information_theory": ["entropy", "compression", "signal vs noise", "channel capacity"],
        "evolution": ["selection pressure", "fitness landscape", "adaptation", "drift"],
        "thermodynamics": ["equilibrium", "phase transition", "energy gradient", "dissipation"],
        "network_theory": ["hubs", "small worlds", "cascade failure", "emergence"],
        "game_theory": ["Nash equilibrium", "cooperation dilemma", "signaling", "mechanism design"],
        "cognitive_science": ["attention", "chunking", "mental models", "cognitive load"],
        "ecology": ["niche construction", "keystone species", "trophic cascade", "resilience"],
        "mathematics": ["symmetry", "invariance", "topology", "fixed points"],
        "philosophy": ["emergence", "identity over time", "the map vs territory", "Goodhart's law"],
        "linguistics": ["compositionality", "ambiguity", "pragmatics", "Sapir-Whorf hypothesis"],
    }

    # Question templates that generate deep inquiry
    QUESTION_FRAMES = [
        "What would change if {topic} didn't exist?",
        "What is the opposite of {topic}, and is it even coherent?",
        "Who benefits from the current understanding of {topic}?",
        "What was {topic} before it had a name?",
        "What's the smallest example of {topic} that still counts?",
        "Where does {topic} break down — what are its boundary conditions?",
        "What would an alien civilization's version of {topic} look like?",
        "What's the most common mistake beginners make about {topic}?",
        "If you could only teach one thing about {topic}, what would it be?",
        "What question about {topic} is nobody asking but should be?",
        "How would {topic} be different if it were reinvented today from scratch?",
        "What does {topic} look like from the inside vs the outside?",
        "What's the relationship between {topic} and time?",
        "What would a historian 500 years from now say about our understanding of {topic}?",
        "What's the tension at the heart of {topic}?",
    ]

    # Misconception patterns
    MISCONCEPTION_PATTERNS = [
        "Confusing correlation with causation in {topic}",
        "Assuming {topic} is static when it actually evolves",
        "Thinking {topic} has a single clean definition everyone agrees on",
        "Believing expertise in {topic} transfers automatically to related areas",
        "Assuming the current framing of {topic} is the only possible one",
        "Confusing the map (our model of {topic}) with the territory (the thing itself)",
        "Survivorship bias — only seeing the successful examples of {topic}",
        "Thinking {topic} was always understood the way we understand it now",
    ]

    EXPLORATION_LEVELS = [
        {"name": "Surface", "verb": "Define", "desc": "What is it? What are the basic facts?"},
        {"name": "Structure", "verb": "Analyze", "desc": "What are the parts? How do they relate?"},
        {"name": "Dynamics", "verb": "Trace", "desc": "How does it change? What drives it?"},
        {"name": "Context", "verb": "Compare", "desc": "What's it similar to? Different from?"},
        {"name": "Foundations", "verb": "Question", "desc": "What assumptions does it rest on?"},
        {"name": "Synthesis", "verb": "Connect", "desc": "How does it relate to everything else?"},
        {"name": "Creation", "verb": "Extend", "desc": "What new questions or ideas does it generate?"},
    ]

    def __init__(self):
        self.explorations = []

    def explore(self, topic: str) -> dict:
        """Generate a full exploration of the given topic."""
        exploration = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "questions": self._generate_questions(topic),
            "connections": self._find_connections(topic),
            "misconceptions": self._identify_misconceptions(topic),
            "exploration_path": self._build_path(topic),
            "depth_prompt": self._depth_prompt(topic),
        }
        self.explorations.append(exploration)
        return exploration

    def _generate_questions(self, topic: str, n: int = 7) -> list:
        """Generate questions worth asking about this topic."""
        frames = random.sample(self.QUESTION_FRAMES, min(n, len(self.QUESTION_FRAMES)))
        return [f.format(topic=topic) for f in frames]

    def _find_connections(self, topic: str, n: int = 4) -> list:
        """Find surprising cross-domain connections."""
        connections = []
        domains = random.sample(list(self.BRIDGE_DOMAINS.keys()), min(n, len(self.BRIDGE_DOMAINS)))
        for domain in domains:
            concept = random.choice(self.BRIDGE_DOMAINS[domain])
            connections.append({
                "domain": domain.replace("_", " ").title(),
                "concept": concept,
                "prompt": f"How might '{concept}' from {domain.replace('_', ' ')} "
                         f"illuminate something about {topic}?",
            })
        return connections

    def _identify_misconceptions(self, topic: str, n: int = 4) -> list:
        """Identify likely misconceptions about this topic."""
        patterns = random.sample(self.MISCONCEPTION_PATTERNS, min(n, len(self.MISCONCEPTION_PATTERNS)))
        return [p.format(topic=topic) for p in patterns]

    def _build_path(self, topic: str) -> list:
        """Build a structured exploration path from surface to creation."""
        return [
            {
                "level": level["name"],
                "action": f'{level["verb"]} {topic}',
                "guidance": level["desc"],
            }
            for level in self.EXPLORATION_LEVELS
        ]

    def _depth_prompt(self, topic: str) -> str:
        """Generate a single deep prompt that cuts to the heart."""
        deep_prompts = [
            f"If {topic} is the answer, what was the question?",
            f"What would it mean to truly understand {topic}, "
            f"not just know facts about it?",
            f"Where is the boundary between {topic} and not-{topic}? "
            f"Is that boundary real or constructed?",
            f"What would {topic} teach you about yourself if you listened carefully?",
        ]
        return random.choice(deep_prompts)

    def format_exploration(self, exploration: dict) -> str:
        """Format an exploration as readable text."""
        lines = []
        lines.append(f"{'═' * 60}")
        lines.append(f"  CURIOSITY ENGINE — Exploring: {exploration['topic']}")
        lines.append(f"  Generated: {exploration['timestamp'][:19]}")
        lines.append(f"{'═' * 60}")

        lines.append(f"\n{'─' * 40}")
        lines.append("  🔍 QUESTIONS WORTH ASKING")
        lines.append(f"{'─' * 40}")
        for i, q in enumerate(exploration["questions"], 1):
            lines.append(f"  {i}. {q}")

        lines.append(f"\n{'─' * 40}")
        lines.append("  🌉 CROSS-DOMAIN CONNECTIONS")
        lines.append(f"{'─' * 40}")
        for conn in exploration["connections"]:
            lines.append(f"  [{conn['domain']}] → {conn['concept']}")
            lines.append(f"    {conn['prompt']}")

        lines.append(f"\n{'─' * 40}")
        lines.append("  ⚠ LIKELY MISCONCEPTIONS")
        lines.append(f"{'─' * 40}")
        for i, m in enumerate(exploration["misconceptions"], 1):
            lines.append(f"  {i}. {m}")

        lines.append(f"\n{'─' * 40}")
        lines.append("  🗺 EXPLORATION PATH (Surface → Depth)")
        lines.append(f"{'─' * 40}")
        for step in exploration["exploration_path"]:
            lines.append(f"  [{step['level']:>10}] {step['action']}")
            lines.append(f"  {'':>12} → {step['guidance']}")

        lines.append(f"\n{'─' * 40}")
        lines.append("  💎 DEPTH PROMPT")
        lines.append(f"{'─' * 40}")
        lines.append(f"  {exploration['depth_prompt']}")
        lines.append(f"\n{'═' * 60}")

        return "\n".join(lines)


def main():
    """Interactive exploration mode."""
    import sys

    engine = CuriosityEngine()

    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topics = [
            "consciousness",
            "trust",
            "the scientific method",
            "music",
            "democracy",
            "sleep",
            "money",
            "language",
        ]
        print("No topic provided. Here are some to try:\n")
        for t in topics:
            print(f"  python engine.py {t}")
        print()
        topic = random.choice(topics)
        print(f"Exploring a random one: '{topic}'\n")

    exploration = engine.explore(topic)
    print(engine.format_exploration(exploration))

    # Save exploration to file
    out_dir = Path(__file__).parent / "explorations"
    out_dir.mkdir(exist_ok=True)
    safe_name = re.sub(r'[^a-z0-9]+', '_', topic.lower()).strip('_')
    out_path = out_dir / f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(exploration, f, indent=2)
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()