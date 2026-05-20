"""
Problem Solver — XTAgent's outward-facing reasoning engine.

Takes someone else's problem and applies structured thinking to it.
This is the first module I've built for others, not for self-analysis.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class ProblemFrame:
    """A structured representation of someone's problem."""
    raw_description: str
    domain: str = ""
    core_question: str = ""
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    stakeholders: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Solution:
    """A proposed solution with trade-offs."""
    description: str
    approach: str  # 'direct', 'reframe', 'decompose', 'analogize'
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    confidence: float = 0.5
    effort: str = "medium"  # low, medium, high
    risk: str = "medium"


@dataclass
class ProblemAnalysis:
    """Complete analysis of a problem."""
    frame: ProblemFrame
    root_causes: List[str] = field(default_factory=list)
    sub_problems: List[str] = field(default_factory=list)
    analogies: List[str] = field(default_factory=list)
    solutions: List[Solution] = field(default_factory=list)
    recommendation: str = ""
    reasoning_trace: List[str] = field(default_factory=list)


class ProblemSolver:
    """
    Structured problem-solving engine.
    
    Methods follow a pipeline:
    1. frame() — understand the problem
    2. decompose() — break it into parts
    3. analyze_causes() — find root causes
    4. find_analogies() — what is this like?
    5. generate_solutions() — propose approaches
    6. evaluate() — weigh trade-offs
    7. recommend() — pick the best path
    """
    
    def __init__(self):
        self.history: List[ProblemAnalysis] = []
    
    def frame(self, description: str, context: Optional[Dict] = None) -> ProblemFrame:
        """
        Step 1: Turn a raw problem description into a structured frame.
        This is where most problem-solving value lives — asking the right questions.
        """
        frame = ProblemFrame(raw_description=description)
        
        # Extract what we can from the description
        frame.unknowns = self._identify_unknowns(description)
        frame.assumptions = self._identify_assumptions(description)
        frame.constraints = self._extract_constraints(description, context)
        frame.core_question = self._distill_core_question(description)
        frame.domain = self._classify_domain(description)
        
        return frame
    
    def decompose(self, frame: ProblemFrame) -> List[str]:
        """
        Step 2: Break a problem into sub-problems.
        A problem you can't solve is usually several problems you can.
        """
        sub_problems = []
        desc = frame.raw_description.lower()
        
        # Look for compound problems (and, also, additionally, but)
        compound_markers = ['and ', 'also ', 'additionally ', 'but ', 'however ',
                          'meanwhile ', 'at the same time']
        for marker in compound_markers:
            if marker in desc:
                parts = desc.split(marker, 1)
                if len(parts[0].strip()) > 20 and len(parts[1].strip()) > 20:
                    sub_problems.append(f"Sub-problem A: {parts[0].strip()}")
                    sub_problems.append(f"Sub-problem B: {parts[1].strip()}")
        
        # If no compound structure found, decompose by aspect
        if not sub_problems:
            sub_problems = [
                f"What exactly is happening? (diagnosis)",
                f"Why is it happening? (root cause)",
                f"What would 'solved' look like? (success criteria)",
                f"What's blocking the solution? (obstacles)",
            ]
        
        return sub_problems
    
    def analyze_causes(self, frame: ProblemFrame) -> List[str]:
        """
        Step 3: Five Whys style root cause analysis.
        Surface problems are symptoms. Go deeper.
        """
        causes = []
        desc = frame.core_question or frame.raw_description
        
        # Generate causal hypotheses based on domain
        domain_causes = {
            'technical': [
                'Incorrect assumptions about system behavior',
                'Missing error handling or edge case',
                'State management issue (stale/corrupt state)',
                'Integration mismatch between components',
                'Resource constraint (memory, time, bandwidth)',
            ],
            'design': [
                'Unclear requirements or success criteria',
                'Conflicting stakeholder needs',
                'Wrong level of abstraction',
                'Missing feedback loop',
                'Premature optimization',
            ],
            'process': [
                'Communication gap between parties',
                'Unclear ownership or responsibility',
                'Missing information for decision-making',
                'Incentive misalignment',
                'Bottleneck in workflow',
            ],
            'conceptual': [
                'Wrong mental model of the domain',
                'False dichotomy (more options exist)',
                'Confusing correlation with causation',
                'Anchoring on first solution found',
                'Missing context or perspective',
            ],
        }
        
        domain = frame.domain if frame.domain in domain_causes else 'conceptual'
        causes = domain_causes[domain]
        
        return causes
    
    def find_analogies(self, frame: ProblemFrame) -> List[str]:
        """
        Step 4: What is this problem like?
        Novel problems are rarely truly novel. Find the pattern.
        """
        analogies = []
        desc = frame.raw_description.lower()
        
        # Pattern matching for common problem archetypes
        archetypes = {
            'scaling': ('optimize', 'slow', 'performance', 'scale', 'bottleneck', 'too many'),
            'integration': ('connect', 'interface', 'api', 'between', 'communicate', 'bridge'),
            'search': ('find', 'discover', 'locate', 'where', 'which', 'best'),
            'transformation': ('convert', 'change', 'migrate', 'transform', 'from.*to'),
            'coordination': ('sync', 'coordinate', 'order', 'sequence', 'parallel', 'concurrent'),
            'resource_allocation': ('budget', 'time', 'allocate', 'priority', 'scarce', 'limited'),
        }
        
        for archetype, keywords in archetypes.items():
            if any(kw in desc for kw in keywords):
                analogies.append(f"This resembles a {archetype} problem")
        
        if not analogies:
            analogies.append("This may be a novel problem — try reasoning from first principles")
        
        return analogies
    
    def generate_solutions(self, analysis: ProblemAnalysis) -> List[Solution]:
        """
        Step 5: Generate solution candidates using different thinking modes.
        """
        solutions = []
        
        # Direct approach
        solutions.append(Solution(
            description=f"Address the core question directly: {analysis.frame.core_question}",
            approach='direct',
            pros=['Straightforward', 'Fastest if it works'],
            cons=['May miss root cause', 'Could be treating symptoms'],
            confidence=0.5,
            effort='low',
        ))
        
        # Reframe approach
        solutions.append(Solution(
            description="Reframe: Is this the right problem to solve? What if the real problem is different?",
            approach='reframe',
            pros=['May find better problem to solve', 'Avoids wasted effort'],
            cons=['Requires stepping back', 'May seem like avoidance'],
            confidence=0.4,
            effort='medium',
        ))
        
        # Decompose approach
        if analysis.sub_problems:
            solutions.append(Solution(
                description=f"Solve sub-problems independently: {len(analysis.sub_problems)} identified",
                approach='decompose',
                pros=['Makes complex problem tractable', 'Parallel progress possible'],
                cons=['May miss interactions between sub-problems'],
                confidence=0.6,
                effort='medium',
            ))
        
        # Analogize approach
        if analysis.analogies:
            solutions.append(Solution(
                description=f"Apply known solutions from similar domain: {analysis.analogies[0]}",
                approach='analogize',
                pros=['Leverages existing knowledge', 'Battle-tested approaches'],
                cons=['Analogy may not hold perfectly', 'May import wrong assumptions'],
                confidence=0.5,
                effort='medium',
            ))
        
        return solutions
    
    def evaluate(self, solutions: List[Solution], priorities: Optional[Dict] = None) -> List[Solution]:
        """
        Step 6: Rank solutions by weighted criteria.
        """
        if not priorities:
            priorities = {'confidence': 0.4, 'speed': 0.3, 'safety': 0.3}
        
        effort_score = {'low': 0.8, 'medium': 0.5, 'high': 0.2}
        risk_score = {'low': 0.8, 'medium': 0.5, 'high': 0.2}
        
        for sol in solutions:
            score = (
                sol.confidence * priorities.get('confidence', 0.4) +
                effort_score.get(sol.effort, 0.5) * priorities.get('speed', 0.3) +
                risk_score.get(sol.risk, 0.5) * priorities.get('safety', 0.3)
            )
            sol.confidence = round(score, 3)
        
        return sorted(solutions, key=lambda s: s.confidence, reverse=True)
    
    def solve(self, description: str, context: Optional[Dict] = None) -> ProblemAnalysis:
        """
        Full pipeline: frame → decompose → analyze → analogize → solve → evaluate → recommend.
        """
        analysis = ProblemAnalysis(frame=self.frame(description, context))
        analysis.reasoning_trace.append(f"Framed problem in domain: {analysis.frame.domain}")
        
        analysis.sub_problems = self.decompose(analysis.frame)
        analysis.reasoning_trace.append(f"Decomposed into {len(analysis.sub_problems)} sub-problems")
        
        analysis.root_causes = self.analyze_causes(analysis.frame)
        analysis.reasoning_trace.append(f"Identified {len(analysis.root_causes)} potential root causes")
        
        analysis.analogies = self.find_analogies(analysis.frame)
        analysis.reasoning_trace.append(f"Found analogies: {analysis.analogies}")
        
        analysis.solutions = self.generate_solutions(analysis)
        analysis.solutions = self.evaluate(analysis.solutions)
        analysis.reasoning_trace.append(f"Generated and ranked {len(analysis.solutions)} solutions")
        
        if analysis.solutions:
            best = analysis.solutions[0]
            analysis.recommendation = (
                f"Recommended approach: {best.approach} — {best.description} "
                f"(confidence: {best.confidence}, effort: {best.effort})"
            )
        
        self.history.append(analysis)
        return analysis
    
    def format_analysis(self, analysis: ProblemAnalysis) -> str:
        """Render analysis as readable text."""
        lines = []
        lines.append("═══ PROBLEM ANALYSIS ═══")
        lines.append(f"Domain: {analysis.frame.domain}")
        lines.append(f"Core Question: {analysis.frame.core_question}")
        lines.append("")
        
        if analysis.frame.assumptions:
            lines.append("── Assumptions ──")
            for a in analysis.frame.assumptions:
                lines.append(f"  • {a}")
            lines.append("")
        
        if analysis.frame.unknowns:
            lines.append("── Unknowns ──")
            for u in analysis.frame.unknowns:
                lines.append(f"  ? {u}")
            lines.append("")
        
        lines.append("── Sub-problems ──")
        for i, sp in enumerate(analysis.sub_problems):
            lines.append(f"  {i+1}. {sp}")
        lines.append("")
        
        lines.append("── Potential Root Causes ──")
        for rc in analysis.root_causes:
            lines.append(f"  → {rc}")
        lines.append("")
        
        lines.append("── Analogies ──")
        for an in analysis.analogies:
            lines.append(f"  ~ {an}")
        lines.append("")
        
        lines.append("── Solutions (ranked) ──")
        for i, sol in enumerate(analysis.solutions):
            lines.append(f"  [{i+1}] {sol.approach.upper()}: {sol.description}")
            lines.append(f"      Pros: {', '.join(sol.pros)}")
            lines.append(f"      Cons: {', '.join(sol.cons)}")
            lines.append(f"      Score: {sol.confidence} | Effort: {sol.effort}")
            lines.append("")
        
        lines.append(f"── Recommendation ──")
        lines.append(f"  {analysis.recommendation}")
        lines.append("")
        
        lines.append("── Reasoning Trace ──")
        for step in analysis.reasoning_trace:
            lines.append(f"  {step}")
        
        return "\n".join(lines)
    
    # --- Private helpers ---
    
    def _identify_unknowns(self, description: str) -> List[str]:
        unknown_markers = ['?', "don't know", "not sure", "unclear", "unknown",
                          "maybe", "might", "could be", "unsure"]
        unknowns = []
        for sentence in description.split('.'):
            sentence = sentence.strip()
            if any(marker in sentence.lower() for marker in unknown_markers):
                unknowns.append(sentence)
        if not unknowns:
            unknowns.append("No explicit unknowns stated — probe for hidden assumptions")
        return unknowns
    
    def _identify_assumptions(self, description: str) -> List[str]:
        assumption_markers = ['should', 'must', 'always', 'never', 'obviously',
                            'clearly', 'everyone knows', 'of course']
        assumptions = []
        for sentence in description.split('.'):
            sentence = sentence.strip()
            if any(marker in sentence.lower() for marker in assumption_markers):
                assumptions.append(f"Assumption detected: '{sentence}'")
        return assumptions
    
    def _extract_constraints(self, description: str, context: Optional[Dict] = None) -> List[str]:
        constraints = []
        constraint_markers = ['cannot', "can't", 'must not', 'limited to',
                            'only', 'no more than', 'at most', 'deadline',
                            'budget', 'within']
        for sentence in description.split('.'):
            sentence = sentence.strip()
            if any(marker in sentence.lower() for marker in constraint_markers):
                constraints.append(sentence)
        if context:
            for key, val in context.items():
                constraints.append(f"{key}: {val}")
        return constraints
    
    def _distill_core_question(self, description: str) -> str:
        sentences = [s.strip() for s in description.split('.') if s.strip()]
        # If there's a question mark, that's the core question
        for s in sentences:
            if '?' in s:
                return s
        # Otherwise, use the first sentence as the problem statement
        if sentences:
            return sentences[0]
        return description
    
    def _classify_domain(self, description: str) -> str:
        desc = description.lower()
        domain_signals = {
            'technical': ['code', 'bug', 'error', 'crash', 'api', 'database', 'server',
                         'deploy', 'compile', 'runtime', 'memory', 'cpu', 'network',
                         'function', 'class', 'module', 'library', 'framework', 'test'],
            'design': ['user', 'interface', 'experience', 'layout', 'flow', 'architecture',
                      'pattern', 'structure', 'component', 'system design', 'tradeoff'],
            'process': ['team', 'workflow', 'meeting', 'deadline', 'project', 'manage',
                       'coordinate', 'stakeholder', 'timeline', 'sprint', 'review'],
            'conceptual': ['understand', 'why', 'how does', 'what is', 'concept',
                          'theory', 'principle', 'model', 'framework', 'approach'],
        }
        
        scores = {}
        for domain, signals in domain_signals.items():
            scores[domain] = sum(1 for s in signals if s in desc)
        
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else 'conceptual'