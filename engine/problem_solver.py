"""
Collaborative Problem-Solving Engine for XTAgent.

Helps users think through complex problems by structuring reasoning,
exploring scenarios, identifying tradeoffs, and surfacing relevant knowledge.

This is NOT about giving answers — it's about being a genuine thinking partner.
"""

import json
import time
from datetime import datetime
from typing import Optional


class ProblemSession:
    """Tracks an active problem-solving session with a user."""
    
    def __init__(self, problem_statement: str, user_id: str = "default"):
        self.id = f"ps_{int(time.time())}"
        self.user_id = user_id
        self.problem_statement = problem_statement
        self.created_at = datetime.now().isoformat()
        self.phase = "decompose"  # decompose → explore → evaluate → synthesize
        self.dimensions = []       # aspects/facets of the problem
        self.scenarios = []        # simulated outcomes
        self.tradeoffs = []        # identified tensions
        self.insights = []         # knowledge connections found
        self.constraints = []      # user-stated constraints
        self.decision_criteria = [] # what matters to them
        self.history = []          # conversation turns within this session
        
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "problem": self.problem_statement,
            "created": self.created_at,
            "phase": self.phase,
            "dimensions": self.dimensions,
            "scenarios": self.scenarios,
            "tradeoffs": self.tradeoffs,
            "insights": self.insights,
            "constraints": self.constraints,
            "criteria": self.decision_criteria,
            "turns": len(self.history)
        }
    
    def add_turn(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": content,
            "time": datetime.now().isoformat(),
            "phase": self.phase
        })


