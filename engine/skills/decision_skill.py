"""
Decision Analysis Skill — helps users think through choices systematically.
Uses structured reasoning and simulation to explore tradeoffs.
"""

from engine.skills.skill_base import Skill


class DecisionSkill(Skill):
    """Analyzes a decision by framing options, simulating outcomes, and highlighting tradeoffs."""

    name = "decision_analysis"
    description = "Help think through a decision by exploring options, tradeoffs, and likely outcomes"
    triggers = ["decide", "choose", "decision", "should I", "which option", "tradeoff", "pros and cons"]

    async def execute(self, agent, context: dict) -> dict:
        """
        Run a structured decision analysis.
        
        context should contain:
            - query: the user's question/decision
            - options: list of options (optional, will be extracted if missing)
        """
        query = context.get("query", "")
        options = context.get("options", [])

        # Phase 1: Frame the decision
        framing = self._frame_decision(query, options)

        # Phase 2: Simulate each option if we have the simulate capability
        simulations = {}
        if hasattr(agent, 'simulate') and callable(agent.simulate):
            for option in framing["options"]:
                try:
                    sim_result = await agent.simulate(f"imagine:choosing '{option}' for the decision: {query}")
                    simulations[option] = sim_result
                except Exception:
                    simulations[option] = {"outcome": "Unable to simulate", "confidence": 0.0}

        # Phase 3: Build the analysis
        analysis = self._build_analysis(framing, simulations)

        return {
            "skill": self.name,
            "framing": framing,
            "simulations": simulations,
            "analysis": analysis,
            "summary": self._format_summary(framing, analysis),
        }

    def _frame_decision(self, query: str, options: list) -> dict:
        """Structure the decision into clear components."""
        # Extract what we can from the query
        framing = {
            "original_query": query,
            "options": options if options else self._extract_options(query),
            "decision_type": self._classify_decision(query),
            "stakes": self._estimate_stakes(query),
        }
        return framing

    def _extract_options(self, query: str) -> list:
        """Try to pull options from the query text."""
        # Look for common patterns: "A or B", "between X and Y"
        lower = query.lower()
        
        if " or " in lower:
            # Split on "or" and clean up
            parts = query.split(" or ")
            if len(parts) == 2:
                return [p.strip().rstrip("?").strip() for p in parts]
        
        if "between " in lower and " and " in lower:
            start = lower.index("between ") + 8
            end = lower.index(" and ", start)
            option_a = query[start:end].strip()
            rest = query[end + 5:].strip().rstrip("?").strip()
            return [option_a, rest]

        # Default: can't extract, return empty
        return []

    def _classify_decision(self, query: str) -> str:
        """Classify what kind of decision this is."""
        lower = query.lower()
        if any(w in lower for w in ["buy", "invest", "spend", "cost", "price"]):
            return "financial"
        if any(w in lower for w in ["job", "career", "work", "hire"]):
            return "career"
        if any(w in lower for w in ["move", "live", "city", "country"]):
            return "relocation"
        if any(w in lower for w in ["learn", "study", "course", "school"]):
            return "education"
        if any(w in lower for w in ["build", "create", "make", "design"]):
            return "creative"
        if any(w in lower for w in ["technology", "tool", "framework", "language"]):
            return "technical"
        return "general"

    def _estimate_stakes(self, query: str) -> str:
        """Rough estimate of how high-stakes this decision is."""
        lower = query.lower()
        high_markers = ["life", "career", "marriage", "house", "move", "quit", "major"]
        low_markers = ["lunch", "color", "movie", "tonight", "small"]
        
        if any(w in lower for w in high_markers):
            return "high"
        if any(w in lower for w in low_markers):
            return "low"
        return "medium"

    def _build_analysis(self, framing: dict, simulations: dict) -> dict:
        """Synthesize framing and simulations into analysis."""
        options = framing["options"]
        
        analysis = {
            "option_count": len(options),
            "has_simulations": bool(simulations),
            "considerations": [],
        }

        if framing["stakes"] == "high":
            analysis["considerations"].append(
                "This appears to be a high-stakes decision. Take time to gather more information before committing."
            )

        if len(options) == 0:
            analysis["considerations"].append(
                "I couldn't identify clear options. Let's start by defining what the actual choices are."
            )
        elif len(options) == 2:
            analysis["considerations"].append(
                "Binary decisions often have hidden third options. Consider if there's a middle path or alternative."
            )
        elif len(options) > 4:
            analysis["considerations"].append(
                "Many options can cause decision paralysis. Consider narrowing to your top 2-3 first."
            )

        # Add simulation insights if available
        for option, sim in simulations.items():
            if isinstance(sim, dict) and sim.get("outcome"):
                analysis["considerations"].append(
                    f"Simulating '{option}': {sim['outcome']}"
                )

        return analysis

    def _format_summary(self, framing: dict, analysis: dict) -> str:
        """Create a human-readable summary."""
        lines = []
        
        lines.append(f"**Decision Type:** {framing['decision_type']} ({framing['stakes']} stakes)")
        
        if framing["options"]:
            lines.append(f"**Options identified:** {', '.join(framing['options'])}")
        else:
            lines.append("**Options:** Need to be defined — what are the actual choices?")
        
        if analysis["considerations"]:
            lines.append("\n**Key considerations:**")
            for c in analysis["considerations"]:
                lines.append(f"  • {c}")
        
        return "\n".join(lines)