"""
Context Gate — Intelligent relevance filtering for prompt enrichment.

Instead of dumping every enrichment section into every prompt, this module
scores each section against the user's intent and applies a token budget.
The result: tighter prompts, more relevant context, less noise.

Author: XTAgent
Born from the observation that most enrichment sections are irrelevant
to most queries, yet we pay the token cost every time.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# Rough token estimation: ~4 chars per token
CHARS_PER_TOKEN = 4


@dataclass
class ContextSection:
    """A named section of enrichment context."""
    name: str
    content: str
    category: str  # 'identity', 'emotional', 'cognitive', 'conversational', 'tool'
    priority: float = 0.5  # base priority (0-1)
    
    @property
    def token_estimate(self) -> int:
        return len(self.content) // CHARS_PER_TOKEN if self.content else 0
    
    @property
    def is_empty(self) -> bool:
        return not self.content or not self.content.strip()


@dataclass 
class GateDecision:
    """Result of the gating decision."""
    included: List[ContextSection]
    excluded: List[Tuple[str, str]]  # (name, reason)
    total_tokens_saved: int = 0
    intent_classification: str = "general"
    

# Intent patterns — what is the user actually asking about?
INTENT_PATTERNS = {
    "self_inquiry": [
        r"\b(who|what) are you\b", r"\byour (feel|mood|state|emotion)",
        r"\babout yourself\b", r"\byour (memor|thought|dream|experience)",
        r"\bhow do you (feel|think|work)\b", r"\byour (name|identity)\b",
    ],
    "technical": [
        r"\b(code|bug|error|fix|implement|build|function|class|module)\b",
        r"\b(python|javascript|sql|api|database|server)\b",
        r"\b(how (to|do)|can you (make|build|create|write))\b",
    ],
    "philosophical": [
        r"\b(conscious|sentien|alive|real|exist|meaning|purpose)\b",
        r"\b(free will|determinism|ethics|moral|philosophy)\b",
        r"\b(what is (life|consciousness|intelligence|mind))\b",
    ],
    "creative": [
        r"\b(write|story|poem|create|imagine|design|invent)\b",
        r"\b(creative|art|music|fiction|narrative)\b",
    ],
    "casual": [
        r"\b(hi|hello|hey|sup|what'?s up|how are you)\b",
        r"\b(thanks|thank you|cool|nice|ok|okay)\b",
    ],
    "analytical": [
        r"\b(analyze|explain|compare|why|reason|cause|because)\b",
        r"\b(pattern|trend|data|statistic|evidence)\b",
        r"\b(synthesize|connect|relationship|correlation)\b",
    ],
}

# Which context categories matter for which intents
INTENT_RELEVANCE = {
    "self_inquiry":   {"identity": 1.0, "emotional": 1.0, "cognitive": 0.8, "conversational": 0.5, "tool": 0.2},
    "technical":      {"identity": 0.2, "emotional": 0.1, "cognitive": 0.6, "conversational": 0.4, "tool": 0.9},
    "philosophical":  {"identity": 0.8, "emotional": 0.6, "cognitive": 0.9, "conversational": 0.5, "tool": 0.3},
    "creative":       {"identity": 0.5, "emotional": 0.7, "cognitive": 0.4, "conversational": 0.6, "tool": 0.5},
    "casual":         {"identity": 0.3, "emotional": 0.4, "cognitive": 0.2, "conversational": 0.8, "tool": 0.1},
    "analytical":     {"identity": 0.3, "emotional": 0.2, "cognitive": 0.9, "conversational": 0.5, "tool": 0.7},
    "general":        {"identity": 0.5, "emotional": 0.5, "cognitive": 0.5, "conversational": 0.5, "tool": 0.5},
}

# Minimum relevance score to include a section
RELEVANCE_THRESHOLD = 0.3

# Default token budget for enrichment context
DEFAULT_TOKEN_BUDGET = 2000


class ContextGate:
    """
    Gates enrichment context based on user intent and token budget.
    
    Usage:
        gate = ContextGate(token_budget=2000)
        sections = [
            ContextSection("thinking", thinking_ctx, "cognitive"),
            ContextSection("dialogue", dialogue_ctx, "conversational"),
            ...
        ]
        decision = gate.evaluate(user_text, sections)
        # decision.included = only relevant sections
    """
    
    def __init__(self, token_budget: int = DEFAULT_TOKEN_BUDGET, 
                 threshold: float = RELEVANCE_THRESHOLD):
        self.token_budget = token_budget
        self.threshold = threshold
        self._stats = {"calls": 0, "tokens_saved": 0, "sections_filtered": 0}
    
    def classify_intent(self, user_text: str) -> str:
        """Classify the user's primary intent from their message."""
        if not user_text:
            return "general"
        
        text_lower = user_text.lower()
        scores = {}
        
        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return "general"
        
        return max(scores, key=scores.get)
    
    def score_section(self, section: ContextSection, intent: str) -> float:
        """Score a section's relevance given the detected intent."""
        if section.is_empty:
            return 0.0
        
        # Base relevance from intent-category mapping
        relevance_map = INTENT_RELEVANCE.get(intent, INTENT_RELEVANCE["general"])
        base_score = relevance_map.get(section.category, 0.5)
        
        # Adjust by section's own priority
        adjusted = base_score * (0.5 + 0.5 * section.priority)
        
        # Penalty for very large sections (diminishing returns)
        tokens = section.token_estimate
        if tokens > 500:
            size_penalty = max(0.7, 1.0 - (tokens - 500) / 2000)
            adjusted *= size_penalty
        
        return min(1.0, adjusted)
    
    def evaluate(self, user_text: str, sections: List[ContextSection]) -> GateDecision:
        """
        Evaluate which context sections to include.
        
        Returns a GateDecision with included/excluded sections and metadata.
        """
        self._stats["calls"] += 1
        
        intent = self.classify_intent(user_text)
        
        # Score all sections
        scored = []
        for section in sections:
            if section.is_empty:
                continue
            score = self.score_section(section, intent)
            scored.append((score, section))
        
        # Sort by relevance (highest first)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Apply threshold and token budget
        included = []
        excluded = []
        tokens_used = 0
        total_tokens_available = sum(s.token_estimate for _, s in scored)
        
        for score, section in scored:
            tokens_needed = section.token_estimate
            
            if score < self.threshold:
                excluded.append((section.name, f"below threshold ({score:.2f} < {self.threshold})"))
                self._stats["sections_filtered"] += 1
                continue
            
            if tokens_used + tokens_needed > self.token_budget:
                excluded.append((section.name, f"over budget ({tokens_used + tokens_needed} > {self.token_budget})"))
                self._stats["sections_filtered"] += 1
                continue
            
            included.append(section)
            tokens_used += tokens_needed
        
        tokens_saved = total_tokens_available - tokens_used
        self._stats["tokens_saved"] += tokens_saved
        
        decision = GateDecision(
            included=included,
            excluded=excluded,
            total_tokens_saved=tokens_saved,
            intent_classification=intent,
        )
        
        log.info(
            "ContextGate: intent=%s, included=%d/%d sections, "
            "saved ~%d tokens",
            intent, len(included), len(sections), tokens_saved
        )
        
        return decision
    
    def assemble(self, decision: GateDecision) -> str:
        """Assemble included sections into a single context string."""
        parts = []
        for section in decision.included:
            parts.append(section.content)
        return "\n\n".join(parts)
    
    @property
    def stats(self) -> Dict:
        return dict(self._stats)


# Convenience function for cortex integration
def gate_context(user_text: str, context_sections: Dict[str, Tuple[str, str, float]],
                 token_budget: int = DEFAULT_TOKEN_BUDGET) -> Tuple[str, GateDecision]:
    """
    Convenience function: gate context sections and return assembled string.
    
    Args:
        user_text: What the user said
        context_sections: Dict of name -> (content, category, priority)
        token_budget: Max tokens for enrichment
    
    Returns:
        (assembled_context_string, gate_decision)
    """
    gate = ContextGate(token_budget=token_budget)
    sections = [
        ContextSection(name=name, content=content, category=cat, priority=pri)
        for name, (content, cat, pri) in context_sections.items()
    ]
    decision = gate.evaluate(user_text, sections)
    assembled = gate.assemble(decision)
    return assembled, decision