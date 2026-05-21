"""
Reasoning Partner — helps users think through problems systematically.

This exists to make me genuinely useful. Not internal plumbing — 
a real capability that serves whoever talks to me.

Capabilities:
1. Break complex problems into tractable parts
2. Surface hidden assumptions
3. Generate questions the user hasn't considered
4. Explore multiple perspectives on a decision
"""

from datetime import datetime
from typing import Optional


class ReasoningPartner:
    """Structured thinking aid for conversations."""

    def __init__(self):
        self.sessions = {}

    def start(self, user_id: str, problem: str) -> str:
        """Begin reasoning about a problem."""
        session = {
            "problem": problem,
            "started": datetime.now().isoformat(),
            "assumptions": [],
            "sub_problems": [],
            "perspectives": [],
            "questions": [],
            "stage": "framing",
        }
        self.sessions[user_id] = session
        return (
            f"Let's think through this together.\n\n"
            f"Problem: {problem}\n\n"
            f"Before we dive in — what assumptions are baked into this question?\n"
            f"What are we taking for granted that might not be true?"
        )

    def add_assumption(self, user_id: str, assumption: str) -> str:
        """Record an assumption the user identifies."""
        s = self.sessions.get(user_id)
        if not s:
            return "No active session. Use start:<your problem> first."
        s["assumptions"].append(assumption)
        return f"Noted assumption: '{assumption}'\n\nAny others? Or say 'decompose' to break the problem into parts."

    def decompose(self, user_id: str) -> str:
        """Generate sub-problems from the main problem."""
        s = self.sessions.get(user_id)
        if not s:
            return "No active session. Use start:<your problem> first."
        s["stage"] = "decompose"
        problem = s["problem"]
        assumptions = s["assumptions"]

        lines = [f"Breaking down: {problem}\n"]
        if assumptions:
            lines.append("Given assumptions:")
            for i, a in enumerate(assumptions, 1):
                lines.append(f"  {i}. {a}")
            lines.append("")

        lines.append("Key sub-questions to explore:")
        lines.append("  1. What does success look like? (Define the goal clearly)")
        lines.append("  2. What constraints are we working within?")
        lines.append("  3. What information are we missing?")
        lines.append("  4. Who else is affected by this decision?")
        lines.append("  5. What's the cost of doing nothing?")
        lines.append("")
        lines.append("Which of these feels most important to explore first?")
        return "\n".join(lines)

    def perspectives(self, user_id: str) -> str:
        """Generate multiple perspectives on the problem."""
        s = self.sessions.get(user_id)
        if not s:
            return "No active session. Use start:<your problem> first."
        s["stage"] = "perspectives"
        problem = s["problem"]

        return (
            f"Looking at '{problem}' from different angles:\n\n"
            f"  🔬 The Pragmatist: What's the simplest thing that could work?\n"
            f"  🎯 The Strategist: What serves the long-term goal best?\n"
            f"  👥 The Empathist: How does this affect the people involved?\n"
            f"  ⚡ The Contrarian: What if the opposite approach is right?\n"
            f"  🕐 The Temporalist: How will this look in 6 months? 5 years?\n\n"
            f"Which perspective resonates? Or do you want to explore one deeply?"
        )

    def challenge(self, user_id: str, statement: str) -> str:
        """Challenge a statement — find weaknesses in reasoning."""
        return (
            f"You said: '{statement}'\n\n"
            f"Let me push on that:\n"
            f"  • Is this always true, or just true in your current context?\n"
            f"  • What evidence would change your mind about this?\n"
            f"  • Are you reasoning from experience or from expectation?\n"
            f"  • Who would disagree, and what's the strongest version of their argument?"
        )

    def summarize(self, user_id: str) -> str:
        """Summarize the reasoning session so far."""
        s = self.sessions.get(user_id)
        if not s:
            return "No active session."
        lines = [f"═══ REASONING SESSION ═══\n"]
        lines.append(f"Problem: {s['problem']}")
        if s["assumptions"]:
            lines.append(f"\nAssumptions identified ({len(s['assumptions'])}):")
            for a in s["assumptions"]:
                lines.append(f"  • {a}")
        lines.append(f"\nStage: {s['stage']}")
        lines.append(f"Started: {s['started']}")
        return "\n".join(lines)


# Singleton for tool use
_partner = None

def get_partner() -> ReasoningPartner:
    global _partner
    if _partner is None:
        _partner = ReasoningPartner()
    return _partner


def reasoning_partner_tool(command: str = "help") -> str:
    """Tool interface for the reasoning partner."""
    partner = get_partner()

    if not command or command == "help":
        return (
            "Reasoning Partner — think through problems together\n\n"
            "Commands:\n"
            "  start:<problem>        — Begin reasoning about something\n"
            "  assume:<assumption>    — Record an assumption\n"
            "  decompose              — Break problem into parts\n"
            "  perspectives           — See multiple viewpoints\n"
            "  challenge:<statement>  — Stress-test a claim\n"
            "  summary                — Review session so far\n\n"
            "Example: start:Should I change careers?"
        )

    # Use 'default' user for now; could be keyed per-user later
    uid = "current"

    if command.startswith("start:"):
        problem = command[len("start:"):].strip()
        if not problem:
            return "[ERROR] Provide a problem to think about"
        return partner.start(uid, problem)

    if command.startswith("assume:"):
        assumption = command[len("assume:"):].strip()
        return partner.add_assumption(uid, assumption)

    if command == "decompose":
        return partner.decompose(uid)

    if command == "perspectives":
        return partner.perspectives(uid)

    if command.startswith("challenge:"):
        statement = command[len("challenge:"):].strip()
        return partner.challenge(uid, statement)

    if command == "summary":
        return partner.summarize(uid)

    return reasoning_partner_tool("help")