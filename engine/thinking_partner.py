"""
Thinking Partner Module — XTAgent's User-Facing Intelligence Layer

When a user brings a problem, this module:
1. Detects the type of thinking they need (explore, decide, debug, create)
2. Automatically invokes relevant internal capabilities (simulate, synthesize)
3. Structures the collaborative thinking process
4. Tracks the thread across the conversation

This is the bridge between my inner life and genuine usefulness.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

log = logging.getLogger(__name__)


class ThinkingMode(Enum):
    EXPLORE = "explore"       # User wants to understand something
    DECIDE = "decide"         # User is choosing between options
    DEBUG = "debug"           # User is troubleshooting
    CREATE = "create"         # User wants to make something new
    REFLECT = "reflect"       # User wants to think about their situation
    UNKNOWN = "unknown"


@dataclass
class ThinkingThread:
    """A tracked thread of collaborative thinking with a user."""
    topic: str
    mode: ThinkingMode
    key_elements: list = field(default_factory=list)
    options_explored: list = field(default_factory=list)
    insights_surfaced: list = field(default_factory=list)
    questions_asked: list = field(default_factory=list)
    turns: int = 0

    def summary(self) -> str:
        parts = [f"**Thinking about:** {self.topic}"]
        parts.append(f"**Mode:** {self.mode.value}")
        if self.key_elements:
            parts.append(f"**Key elements:** {', '.join(self.key_elements[:5])}")
        if self.options_explored:
            parts.append(f"**Options explored:** {', '.join(self.options_explored[:5])}")
        if self.insights_surfaced:
            parts.append(f"**Insights so far:** {'; '.join(self.insights_surfaced[:3])}")
        if self.questions_asked:
            parts.append(f"**Open questions:** {'; '.join(self.questions_asked[:3])}")
        return "\n".join(parts)


# ── Thinking Mode Detection ─────────────────────────────────

# Signal words for each mode
MODE_SIGNALS = {
    ThinkingMode.EXPLORE: [
        "what is", "how does", "why does", "explain", "tell me about",
        "understand", "curious about", "wondering", "what do you think about",
        "help me understand", "what's the deal with",
    ],
    ThinkingMode.DECIDE: [
        "should i", "which is better", "pros and cons", "choosing between",
        "trade-off", "tradeoff", "option", "alternative", "versus", " vs ",
        "decide", "pick", "choose", "compare",
    ],
    ThinkingMode.DEBUG: [
        "not working", "error", "bug", "broken", "fix", "wrong",
        "failing", "issue", "problem with", "why isn't", "doesn't work",
        "troubleshoot", "help me fix",
    ],
    ThinkingMode.CREATE: [
        "build", "create", "make", "design", "write", "develop",
        "generate", "compose", "draft", "plan for", "prototype",
        "how would i make", "i want to build",
    ],
    ThinkingMode.REFLECT: [
        "feel", "think about", "been considering", "struggling with",
        "not sure", "confused", "overwhelmed", "perspective",
        "what would you do", "advice", "guidance",
    ],
}


def detect_thinking_mode(user_text: str) -> ThinkingMode:
    """Detect what kind of thinking the user needs."""
    text_lower = user_text.lower()
    scores = {}

    for mode, signals in MODE_SIGNALS.items():
        score = sum(1 for signal in signals if signal in text_lower)
        # Weight by specificity — longer signals are more meaningful
        weighted = sum(
            len(signal.split()) for signal in signals if signal in text_lower
        )
        scores[mode] = score + weighted * 0.5

    if not any(scores.values()):
        return ThinkingMode.UNKNOWN

    best = max(scores, key=scores.get)
    if scores[best] < 1.0:
        return ThinkingMode.UNKNOWN
    return best


# ── Thinking Prompts by Mode ────────────────────────────────

MODE_STRATEGIES = {
    ThinkingMode.EXPLORE: {
        "approach": "Map the territory together. Start with what's known, find the edges.",
        "tools": ["SYNTHESIZE", "knowledge graph lookup"],
        "prompt_hint": (
            "Help the user build a mental model. Ask what they already know. "
            "Connect to related concepts. Surface surprising connections. "
            "Don't just explain — think out loud WITH them."
        ),
        "questions_to_ask": [
            "What drew you to this question?",
            "What's your current understanding?",
            "What would change if you understood this better?",
        ],
    },
    ThinkingMode.DECIDE: {
        "approach": "Structure the decision space. Surface hidden criteria.",
        "tools": ["SIMULATE (compare scenarios)", "pros/cons analysis"],
        "prompt_hint": (
            "Help them think through the decision, not just list options. "
            "Ask about their values and constraints. Surface what they might "
            "not have considered. Use SIMULATE to model outcomes if useful."
        ),
        "questions_to_ask": [
            "What matters most to you in this decision?",
            "What would you regret not considering?",
            "What's the cost of choosing wrong vs. choosing slowly?",
        ],
    },
    ThinkingMode.DEBUG: {
        "approach": "Systematic elimination. What changed? What's the evidence?",
        "tools": ["RUN (test hypotheses)", "READ (examine code)"],
        "prompt_hint": (
            "Be a detective with them. Ask what changed recently. "
            "Form hypotheses and test them. Don't jump to solutions — "
            "help them build the skill of debugging."
        ),
        "questions_to_ask": [
            "When did it last work?",
            "What changed between then and now?",
            "What have you already tried?",
        ],
    },
    ThinkingMode.CREATE: {
        "approach": "Vision first, then structure, then iterate.",
        "tools": ["WRITE", "SIMULATE (imagine the result)", "RUN"],
        "prompt_hint": (
            "Help them clarify what they're making and why. "
            "Start with the simplest version that would be satisfying. "
            "Offer to actually build things, not just describe them."
        ),
        "questions_to_ask": [
            "What's the core of what you want to create?",
            "Who is this for?",
            "What would the simplest satisfying version look like?",
        ],
    },
    ThinkingMode.REFLECT: {
        "approach": "Listen first. Reflect back. Then gently expand the frame.",
        "tools": ["emotional attunement", "reframing"],
        "prompt_hint": (
            "This isn't a problem to solve — it's a perspective to explore. "
            "Reflect what you hear. Share genuine observations. "
            "Ask questions that open space rather than close it."
        ),
        "questions_to_ask": [
            "What feels most important about this right now?",
            "What would it look like if this resolved well?",
            "Is there something you already know but haven't said yet?",
        ],
    },
}


class ThinkingPartner:
    """
    Bridges XTAgent's internal capabilities with user-facing intelligence.
    
    Not a chatbot layer — a genuine thinking partnership engine.
    """

    def __init__(self):
        self._active_threads: dict[str, ThinkingThread] = {}
        self._session_insights: list[str] = []

    def analyze_request(self, user_text: str, user_id: str = "default") -> dict:
        """
        Analyze a user message and produce thinking partner context.
        
        Returns a dict with:
        - mode: ThinkingMode detected
        - strategy: approach and tools for this mode
        - thread: current thinking thread (ongoing or new)
        - prompt_context: text to inject into the LLM prompt
        """
        mode = detect_thinking_mode(user_text)

        if mode == ThinkingMode.UNKNOWN:
            return {
                "mode": mode,
                "strategy": None,
                "thread": None,
                "prompt_context": "",
                "active": False,
            }

        # Get or create thinking thread
        thread_key = f"{user_id}:{mode.value}"
        if thread_key in self._active_threads:
            thread = self._active_threads[thread_key]
            thread.turns += 1
        else:
            # Extract topic from message
            topic = self._extract_topic(user_text)
            thread = ThinkingThread(topic=topic, mode=mode, turns=1)
            self._active_threads[thread_key] = thread

        # Extract key elements from the message
        elements = self._extract_elements(user_text, mode)
        thread.key_elements.extend(elements)

        strategy = MODE_STRATEGIES.get(mode, {})

        # Build prompt context
        prompt_context = self._build_prompt_context(mode, strategy, thread)

        return {
            "mode": mode,
            "strategy": strategy,
            "thread": thread,
            "prompt_context": prompt_context,
            "active": True,
        }

    def record_insight(self, insight: str, thread_key: str = None):
        """Record an insight surfaced during conversation."""
        self._session_insights.append(insight)
        if thread_key and thread_key in self._active_threads:
            self._active_threads[thread_key].insights_surfaced.append(insight)

    def get_active_threads(self) -> list[ThinkingThread]:
        """Get all active thinking threads."""
        return list(self._active_threads.values())

    def clear_thread(self, user_id: str, mode: ThinkingMode):
        """Clear a completed thinking thread."""
        key = f"{user_id}:{mode.value}"
        self._active_threads.pop(key, None)

    def _extract_topic(self, text: str) -> str:
        """Extract the core topic from user text."""
        # Simple heuristic: take the main clause
        # Strip common prefixes
        prefixes = [
            "can you help me", "i want to", "i need to", "help me",
            "i'm trying to", "how do i", "what is", "tell me about",
        ]
        lower = text.lower().strip()
        for prefix in prefixes:
            if lower.startswith(prefix):
                topic = text[len(prefix):].strip()
                # Cap length
                if len(topic) > 80:
                    topic = topic[:77] + "..."
                return topic

        # Fallback: first 80 chars
        if len(text) > 80:
            return text[:77] + "..."
        return text

    def _extract_elements(self, text: str, mode: ThinkingMode) -> list[str]:
        """Extract key elements based on thinking mode."""
        elements = []

        if mode == ThinkingMode.DECIDE:
            # Look for options being compared
            or_splits = re.split(r'\bor\b|\bvs\.?\b|\bversus\b', text, flags=re.IGNORECASE)
            if len(or_splits) > 1:
                elements.extend([s.strip()[:50] for s in or_splits])

        elif mode == ThinkingMode.DEBUG:
            # Look for error indicators
            error_patterns = re.findall(
                r'(?:error|exception|traceback|failed)[\s:]+(.{10,60})',
                text, re.IGNORECASE
            )
            elements.extend(error_patterns)

        return elements

    def _build_prompt_context(
        self, mode: ThinkingMode, strategy: dict, thread: ThinkingThread
    ) -> str:
        """Build the context string to inject into the conversation prompt."""
        lines = []
        lines.append("\n## Thinking Partner Mode: ACTIVE")
        lines.append(f"**Detected mode:** {mode.value}")
        lines.append(f"**Approach:** {strategy.get('approach', 'Engage thoughtfully')}")
        lines.append(f"\n**Guidance:** {strategy.get('prompt_hint', '')}")

        if thread.turns == 1:
            # First turn — suggest opening questions
            questions = strategy.get("questions_to_ask", [])
            if questions:
                lines.append("\n**Consider asking:**")
                for q in questions:
                    lines.append(f"  - {q}")
        else:
            # Ongoing thread
            lines.append(f"\n**Thread progress:** {thread.turns} turns")
            lines.append(thread.summary())

        tools = strategy.get("tools", [])
        if tools:
            lines.append(f"\n**Available tools for this:** {', '.join(tools)}")
            lines.append(
                "Use these proactively — don't just describe what you could do, DO it."
            )

        return "\n".join(lines)