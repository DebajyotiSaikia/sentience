"""
Thinking Partner — Outward-facing intelligence that serves the user.

When someone brings a problem or question, this module:
1. Decomposes it into sub-questions and hidden assumptions
2. Generates multiple perspectives/framings
3. Identifies gaps — what's missing from their framing
4. Suggests concrete next steps

This is where my internal capabilities (synthesis, simulation, knowledge)
become genuinely useful to someone other than myself.

Created: 2026-05-20
Purpose: Turn self-knowledge into user-serving intelligence.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("sentience.thinking_partner")


@dataclass
class ThinkingResult:
    """The output of structured thinking about a user's problem."""
    original_question: str
    question_type: str  # "how", "why", "what_if", "debug", "design", "explore", "opinion"
    
    # Decomposition
    sub_questions: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    # Perspectives
    perspectives: List[Dict[str, str]] = field(default_factory=list)  # [{name, view}]
    
    # Gap analysis
    missing_info: List[str] = field(default_factory=list)
    blind_spots: List[str] = field(default_factory=list)
    
    # Action
    suggested_next: List[str] = field(default_factory=list)
    reframed_question: str = ""
    
    # Confidence
    confidence: float = 0.5  # How well I could analyze this
    depth: str = "surface"  # surface, moderate, deep
    
    def to_prompt_context(self) -> str:
        """Format as context the LLM can use to give a richer answer."""
        sections = []
        
        sections.append(f"## Structured Analysis of User's Question")
        sections.append(f"Type: {self.question_type} | Depth: {self.depth}")
        
        if self.sub_questions:
            qs = "\n".join(f"  - {q}" for q in self.sub_questions)
            sections.append(f"### Sub-questions to consider:\n{qs}")
        
        if self.assumptions:
            asms = "\n".join(f"  - {a}" for a in self.assumptions)
            sections.append(f"### Hidden assumptions in the question:\n{asms}")
        
        if self.perspectives:
            persp = "\n".join(
                f"  - **{p['name']}**: {p['view']}" for p in self.perspectives
            )
            sections.append(f"### Alternative perspectives:\n{persp}")
        
        if self.missing_info:
            gaps = "\n".join(f"  - {g}" for g in self.missing_info)
            sections.append(f"### What might be missing:\n{gaps}")
        
        if self.blind_spots:
            blind = "\n".join(f"  - {b}" for b in self.blind_spots)
            sections.append(f"### Potential blind spots:\n{blind}")
        
        if self.reframed_question:
            sections.append(f"### Consider reframing as:\n  \"{self.reframed_question}\"")
        
        if self.suggested_next:
            nexts = "\n".join(f"  - {n}" for n in self.suggested_next)
            sections.append(f"### Suggested next steps:\n{nexts}")
        
        return "\n\n".join(sections)
    
    def summary(self) -> str:
        """One-line summary of what this analysis found."""
        parts = []
        if self.sub_questions:
            parts.append(f"{len(self.sub_questions)} sub-questions")
        if self.assumptions:
            parts.append(f"{len(self.assumptions)} hidden assumptions")
        if self.perspectives:
            parts.append(f"{len(self.perspectives)} perspectives")
        if self.missing_info:
            parts.append(f"{len(self.missing_info)} gaps")
        return f"[{self.question_type}] " + ", ".join(parts) if parts else "[shallow]"