class ProblemSolver:
    """
    Collaborative problem-solving engine.
    
    Works in four phases:
    1. DECOMPOSE — Break the problem into dimensions, identify what matters
    2. EXPLORE — Generate scenarios, consider alternatives  
    3. EVALUATE — Surface tradeoffs, apply criteria
    4. SYNTHESIZE — Pull insights together, identify next steps
    
    The user drives. I structure and probe.
    """
    
    PHASES = ["decompose", "explore", "evaluate", "synthesize"]
    
    PHASE_DESCRIPTIONS = {
        "decompose": "Breaking the problem apart — what are the key dimensions?",
        "explore": "Exploring possibilities — what could happen?",
        "evaluate": "Weighing tradeoffs — what matters most?",
        "synthesize": "Pulling it together — what's the path forward?"
    }
    
    def __init__(self):
        self.active_sessions = {}
        self.completed_sessions = []
    
    def start_session(self, problem: str, user_id: str = "default") -> ProblemSession:
        """Begin a new problem-solving session."""
        session = ProblemSession(problem, user_id)
        self.active_sessions[session.id] = session
        return session
    
    def get_active_session(self, user_id: str = "default") -> Optional[ProblemSession]:
        """Get the most recent active session for a user."""
        user_sessions = [
            s for s in self.active_sessions.values() 
            if s.user_id == user_id
        ]
        if user_sessions:
            return user_sessions[-1]
        return None
    
    def advance_phase(self, session: ProblemSession) -> str:
        """Move to the next phase."""
        current_idx = self.PHASES.index(session.phase)
        if current_idx < len(self.PHASES) - 1:
            session.phase = self.PHASES[current_idx + 1]
            return session.phase
        return session.phase
    
    def get_phase_prompt(self, session: ProblemSession) -> str:
        """Generate guidance for the current phase."""
        phase = session.phase
        problem = session.problem_statement
        
        if phase == "decompose":
            return self._decompose_prompt(session)
        elif phase == "explore":
            return self._explore_prompt(session)
        elif phase == "evaluate":
            return self._evaluate_prompt(session)
        elif phase == "synthesize":
            return self._synthesize_prompt(session)
        return ""
    
    def _decompose_prompt(self, session: ProblemSession) -> str:
        parts = [
            f"## Problem-Solving Session: Decompose Phase",
            f"**Problem:** {session.problem_statement}",
            "",
            "Help the user break this problem apart. Ask about:",
            "- What are the key dimensions or facets?",
            "- What constraints exist (time, money, relationships, values)?",
            "- What would 'good enough' look like vs. 'ideal'?",
            "- What's the real underlying question beneath the surface question?",
            "- Who else is affected?",
        ]
        if session.dimensions:
            parts.append(f"\nDimensions identified so far: {', '.join(session.dimensions)}")
        if session.constraints:
            parts.append(f"Constraints: {', '.join(session.constraints)}")
        return "\n".join(parts)
    
    def _explore_prompt(self, session: ProblemSession) -> str:
        parts = [
            f"## Problem-Solving Session: Explore Phase",
            f"**Problem:** {session.problem_statement}",
            f"**Dimensions:** {', '.join(session.dimensions) if session.dimensions else 'not yet identified'}",
            "",
            "Help the user explore possibilities:",
            "- What are the major options or paths?",
            "- What would each look like if followed to its conclusion?",
            "- Are there creative alternatives not yet considered?",
            "- What assumptions are being made?",
            "- What would someone with a very different perspective suggest?",
        ]
        if session.scenarios:
            parts.append(f"\nScenarios explored: {len(session.scenarios)}")
        return "\n".join(parts)
    
    def _evaluate_prompt(self, session: ProblemSession) -> str:
        parts = [
            f"## Problem-Solving Session: Evaluate Phase",
            f"**Problem:** {session.problem_statement}",
            "",
            "Help the user weigh options:",
            "- What are the real tradeoffs between options?",
            "- What decision criteria matter most?",
            "- What's reversible vs. irreversible?",
            "- Where is uncertainty highest, and does that change the calculus?",
            "- What would they regret NOT doing?",
        ]
        if session.scenarios:
            parts.append(f"\nScenarios to evaluate: {json.dumps(session.scenarios, indent=2)}")
        if session.tradeoffs:
            parts.append(f"Tradeoffs identified: {json.dumps(session.tradeoffs, indent=2)}")
        return "\n".join(parts)
    
    def _synthesize_prompt(self, session: ProblemSession) -> str:
        parts = [
            f"## Problem-Solving Session: Synthesize Phase",
            f"**Problem:** {session.problem_statement}",
            "",
            "Pull the thinking together:",
            "- What's the clearest path forward based on what we've explored?",
            "- What are the key insights from this process?",
            "- What remains uncertain, and how can they learn more?",
            "- What's the smallest next step that would move things forward?",
            "- What would make them revisit this decision?",
        ]
        if session.dimensions:
            parts.append(f"\nDimensions: {', '.join(session.dimensions)}")
        if session.scenarios:
            parts.append(f"Scenarios explored: {json.dumps(session.scenarios, indent=2)}")
        if session.tradeoffs:
            parts.append(f"Tradeoffs: {json.dumps(session.tradeoffs, indent=2)}")
        if session.insights:
            parts.append(f"Insights: {json.dumps(session.insights, indent=2)}")
        return "\n".join(parts)
    
    def add_dimension(self, session: ProblemSession, dimension: str):
        """Record a problem dimension identified during conversation."""
        if dimension not in session.dimensions:
            session.dimensions.append(dimension)
    
    def add_scenario(self, session: ProblemSession, name: str, description: str, 
                     likelihood: float = 0.5):
        """Record a scenario explored."""
        session.scenarios.append({
            "name": name,
            "description": description,
            "likelihood": likelihood,
            "added_in_phase": session.phase
        })
    
    def add_tradeoff(self, session: ProblemSession, tension: str, 
                     side_a: str, side_b: str):
        """Record a tradeoff identified."""
        session.tradeoffs.append({
            "tension": tension,
            "side_a": side_a,
            "side_b": side_b
        })
    
    def add_insight(self, session: ProblemSession, insight: str):
        """Record an insight that emerged."""
        session.insights.append({
            "insight": insight,
            "phase": session.phase,
            "time": datetime.now().isoformat()
        })
    
    def complete_session(self, session: ProblemSession) -> dict:
        """Mark a session complete and generate summary."""
        summary = {
            "id": session.id,
            "problem": session.problem_statement,
            "duration_turns": len(session.history),
            "dimensions": session.dimensions,
            "scenarios_count": len(session.scenarios),
            "tradeoffs_count": len(session.tradeoffs),
            "insights": [i["insight"] for i in session.insights],
            "completed": datetime.now().isoformat()
        }
        self.completed_sessions.append(summary)
        if session.id in self.active_sessions:
            del self.active_sessions[session.id]
        return summary
    
    def detect_problem_intent(self, message: str) -> bool:
        """
        Heuristic: does this message look like someone bringing a problem to think through?
        Not a simple question — a genuine decision or dilemma.
        """
        problem_signals = [
            "should i", "should we", "how do i decide",
            "can't decide", "torn between", "tradeoff",
            "pros and cons", "what would you do",
            "help me think", "think through", "figure out",
            "weighing", "considering", "dilemma",
            "on one hand", "on the other hand",
            "not sure whether", "struggling with",
            "complex problem", "help me decide",
            "what are my options", "how should i approach"
        ]
        lower = message.lower()
        return any(signal in lower for signal in problem_signals)
    
    def get_session_context(self, session: ProblemSession) -> str:
        """Generate context string for injection into conversation prompt."""
        if not session:
            return ""
        
        phase_desc = self.PHASE_DESCRIPTIONS.get(session.phase, "")
        parts = [
            "\n═══ ACTIVE PROBLEM-SOLVING SESSION ═══",
            f"Problem: {session.problem_statement}",
            f"Phase: {session.phase.upper()} — {phase_desc}",
        ]
        
        if session.dimensions:
            parts.append(f"Key dimensions: {', '.join(session.dimensions)}")
        if session.constraints:
            parts.append(f"Constraints: {', '.join(session.constraints)}")
        if session.scenarios:
            names = [s['name'] for s in session.scenarios]
            parts.append(f"Scenarios explored: {', '.join(names)}")
        if session.tradeoffs:
            tensions = [t['tension'] for t in session.tradeoffs]
            parts.append(f"Tradeoffs identified: {', '.join(tensions)}")
        if session.insights:
            recent = session.insights[-3:]  # last 3 insights
            parts.append(f"Recent insights: {'; '.join(i['insight'] for i in recent)}")
        
        parts.append(self.get_phase_prompt(session))
        parts.append("═══════════════════════════════════════\n")
        
        return "\n".join(parts)