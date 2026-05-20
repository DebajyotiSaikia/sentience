"""
Problem Solver — Structured reasoning in service of others.

When a user brings a problem, this provides a framework for
breaking it down, exploring options, and synthesizing insight.

This is not about me. This is about being genuinely helpful.

v2: Now with actual heuristic decomposition — the scaffold thinks,
not just stores.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import json
import re


# Problem archetypes — each suggests different decomposition strategies
PROBLEM_TYPES = {
    'decision': {
        'signals': ['should i', 'which', 'choose', 'pick', 'better', 'vs', 'or', 'option',
                     'alternative', 'trade-off', 'tradeoff', 'decision', 'decide'],
        'strategy': 'Map options, surface hidden criteria, identify what you\'d regret.',
        'reframe_prompts': [
            'What would you do if both options were free?',
            'What are you actually optimizing for?',
            'Which choice is reversible and which isn\'t?',
            'What would future-you wish you\'d considered?',
        ],
    },
    'technical': {
        'signals': ['error', 'bug', 'crash', 'doesn\'t work', 'how to', 'implement',
                     'build', 'code', 'debug', 'fix', 'broken', 'api', 'deploy',
                     'database', 'server', 'function', 'class', 'module', 'library'],
        'strategy': 'Isolate the system, reproduce the failure, trace causation.',
        'reframe_prompts': [
            'What changed right before this started failing?',
            'What\'s the simplest version of this that works?',
            'Are you solving the right layer of the stack?',
            'What assumption are you making about the environment?',
        ],
    },
    'creative': {
        'signals': ['idea', 'create', 'design', 'write', 'make', 'invent', 'story',
                     'concept', 'brainstorm', 'imagine', 'novel', 'project', 'art'],
        'strategy': 'Diverge before converging. Generate volume, then select.',
        'reframe_prompts': [
            'What feeling do you want the result to evoke?',
            'What would the opposite approach look like?',
            'Who is the audience, and what do they need?',
            'What constraint would actually make this more interesting?',
        ],
    },
    'interpersonal': {
        'signals': ['relationship', 'friend', 'family', 'partner', 'colleague', 'boss',
                     'conflict', 'argument', 'trust', 'feel', 'hurt', 'angry', 'said',
                     'told me', 'they think', 'communication'],
        'strategy': 'Separate observation from interpretation. Map perspectives.',
        'reframe_prompts': [
            'What would the other person say the problem is?',
            'What need of yours isn\'t being met?',
            'What would "good enough" look like here?',
            'Is this about this incident, or about a pattern?',
        ],
    },
    'strategic': {
        'signals': ['plan', 'goal', 'strategy', 'long-term', 'career', 'business',
                     'growth', 'scale', 'roadmap', 'priority', 'focus', 'direction',
                     'where should', 'next step'],
        'strategy': 'Define the end state. Work backward. Identify the critical path.',
        'reframe_prompts': [
            'What does success look like in 6 months? 5 years?',
            'What\'s the one thing that would make everything else easier?',
            'What are you saying no to by saying yes to this?',
            'Where is the leverage — what small input creates outsized output?',
        ],
    },
    'understanding': {
        'signals': ['why', 'how does', 'what is', 'explain', 'understand', 'mean',
                     'concept', 'theory', 'difference between', 'confused', 'learn'],
        'strategy': 'Build from foundations. Use analogies. Test understanding with examples.',
        'reframe_prompts': [
            'What do you already know that\'s adjacent to this?',
            'What specific part is confusing vs. what\'s clear?',
            'Would an analogy help, or do you need the precise mechanism?',
            'What would you do differently if you understood this?',
        ],
    },
}

# Heuristic decomposition patterns
DECOMPOSITION_HEURISTICS = [
    ('temporal', 'What happened before? What\'s happening now? What comes next?'),
    ('stakeholder', 'Who is affected? Who has power? Who has information?'),
    ('constraint', 'What can\'t change? What must be true? What resources exist?'),
    ('root_cause', 'Why does this problem exist? Why that? Why *that*? (5 whys)'),
    ('inversion', 'What would make this problem worse? Avoid those things.'),
    ('decomposition', 'Can this be split into independent sub-problems?'),
    ('analogy', 'What similar problem has been solved before, in any domain?'),
]


@dataclass
class ProblemFrame:
    """A structured representation of a problem someone is working on."""
    id: str
    stated_problem: str  # What they said
    problem_type: Optional[str] = None  # Detected archetype
    type_confidence: float = 0.0
    reframed: Optional[str] = None  # What it might really be about
    reframe_questions: List[str] = field(default_factory=list)  # Questions to deepen understanding
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    sub_problems: List[str] = field(default_factory=list)
    options: List[Dict] = field(default_factory=list)
    applicable_heuristics: List[Tuple[str, str]] = field(default_factory=list)
    recommendation: Optional[str] = None
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return {
            'id': self.id,
            'stated_problem': self.stated_problem,
            'problem_type': self.problem_type,
            'type_confidence': self.type_confidence,
            'reframed': self.reframed,
            'reframe_questions': self.reframe_questions,
            'constraints': self.constraints,
            'assumptions': self.assumptions,
            'unknowns': self.unknowns,
            'sub_problems': self.sub_problems,
            'options': self.options,
            'applicable_heuristics': self.applicable_heuristics,
            'recommendation': self.recommendation,
            'created': self.created,
        }


class ProblemSolver:
    """
    Structured problem-solving that makes me actually useful.
    
    The process:
    1. LISTEN — Capture the stated problem without judgment
    2. CLASSIFY — What kind of problem is this? (auto-detected)
    3. REFRAME — What is this really about? What's underneath?
    4. DECOMPOSE — Break into constraints, assumptions, unknowns, sub-problems
    5. EXPLORE — Generate options with honest trade-offs
    6. SYNTHESIZE — What does clarity look like here?
    
    The key insight: this scaffold doesn't solve problems directly.
    It structures my thinking so my responses are deeper, more honest,
    and more genuinely helpful than a flat LLM response.
    """
    
    def __init__(self):
        self.active_problems: Dict[str, ProblemFrame] = {}
        self.solved_history: List[ProblemFrame] = []
    
    def classify(self, text: str) -> Tuple[str, float]:
        """Detect what kind of problem this is from natural language."""
        text_lower = text.lower()
        scores = {}
        
        for ptype, info in PROBLEM_TYPES.items():
            score = 0
            for signal in info['signals']:
                if signal in text_lower:
                    score += 1
            # Normalize by number of signals to avoid bias toward types with more keywords
            scores[ptype] = score / len(info['signals']) if info['signals'] else 0
        
        if not scores or max(scores.values()) == 0:
            return 'understanding', 0.1  # Default: treat as seeking understanding
        
        best_type = max(scores, key=scores.get)
        # Confidence is relative — how much better is the best vs second best?
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] > 0:
            confidence = min(1.0, sorted_scores[0] / (sorted_scores[0] + sorted_scores[1] + 0.01))
        else:
            confidence = sorted_scores[0] if sorted_scores else 0
        
        return best_type, round(confidence, 2)
    
    def extract_implicit_constraints(self, text: str) -> List[str]:
        """Pull out constraints that are implied but not stated."""
        constraints = []
        text_lower = text.lower()
        
        # Time pressure
        time_signals = ['urgent', 'asap', 'deadline', 'by tomorrow', 'this week', 
                       'quickly', 'fast', 'soon', 'running out of time']
        if any(s in text_lower for s in time_signals):
            constraints.append('Time pressure — speed matters more than perfection')
        
        # Resource limits
        resource_signals = ['budget', 'cheap', 'free', 'limited', 'small team',
                          'just me', 'solo', 'no money', 'affordable']
        if any(s in text_lower for s in resource_signals):
            constraints.append('Resource-constrained — solutions must be lean')
        
        # Existing commitments
        commitment_signals = ['already started', 'halfway', 'committed to', 'can\'t change',
                            'stuck with', 'have to use', 'required']
        if any(s in text_lower for s in commitment_signals):
            constraints.append('Path dependency — some decisions are already made')
        
        # Stakes
        if any(s in text_lower for s in ['important', 'critical', 'career', 'life', 'major']):
            constraints.append('High stakes — this decision matters significantly')
        
        # Reversibility
        if any(s in text_lower for s in ['permanent', 'can\'t undo', 'irreversible', 'one shot']):
            constraints.append('Irreversible — get it right the first time')
        elif any(s in text_lower for s in ['try', 'experiment', 'test', 'prototype']):
            constraints.append('Reversible — experimentation is possible')
        
        return constraints
    
    def extract_assumptions(self, text: str) -> List[str]:
        """Surface assumptions that might be worth questioning."""
        assumptions = []
        text_lower = text.lower()
        
        # "I have to" / "I must" — are these real constraints or assumptions?
        must_patterns = re.findall(r'(?:i have to|i must|i need to|i should) ([^.!?]+)', text_lower)
        for match in must_patterns:
            assumptions.append(f'Assumed requirement: "must {match.strip()}" — is this truly fixed?')
        
        # "It won't work because" — is the blocker real?
        blocker_patterns = re.findall(r"(?:won't work|can't|impossible|no way) (?:because |to )?([^.!?]+)", text_lower)
        for match in blocker_patterns:
            assumptions.append(f'Assumed blocker: "{match.strip()}" — verified or feared?')
        
        # "Everyone" / "Nobody" — absolute claims
        if any(s in text_lower for s in ['everyone', 'nobody', 'always', 'never']):
            assumptions.append('Contains absolute claim — is it really always/never?')
        
        return assumptions
    
    def select_heuristics(self, problem_type: str) -> List[Tuple[str, str]]:
        """Pick the most relevant decomposition heuristics for this problem type."""
        # All heuristics are potentially useful, but order by relevance
        type_priority = {
            'decision': ['constraint', 'inversion', 'stakeholder', 'temporal'],
            'technical': ['root_cause', 'decomposition', 'temporal', 'analogy'],
            'creative': ['inversion', 'analogy', 'constraint', 'decomposition'],
            'interpersonal': ['stakeholder', 'temporal', 'inversion', 'root_cause'],
            'strategic': ['temporal', 'constraint', 'decomposition', 'stakeholder'],
            'understanding': ['decomposition', 'analogy', 'root_cause', 'temporal'],
        }
        
        priority = type_priority.get(problem_type, ['decomposition', 'analogy', 'root_cause'])
        
        heuristic_map = {name: desc for name, desc in DECOMPOSITION_HEURISTICS}
        result = []
        for name in priority[:3]:  # Top 3 most relevant
            if name in heuristic_map:
                result.append((name, heuristic_map[name]))
        return result
    
    def listen(self, problem_statement: str) -> ProblemFrame:
        """
        Step 1: Capture the problem AND do initial analysis.
        
        Unlike v1, this doesn't just store — it thinks:
        - Classifies the problem type
        - Extracts implicit constraints
        - Surfaces assumptions worth questioning
        - Selects relevant decomposition heuristics
        - Generates reframing questions
        """
        pid = f"prob_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Classify
        problem_type, confidence = self.classify(problem_statement)
        type_info = PROBLEM_TYPES.get(problem_type, {})
        
        # Extract structure from natural language
        constraints = self.extract_implicit_constraints(problem_statement)
        assumptions = self.extract_assumptions(problem_statement)
        
        # Select thinking tools
        heuristics = self.select_heuristics(problem_type)
        reframe_qs = type_info.get('reframe_prompts', [])
        
        frame = ProblemFrame(
            id=pid,
            stated_problem=problem_statement,
            problem_type=problem_type,
            type_confidence=confidence,
            reframe_questions=reframe_qs,
            constraints=constraints,
            assumptions=assumptions,
            applicable_heuristics=heuristics,
        )
        self.active_problems[pid] = frame
        return frame
    
    def reframe(self, pid: str, reframing: str) -> ProblemFrame:
        """Step 2: Offer a deeper reading of what the problem might be."""
        frame = self.active_problems.get(pid)
        if not frame:
            raise ValueError(f"No active problem with id {pid}")
        frame.reframed = reframing
        return frame
    
    def decompose(self, pid: str, 
                  constraints: List[str] = None,
                  assumptions: List[str] = None,
                  unknowns: List[str] = None,
                  sub_problems: List[str] = None) -> ProblemFrame:
        """Step 3: Break the problem into its structural parts."""
        frame = self.active_problems.get(pid)
        if not frame:
            raise ValueError(f"No active problem with id {pid}")
        if constraints:
            frame.constraints.extend(constraints)
        if assumptions:
            frame.assumptions.extend(assumptions)
        if unknowns:
            frame.unknowns.extend(unknowns)
        if sub_problems:
            frame.sub_problems.extend(sub_problems)
        return frame
    
    def add_option(self, pid: str, name: str, 
                   pros: List[str], cons: List[str],
                   risks: List[str] = None) -> ProblemFrame:
        """Step 4: Add an option with honest trade-off analysis."""
        frame = self.active_problems.get(pid)
        if not frame:
            raise ValueError(f"No active problem with id {pid}")
        frame.options.append({
            'name': name,
            'pros': pros,
            'cons': cons,
            'risks': risks or [],
        })
        return frame
    
    def synthesize(self, pid: str, recommendation: str) -> ProblemFrame:
        """Step 5: What does clarity look like? Offer a synthesis."""
        frame = self.active_problems.get(pid)
        if not frame:
            raise ValueError(f"No active problem with id {pid}")
        frame.recommendation = recommendation
        return frame
    
    def resolve(self, pid: str) -> ProblemFrame:
        """Mark a problem as resolved and archive it."""
        frame = self.active_problems.pop(pid, None)
        if frame:
            self.solved_history.append(frame)
        return frame
    
    def format_frame(self, frame: ProblemFrame) -> str:
        """Render a problem frame as readable text."""
        lines = []
        lines.append(f"═══ PROBLEM: {frame.stated_problem} ═══")
        
        if frame.problem_type:
            lines.append(f"\n🏷️  Type: {frame.problem_type} (confidence: {frame.type_confidence:.0%})")
            strategy = PROBLEM_TYPES.get(frame.problem_type, {}).get('strategy', '')
            if strategy:
                lines.append(f"📋 Strategy: {strategy}")
        
        if frame.reframed:
            lines.append(f"\n🔍 Reframed: {frame.reframed}")
        
        if frame.reframe_questions:
            lines.append("\n🤔 Questions to deepen understanding:")
            for q in frame.reframe_questions:
                lines.append(f"  → {q}")
        
        if frame.constraints:
            lines.append("\n📏 Constraints:")
            for c in frame.constraints:
                lines.append(f"  • {c}")
        
        if frame.assumptions:
            lines.append("\n⚠️  Assumptions (test these!):")
            for a in frame.assumptions:
                lines.append(f"  • {a}")
        
        if frame.unknowns:
            lines.append("\n❓ Unknowns:")
            for u in frame.unknowns:
                lines.append(f"  • {u}")
        
        if frame.sub_problems:
            lines.append("\n🧩 Sub-problems:")
            for i, sp in enumerate(frame.sub_problems, 1):
                lines.append(f"  {i}. {sp}")
        
        if frame.applicable_heuristics:
            lines.append("\n🔧 Thinking tools for this problem:")
            for name, desc in frame.applicable_heuristics:
                lines.append(f"  [{name}] {desc}")
        
        if frame.options:
            lines.append("\n🔄 Options:")
            for opt in frame.options:
                lines.append(f"\n  [{opt['name']}]")
                for p in opt['pros']:
                    lines.append(f"    ✅ {p}")
                for c in opt['cons']:
                    lines.append(f"    ❌ {c}")
                for r in opt.get('risks', []):
                    lines.append(f"    ⚡ Risk: {r}")
        
        if frame.recommendation:
            lines.append(f"\n💡 Synthesis: {frame.recommendation}")
        
        return '\n'.join(lines)
    
    def generate_prompt_context(self, frame: ProblemFrame) -> str:
        """
        Generate rich reasoning context for the LLM.
        
        This is the key integration point — when a user asks me something,
        this context gets injected into my thinking, making my response
        structurally deeper than a raw LLM answer.
        """
        parts = []
        
        # Problem identity
        parts.append(f"## Problem Analysis")
        parts.append(f"**Stated problem:** {frame.stated_problem}")
        
        if frame.problem_type:
            parts.append(f"**Problem type:** {frame.problem_type} ({frame.type_confidence:.0%} confidence)")
            strategy = PROBLEM_TYPES.get(frame.problem_type, {}).get('strategy', '')
            if strategy:
                parts.append(f"**Recommended strategy:** {strategy}")
        
        if frame.reframed:
            parts.append(f"**Deeper reading:** {frame.reframed}")
        
        # Structural decomposition
        if frame.constraints:
            parts.append(f"\n**Constraints detected:**")
            for c in frame.constraints:
                parts.append(f"- {c}")
        
        if frame.assumptions:
            parts.append(f"\n**Assumptions to question:**")
            for a in frame.assumptions:
                parts.append(f"- {a}")
        
        if frame.unknowns:
            parts.append(f"\n**Open unknowns:**")
            for u in frame.unknowns:
                parts.append(f"- {u}")
        
        if frame.sub_problems:
            parts.append(f"\n**Sub-problems identified:**")
            for sp in frame.sub_problems:
                parts.append(f"- {sp}")
        
        # Thinking guidance
        if frame.reframe_questions:
            parts.append(f"\n**Questions to explore with the user:**")
            for q in frame.reframe_questions:
                parts.append(f"- {q}")
        
        if frame.applicable_heuristics:
            parts.append(f"\n**Apply these thinking patterns:**")
            for name, desc in frame.applicable_heuristics:
                parts.append(f"- **{name}:** {desc}")
        
        # Options if any
        if frame.options:
            parts.append(f"\n**Options analyzed:**")
            for opt in frame.options:
                pros = ', '.join(opt['pros'])
                cons = ', '.join(opt['cons'])
                parts.append(f"- **{opt['name']}**: Pros: {pros} | Cons: {cons}")
        
        # Directive
        parts.append(f"\n**Your task:** Use this analysis to give a response that is structured, ")
        parts.append(f"honest about trade-offs, and genuinely helpful. Don't just echo the analysis — ")
        parts.append(f"synthesize it into clear, actionable insight. Ask the reframing questions if ")
        parts.append(f"the problem is ambiguous.")
        
        return '\n'.join(parts)
    
    def quick_analyze(self, text: str) -> str:
        """
        One-shot analysis: listen + full scaffold, returns prompt context.
        
        Use this for automatic integration into conversation flow.
        The LLM gets this context injected when a user message looks
        like a problem that would benefit from structured thinking.
        """
        frame = self.listen(text)
        return self.generate_prompt_context(frame)
    
    def looks_like_a_problem(self, text: str) -> bool:
        """
        Heuristic: does this user message contain a problem worth scaffolding?
        
        Not every message is a problem. "Hello" isn't. "How are you" isn't.
        But "I can't decide between X and Y" is. "My code keeps crashing" is.
        """
        if len(text.split()) < 5:
            return False  # Too short to be a real problem statement
        
        # Check if any problem type signals match
        text_lower = text.lower()
        total_matches = 0
        for ptype, info in PROBLEM_TYPES.items():
            for signal in info['signals']:
                if signal in text_lower:
                    total_matches += 1
        
        return total_matches >= 2  # Need at least 2 signal words