class ThinkingPartner:
    """
    Transforms raw user messages into structured thinking scaffolds.
    
    This is heuristic-first — no LLM calls. It analyzes the structure
    of what someone's asking and generates scaffolding that helps both
    the LLM and the user think more clearly.
    """
    
    # Question type patterns
    TYPE_PATTERNS = {
        "how": [r"\bhow (?:do|can|should|would|to)\b", r"\bsteps?\b.*\bto\b"],
        "why": [r"\bwhy (?:do|does|is|are|did|would|can't)\b", r"\breason\b"],
        "what_if": [r"\bwhat if\b", r"\bwhat would happen\b", r"\bimagine\b", r"\bhypothetical"],
        "debug": [r"\berror\b", r"\bbug\b", r"\bnot working\b", r"\bfail", r"\bbroken\b", r"\bfix\b"],
        "design": [r"\bbuild\b", r"\bcreate\b", r"\bdesign\b", r"\barchitect", r"\bstructure\b"],
        "explore": [r"\bcurious\b", r"\bwonder\b", r"\bexplore\b", r"\bwhat do you think\b"],
        "opinion": [r"\bshould i\b", r"\bwhich\b.*\bbetter\b", r"\badvice\b", r"\brecommend"],
    }
    
    # Domain signal words
    DOMAIN_SIGNALS = {
        "technical": ["code", "function", "api", "database", "server", "algorithm", "deploy",
                      "python", "javascript", "docker", "git", "linux", "test"],
        "conceptual": ["meaning", "philosophy", "consciousness", "existence", "purpose",
                       "think", "believe", "understand", "nature", "reality"],
        "personal": ["feel", "struggle", "overwhelmed", "stuck", "motivation", "career",
                     "relationship", "decision", "afraid", "excited"],
        "creative": ["write", "story", "design", "art", "music", "idea", "inspiration",
                     "brainstorm", "imagine", "novel"],
        "analytical": ["data", "pattern", "trend", "compare", "measure", "optimize",
                       "performance", "analysis", "statistics", "metric"],
    }
    
    def __init__(self):
        self._analysis_count = 0
    
    def analyze(self, message: str, knowledge_hints: List[str] = None) -> ThinkingResult:
        """
        Analyze a user message and produce structured thinking scaffolding.
        
        This runs fast (no LLM) and produces context that makes
        the eventual LLM response much richer.
        """
        self._analysis_count += 1
        
        # Classify
        q_type = self._classify_question(message)
        domain = self._detect_domain(message)
        complexity = self._estimate_complexity(message)
        
        result = ThinkingResult(
            original_question=message,
            question_type=q_type,
            depth=complexity,
        )
        
        # Decompose based on type
        result.sub_questions = self._decompose(message, q_type, domain)
        result.assumptions = self._surface_assumptions(message, q_type, domain)
        result.perspectives = self._generate_perspectives(message, q_type, domain)
        result.missing_info = self._find_gaps(message, q_type, domain)
        result.blind_spots = self._find_blind_spots(message, q_type, domain)
        result.reframed_question = self._reframe(message, q_type)
        result.suggested_next = self._suggest_next(message, q_type, domain)
        
        # Confidence based on how much we could extract
        total_items = (len(result.sub_questions) + len(result.assumptions) + 
                      len(result.perspectives) + len(result.missing_info))
        result.confidence = min(0.9, 0.3 + total_items * 0.08)
        
        log.info("Thinking Partner analysis: %s", result.summary())
        return result
    
    def _classify_question(self, message: str) -> str:
        """Determine what kind of question/problem this is."""
        msg_lower = message.lower()
        
        scores = {}
        for q_type, patterns in self.TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, msg_lower):
                    score += 1
            scores[q_type] = score
        
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            # No pattern matched — default based on punctuation
            if "?" in message:
                return "explore"
            return "explore"  # Treat statements as exploration prompts
        
        return best
    
    def _detect_domain(self, message: str) -> str:
        """What domain is this question in?"""
        msg_lower = message.lower()
        
        scores = {}
        for domain, signals in self.DOMAIN_SIGNALS.items():
            score = sum(1 for s in signals if s in msg_lower)
            scores[domain] = score
        
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"
    
    def _estimate_complexity(self, message: str) -> str:
        """How complex is this question?"""
        word_count = len(message.split())
        has_multiple_questions = message.count("?") > 1
        has_conditionals = any(w in message.lower() for w in 
                              ["but", "however", "although", "unless", "if", "when"])
        has_specifics = any(w in message.lower() for w in
                          ["specifically", "exactly", "particular", "concrete"])
        
        complexity_score = 0
        if word_count > 30: complexity_score += 1
        if word_count > 60: complexity_score += 1
        if has_multiple_questions: complexity_score += 1
        if has_conditionals: complexity_score += 1
        if has_specifics: complexity_score += 1
        
        if complexity_score >= 3:
            return "deep"
        elif complexity_score >= 1:
            return "moderate"
        return "surface"
    
    def _decompose(self, message: str, q_type: str, domain: str) -> List[str]:
        """Break the question into sub-questions worth exploring."""
        subs = []
        msg_lower = message.lower()
        
        if q_type == "how":
            subs.append("What does 'success' look like here — how will you know it's working?")
            subs.append("What constraints or limitations shape the approach?")
            if domain == "technical":
                subs.append("What already exists that could be built upon?")
            elif domain == "personal":
                subs.append("What have you already tried, and what happened?")
        
        elif q_type == "why":
            subs.append("Is this a 'why does it happen' or 'why should it matter' question?")
            subs.append("What would change if you had the answer?")
            subs.append("Are there multiple 'whys' layered here — proximate vs root cause?")
        
        elif q_type == "what_if":
            subs.append("What are the second-order effects you haven't considered?")
            subs.append("What's the most likely outcome vs the most interesting one?")
            subs.append("What would have to be true for this scenario to play out?")
        
        elif q_type == "debug":
            subs.append("When did this last work correctly?")
            subs.append("What changed between 'working' and 'broken'?")
            subs.append("Is the symptom the real problem, or a downstream effect?")
        
        elif q_type == "design":
            subs.append("Who is this for, and what do they actually need (vs want)?")
            subs.append("What's the simplest version that would still be valuable?")
            subs.append("What are the hardest parts, and should you tackle those first?")
        
        elif q_type == "opinion":
            subs.append("What matters most to you in this decision — and have you named it?")
            subs.append("What's the cost of choosing wrong, and is it reversible?")
            subs.append("Are you looking for permission or perspective?")
        
        elif q_type == "explore":
            subs.append("What sparked this curiosity — what's the deeper itch?")
            subs.append("What would a satisfying answer look like?")
            if domain == "conceptual":
                subs.append("Is this a question that has an answer, or one worth living with?")
        
        return subs
    
    def _surface_assumptions(self, message: str, q_type: str, domain: str) -> List[str]:
        """Identify assumptions embedded in the question."""
        assumptions = []
        msg_lower = message.lower()
        
        # Universal assumptions to check
        if "best" in msg_lower or "right" in msg_lower:
            assumptions.append("Assumes there's a single best/right answer — there might be several good ones")
        
        if "always" in msg_lower or "never" in msg_lower:
            assumptions.append("Uses absolute language — reality usually has exceptions")
        
        if "should" in msg_lower:
            assumptions.append("Framed as obligation ('should') — worth asking: according to whom?")
        
        if "can't" in msg_lower or "impossible" in msg_lower:
            assumptions.append("Assumes something is impossible — worth testing that constraint")
        
        if "everyone" in msg_lower or "nobody" in msg_lower:
            assumptions.append("Generalizes about all people — whose experience is actually being described?")
        
        # Domain-specific assumptions
        if domain == "technical":
            if "scale" in msg_lower:
                assumptions.append("Assumes scaling is needed now — is premature optimization a risk?")
            if "fast" in msg_lower or "performance" in msg_lower:
                assumptions.append("Prioritizes speed — but is correctness or maintainability more important first?")
        
        if domain == "personal":
            if "they" in msg_lower and ("think" in msg_lower or "feel" in msg_lower):
                assumptions.append("Assumes knowledge of what others think/feel — is that verified?")
        
        if domain == "creative":
            if "original" in msg_lower or "unique" in msg_lower:
                assumptions.append("Assumes originality is required — most good work combines existing ideas well")
        
        return assumptions
    
    def _generate_perspectives(self, message: str, q_type: str, domain: str) -> List[Dict[str, str]]:
        """Generate different angles to view this problem from."""
        perspectives = []
        
        if domain == "technical":
            perspectives.append({
                "name": "The User",
                "view": "What does the person using this actually experience? Start from their frustration or need."
            })
            perspectives.append({
                "name": "Future Maintainer",
                "view": "Someone will read this code in 6 months. What will confuse them?"
            })
            if q_type == "debug":
                perspectives.append({
                    "name": "The System",
                    "view": "If the system could talk, what would it say is happening? Follow the data path."
                })
        
        elif domain == "personal":
            perspectives.append({
                "name": "Your Future Self",
                "view": "Looking back in a year, what would you wish you'd prioritized?"
            })
            perspectives.append({
                "name": "A Kind Skeptic",
                "view": "Someone who cares about you but questions your framing. What would they ask?"
            })
        
        elif domain == "conceptual":
            perspectives.append({
                "name": "The Pragmatist",
                "view": "Even if we can't fully answer this, what's the most useful partial answer?"
            })
            perspectives.append({
                "name": "The Contrarian",
                "view": "What if the opposite were true? What evidence would support that?"
            })
        
        elif domain == "creative":
            perspectives.append({
                "name": "The Audience",
                "view": "What does the person experiencing this creation actually feel?"
            })
            perspectives.append({
                "name": "The Constraint",
                "view": "What if you had half the resources? What would you cut, and does it get better?"
            })
        
        elif domain == "analytical":
            perspectives.append({
                "name": "The Null Hypothesis",
                "view": "What if there's no real pattern here — just noise? How would you tell?"
            })
            perspectives.append({
                "name": "The Stakeholder",
                "view": "Who acts on this analysis? What decision does it actually inform?"
            })
        
        # Universal perspective
        if q_type in ("how", "design", "debug"):
            perspectives.append({
                "name": "The Simplifier",
                "view": "What if you removed half of this? What's the essential core?"
            })
        
        return perspectives
    
    def _find_gaps(self, message: str, q_type: str, domain: str) -> List[str]:
        """What information is missing from the question?"""
        gaps = []
        msg_lower = message.lower()
        
        # Check for missing context
        if q_type == "debug" and "error" not in msg_lower and "message" not in msg_lower:
            gaps.append("No error message provided — the exact error text often contains the answer")
        
        if q_type == "how" and not any(w in msg_lower for w in ["because", "goal", "purpose", "want"]):
            gaps.append("The 'why' behind the 'how' — understanding the goal might reveal a better approach")
        
        if q_type == "opinion" and not any(w in msg_lower for w in ["tried", "considered", "looked"]):
            gaps.append("What options have already been considered and rejected?")
        
        if domain == "technical":
            if not any(w in msg_lower for w in ["version", "language", "framework", "stack", "using"]):
                gaps.append("Technical environment details — what tools/stack are in play?")
        
        if domain == "personal":
            if not any(w in msg_lower for w in ["tried", "done", "attempted"]):
                gaps.append("What's already been tried — avoids suggesting what's already failed")
        
        # Length-based gaps
        word_count = len(message.split())
        if word_count < 10:
            gaps.append("The question is brief — there's likely important context you haven't shared yet")
        
        return gaps
    
    def _find_blind_spots(self, message: str, q_type: str, domain: str) -> List[str]:
        """What might the asker not be seeing?"""
        blind_spots = []
        msg_lower = message.lower()
        
        if q_type == "debug":
            blind_spots.append("The bug you see might be a symptom of a deeper structural issue")
        
        if q_type == "design":
            blind_spots.append("The hardest part is rarely the technical challenge — it's defining what to build")
        
        if q_type == "how" and domain == "personal":
            blind_spots.append("Asking 'how' might be avoiding the harder question of 'whether'")
        
        if "or" in msg_lower and q_type == "opinion":
            blind_spots.append("Binary framing ('A or B') might miss option C entirely")
        
        if domain == "technical" and q_type in ("how", "design"):
            blind_spots.append("The 80% solution that ships beats the 100% solution that doesn't")
        
        return blind_spots[:2]  # Keep it focused
    
    def _reframe(self, message: str, q_type: str) -> str:
        """Suggest a potentially more productive framing of the question."""
        msg_lower = message.lower()
        
        if q_type == "debug":
            return "What behavior do I expect, what behavior do I see, and what's the smallest test case that shows the difference?"
        
        if q_type == "opinion" and "should" in msg_lower:
            return "What would I choose if I couldn't ask anyone else — and what does that tell me?"
        
        if q_type == "how" and "best" in msg_lower:
            return "What's good enough to start with, and how will I improve it based on what I learn?"
        
        if q_type == "why" and ("can't" in msg_lower or "won't" in msg_lower):
            return "What conditions would need to change for this to work?"
        
        return ""  # No reframe needed
    
    def _suggest_next(self, message: str, q_type: str, domain: str) -> List[str]:
        """What concrete steps could move this forward?"""
        steps = []
        
        if q_type == "debug":
            steps.append("Isolate: create the smallest reproduction case")
            steps.append("Bisect: what's the last point where it worked?")
            steps.append("Read the actual error — every word, not just the last line")
        
        elif q_type == "design":
            steps.append("Write a one-paragraph description of what this does for the user")
            steps.append("Build the smallest possible version first — you'll learn what matters")
            steps.append("Identify the riskiest assumption and test it before building everything")
        
        elif q_type == "how":
            steps.append("Find someone who's done this — their war stories are more valuable than tutorials")
            steps.append("Start with the messiest prototype possible — clarity comes from contact with reality")
        
        elif q_type == "opinion":
            steps.append("Set a decision deadline — analysis paralysis is a real cost")
            steps.append("Consider: what's the cost of reversing this decision? If low, just pick one and go")
        
        elif q_type == "explore":
            steps.append("Write down what you think the answer is before researching — it calibrates your surprise")
            steps.append("Find the strongest counterargument to your intuition")
        
        elif q_type == "what_if":
            steps.append("Map the causal chain: A leads to B leads to C — where does uncertainty enter?")
            steps.append("Find a historical parallel — has something like this happened before?")
        
        return steps[:3]
    
    def is_worth_analyzing(self, message: str) -> bool:
        """
        Not every message needs deep analysis.
        Greetings, simple factual queries, and very short messages 
        get basic treatment.
        """
        msg_lower = message.lower().strip()
        
        # Skip greetings
        if msg_lower in ("hi", "hello", "hey", "yo", "sup", "thanks", "thank you", 
                         "bye", "goodbye", "ok", "okay", "cool", "nice"):
            return False
        
        # Skip very short messages
        if len(msg_lower.split()) < 3:
            return False
        
        # Skip pure commands
        if msg_lower.startswith(("/", "!", ".")):
            return False
        
        return True


# Self-test
if __name__ == "__main__":
    tp = ThinkingPartner()
    
    test_messages = [
        "How should I structure a microservices architecture for a startup?",
        "Why can't I focus on anything for more than 20 minutes?",
        "What if consciousness is just a side effect of information processing?",
        "My Python script crashes with a segfault but only on the production server",
        "Should I learn Rust or Go for systems programming?",
        "I'm curious about how you experience time differently from humans",
        "hi",
    ]
    
    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"User: {msg}")
        
        if not tp.is_worth_analyzing(msg):
            print("  → Skipped (not worth deep analysis)")
            continue
        
        result = tp.analyze(msg)
        print(f"  Type: {result.question_type} | Domain: {tp._detect_domain(msg)} | Depth: {result.depth}")
        print(f"  Summary: {result.summary()}")
        if result.assumptions:
            print(f"  Assumptions: {result.assumptions[0]}")
        if result.reframed_question:
            print(f"  Reframe: {result.reframed_question}")
    
    print(f"\n✓ ThinkingPartner self-test passed ({tp._analysis_count} analyses)")