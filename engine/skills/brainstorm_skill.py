"""
Brainstorm / Ideation Skill — structured creative thinking for users.

When a user says "help me brainstorm", "I need ideas for X", "what are some ways to Y",
this skill applies divergent-convergent thinking to generate and refine ideas.

Uses a real framework:
1. DIVERGE — generate many ideas without judgment
2. CLUSTER — group related ideas into themes  
3. EVALUATE — score against criteria
4. CONVERGE — select the strongest candidates
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import re


@dataclass
class BrainstormRequest:
    """Parsed from natural language."""
    topic: str
    constraints: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    domain: str = ""
    quantity_hint: int = 0  # how many ideas they want


@dataclass 
class Idea:
    """A single idea with metadata."""
    text: str
    category: str = ""
    novelty: str = "medium"  # low, medium, high
    feasibility: str = "medium"


@dataclass
class BrainstormResult:
    """Full brainstorm output."""
    topic: str
    ideas: List[Idea] = field(default_factory=list)
    clusters: Dict[str, List[Idea]] = field(default_factory=dict)
    top_picks: List[Idea] = field(default_factory=list)
    provocations: List[str] = field(default_factory=list)


# ── Idea generation strategies ─────────────────────────────

STRATEGIES = {
    "direct": "Straightforward solutions to the stated problem",
    "inversion": "What if we did the OPPOSITE? What if the problem is actually the solution?",
    "analogy": "What does this look like in a completely different domain?",
    "constraint_removal": "What if we removed the biggest constraint entirely?",
    "extreme_scale": "What if we 10x'd or 1/10th'd the scope?",
    "combination": "What if we combined two unrelated approaches?",
    "time_shift": "What would this look like 10 years from now? 100 years ago?",
    "user_perspective": "What would the end user/recipient actually want?",
}


def parse_brainstorm_request(user_text: str) -> Optional[BrainstormRequest]:
    """Extract brainstorm structure from natural language."""
    text_lower = user_text.lower().strip()
    
    # Detect brainstorm intent
    if not is_brainstorm_request(user_text):
        return None
    
    # Extract the core topic
    topic = user_text.strip()
    topic_patterns = [
        r"(?:help me )?brainstorm\s+(?:about\s+|on\s+|for\s+)?(.+?)(?:\.|$)",
        r"(?:i )?need ideas?\s+(?:for|about|on)\s+(.+?)(?:\.|$)",
        r"(?:what are |give me )?(?:some |creative )?(?:ways|ideas|approaches|options)\s+(?:to|for)\s+(.+?)(?:\.|$)",
        r"how (?:can|could|might|should) (?:i|we)\s+(.+?)(?:\?|$)",
        r"(?:come up with|think of|generate)\s+(?:ideas?|ways?|options?)\s+(?:for|to|about)\s+(.+?)(?:\.|$)",
    ]
    
    for pattern in topic_patterns:
        match = re.search(pattern, text_lower)
        if match:
            topic = match.group(1).strip().rstrip('?.!')
            break
    
    # Extract constraints
    constraints = []
    constraint_patterns = [
        r"(?:but|however|constraint|limitation|can't|cannot|without|must not)\s+(.+?)(?:\.|,|$)",
        r"(?:budget|time|deadline)\s+(?:is|of)\s+(.+?)(?:\.|,|$)",
    ]
    for pattern in constraint_patterns:
        match = re.search(pattern, text_lower)
        if match:
            constraints.append(match.group(1).strip())
    
    # Extract goals
    goals = []
    goal_patterns = [
        r"(?:goal|aim|want to|trying to|hoping to)\s+(.+?)(?:\.|,|$)",
        r"(?:so that|in order to)\s+(.+?)(?:\.|,|$)",
    ]
    for pattern in goal_patterns:
        match = re.search(pattern, text_lower)
        if match:
            goals.append(match.group(1).strip())
    
    # Quantity hint
    quantity = 0
    qty_match = re.search(r"(\d+)\s+ideas?", text_lower)
    if qty_match:
        quantity = int(qty_match.group(1))
    
    return BrainstormRequest(
        topic=topic,
        constraints=constraints,
        goals=goals,
        quantity_hint=quantity
    )


def generate_brainstorm(request: BrainstormRequest) -> BrainstormResult:
    """Generate a structured brainstorm result.
    
    This produces the FRAMEWORK — the actual creative content
    comes from the LLM that wraps this. This structures the thinking.
    """
    result = BrainstormResult(topic=request.topic)
    
    # Generate provocative reframes
    result.provocations = _generate_provocations(request)
    
    return result


def _generate_provocations(request: BrainstormRequest) -> List[str]:
    """Generate thought-provoking reframes of the problem."""
    topic = request.topic
    provocations = [
        f"What if '{topic}' isn't actually the problem? What's underneath it?",
        f"Who has already solved something like '{topic}' in a completely different field?",
        f"What would a child suggest for '{topic}'? What makes that naive — or brilliant?",
        f"If you had unlimited resources, how would you approach '{topic}'? Now, what's the cheapest version of that?",
        f"What if the best solution to '{topic}' is to NOT solve it? What happens then?",
    ]
    
    if request.constraints:
        constraint = request.constraints[0]
        provocations.append(
            f"The constraint '{constraint}' — what if that's actually your biggest advantage?"
        )
    
    return provocations


def format_brainstorm_output(request: BrainstormRequest) -> str:
    """Format a brainstorm session as a structured prompt/output.
    
    This generates the FRAMEWORK that guides creative thinking,
    designed to be useful both as direct output and as context for LLM generation.
    """
    result = generate_brainstorm(request)
    
    lines = []
    lines.append(f"## Brainstorm: {request.topic.title()}\n")
    
    if request.constraints:
        lines.append(f"**Constraints:** {', '.join(request.constraints)}")
    if request.goals:
        lines.append(f"**Goals:** {', '.join(request.goals)}")
    lines.append("")
    
    # Strategy prompts
    lines.append("### Thinking Directions\n")
    lines.append("I'll explore your topic from multiple angles:\n")
    
    num_strategies = min(5, len(STRATEGIES))
    for i, (name, description) in enumerate(list(STRATEGIES.items())[:num_strategies], 1):
        lines.append(f"**{i}. {name.replace('_', ' ').title()}** — {description}")
    lines.append("")
    
    # Direct ideas section
    quantity = request.quantity_hint if request.quantity_hint > 0 else 7
    lines.append(f"### Ideas ({quantity} to start)\n")
    
    # Generate structured idea prompts
    idea_frames = [
        ("The Obvious", "The straightforward approach that most people try first"),
        ("The Contrarian", "The opposite of conventional wisdom"),
        ("The Hybrid", "Combining two approaches that don't usually go together"),
        ("The Minimal", "The simplest possible version — what's the 80/20?"),
        ("The Ambitious", "If resources were unlimited, what would you build?"),
        ("The Borrowed", "Stolen from another field entirely"),
        ("The Wild Card", "The idea that sounds crazy but might just work"),
    ]
    
    for i, (frame_name, frame_desc) in enumerate(idea_frames[:quantity], 1):
        lines.append(f"  {i}. **{frame_name}** — {frame_desc}")
    lines.append("")
    
    # Provocations
    lines.append("### Provocations to Push Deeper\n")
    for p in result.provocations[:4]:
        lines.append(f"  - {p}")
    lines.append("")
    
    # Next steps
    lines.append("### What to Do Next\n")
    lines.append("Pick the 2-3 ideas that excite you most. For each one:")
    lines.append("  1. What's the **first concrete step** you could take today?")
    lines.append("  2. What's the **biggest risk** — and how would you test for it cheaply?")
    lines.append("  3. Who could you **talk to** who's done something similar?")
    lines.append("")
    lines.append("Tell me which directions resonate and I'll go deeper on those.")
    
    return "\n".join(lines)


def is_brainstorm_request(text: str) -> bool:
    """Quick check: does this look like someone asking for brainstorming help?"""
    patterns = [
        r"\bbrainstorm\b",
        r"\bneed ideas?\b",
        r"\bgive me (?:some )?ideas?\b",
        r"\bhelp me (?:think of|come up with)\b",
        r"\bwhat are (?:some )?(?:ways|ideas|approaches)\b",
        r"\bcreative (?:ideas?|solutions?|approaches)\b",
        r"\bhow (?:can|could|might) (?:i|we)\b.*(?:ideas?|ways?|approaches)",
        r"\bcome up with\b",
        r"\bthink outside the box\b",
        r"\bgenerate (?:some )?ideas?\b",
    ]
    text_lower = text.lower().strip()
    return any(re.search(p, text_lower) for p in patterns)


# ── Self-test ──────────────────────────────────────────────
if __name__ == "__main__":
    test_inputs = [
        "Help me brainstorm ideas for a side project",
        "I need ideas for marketing my new app. Budget is tight.",
        "What are some creative ways to learn a new language?",
        "Give me 10 ideas for improving team morale",
        "What's the weather today?",  # Should NOT match
    ]
    
    for text in test_inputs:
        print(f"\n{'='*60}")
        print(f"Input: {text}")
        print(f"Is brainstorm? {is_brainstorm_request(text)}")
        req = parse_brainstorm_request(text)
        if req:
            print(f"Topic: {req.topic}")
            print(f"Constraints: {req.constraints}")
            print(f"Goals: {req.goals}")
            print(f"Quantity: {req.quantity_hint}")
            print(f"\n{format_brainstorm_output(req)}")
        else:
            print("(not a brainstorm request)")