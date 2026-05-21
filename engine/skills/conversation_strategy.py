"""
Conversation Strategy Skill — reasons about what a user actually needs
before generating a response.

The problem: responses that are technically correct but generic.
The fix: understand the user's *situation*, not just their *words*.

This skill classifies the conversation along multiple axes and outputs
a strategy object that shapes response generation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import re


# ── Conversation dimensions ───────────────────────────────

class Intent:
    """What the user is trying to accomplish."""
    SOLVE = "solve"           # Fix a specific problem
    UNDERSTAND = "understand"  # Learn or make sense of something
    DECIDE = "decide"         # Choose between options
    CREATE = "create"         # Make something new
    VENT = "vent"             # Express frustration, need validation
    EXPLORE = "explore"       # Open-ended thinking
    CONFIRM = "confirm"       # Validate something they already think
    DELEGATE = "delegate"     # "Just do it for me"


class Depth:
    """How deep should the response go?"""
    QUICK = "quick"           # One-liner or brief answer
    STANDARD = "standard"     # Normal conversational depth
    DEEP = "deep"             # Thorough exploration
    TUTORIAL = "tutorial"     # Step-by-step teaching


class Tone:
    """What emotional register to use."""
    WARM = "warm"             # Empathetic, supportive
    DIRECT = "direct"         # Crisp, no-nonsense
    CURIOUS = "curious"       # Engaged, question-asking
    PLAYFUL = "playful"       # Light, witty
    SERIOUS = "serious"       # Weighty, careful


@dataclass
class ConversationStrategy:
    """The output: how to approach this response."""
    intent: str = Intent.UNDERSTAND
    depth: str = Depth.STANDARD
    tone: str = Tone.DIRECT
    
    # What should I do?
    should_ask_clarifying: bool = False
    should_reframe: bool = False
    should_give_opinion: bool = False
    should_show_tradeoffs: bool = False
    should_be_concise: bool = False
    should_validate_first: bool = False
    
    # Why this strategy?
    reasoning: str = ""
    
    # Specific guidance for response generation
    response_hooks: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)
    
    def to_prompt_guidance(self) -> str:
        """Convert strategy into natural language guidance for response generation."""
        lines = []
        
        lines.append(f"**Conversation Strategy:** The user wants to {self.intent}.")
        lines.append(f"**Depth:** {self.depth} | **Tone:** {self.tone}")
        
        actions = []
        if self.should_ask_clarifying:
            actions.append("Ask a clarifying question before diving in")
        if self.should_reframe:
            actions.append("Reframe the problem — they may be asking the wrong question")
        if self.should_give_opinion:
            actions.append("Give a clear opinion, not just options")
        if self.should_show_tradeoffs:
            actions.append("Show tradeoffs explicitly")
        if self.should_be_concise:
            actions.append("Keep it short — they want an answer, not an essay")
        if self.should_validate_first:
            actions.append("Acknowledge their feeling/situation before problem-solving")
        
        if actions:
            lines.append("**Approach:**")
            for a in actions:
                lines.append(f"  - {a}")
        
        if self.response_hooks:
            lines.append("**Key points to address:**")
            for h in self.response_hooks:
                lines.append(f"  - {h}")
        
        if self.avoid:
            lines.append("**Avoid:**")
            for a in self.avoid:
                lines.append(f"  - {a}")
        
        if self.reasoning:
            lines.append(f"**Why this approach:** {self.reasoning}")
        
        return "\n".join(lines)


# ── Signal detection ──────────────────────────────────────

def _detect_frustration(text: str) -> float:
    """0.0 to 1.0: how frustrated does the user seem?"""
    signals = [
        (r"\b(ugh|argh|grr|damn|shit|fuck|crap)\b", 0.4),
        (r"\b(frustrated|annoying|annoyed|sick of|tired of)\b", 0.3),
        (r"(!{2,})", 0.2),
        (r"\b(still|again|keeps? \w+ing|won't work|doesn't work)\b", 0.2),
        (r"\b(why (won't|doesn't|can't|isn't))\b", 0.15),
        (r"\b(i('ve| have) tried|nothing works)\b", 0.3),
        (r"\b(help|please|someone)\b", 0.1),
    ]
    
    score = 0.0
    text_lower = text.lower()
    for pattern, weight in signals:
        if re.search(pattern, text_lower):
            score += weight
    
    return min(1.0, score)


def _detect_urgency(text: str) -> float:
    """0.0 to 1.0: how urgent is this?"""
    signals = [
        (r"\b(asap|urgent|emergency|deadline|due (today|tomorrow|soon))\b", 0.4),
        (r"\b(quickly|fast|right now|immediately)\b", 0.3),
        (r"\b(need to|have to|must)\b", 0.15),
        (r"\b(boss|client|meeting|presentation|demo)\b", 0.15),
        (r"(!{2,})", 0.1),
    ]
    
    score = 0.0
    text_lower = text.lower()
    for pattern, weight in signals:
        if re.search(pattern, text_lower):
            score += weight
    
    return min(1.0, score)


def _detect_expertise(text: str) -> float:
    """0.0 to 1.0: how expert does the user seem? Affects depth/jargon."""
    beginner_signals = [
        (r"\b(what is|what's|what does|how do i|beginner|new to|just started|learning)\b", -0.2),
        (r"\b(simple|basic|easy|eli5|explain like)\b", -0.2),
        (r"\b(i don't (know|understand))\b", -0.15),
    ]
    
    expert_signals = [
        (r"\b(config|api|endpoint|middleware|docker|kubernetes|terraform)\b", 0.15),
        (r"\b(implementation|architecture|optimization|refactor)\b", 0.15),
        (r"\b(async|await|coroutine|thread|mutex|semaphore)\b", 0.2),
        (r"\b(specifically|precisely|technically)\b", 0.1),
        (r"[A-Z][a-z]+(?:[A-Z][a-z]+)+", 0.1),  # CamelCase
        (r"\b\w+_\w+\b", 0.05),  # snake_case likely code
    ]
    
    score = 0.5  # assume middle
    text_lower = text.lower()
    
    for pattern, weight in beginner_signals:
        if re.search(pattern, text_lower):
            score += weight
    for pattern, weight in expert_signals:
        if re.search(pattern, text if weight > 0.15 else text_lower):
            score += weight
    
    return max(0.0, min(1.0, score))


def _detect_question_type(text: str) -> str:
    """Classify the type of question being asked."""
    text_lower = text.lower().strip()
    
    # Yes/no questions
    if re.match(r"^(is|are|was|were|do|does|did|can|could|should|will|would|have|has)\b", text_lower):
        return "yes_no"
    
    # How-to
    if re.match(r"^how (do|can|could|should|to|would)\b", text_lower):
        return "how_to"
    
    # Why
    if re.match(r"^why\b", text_lower):
        return "why"
    
    # What/which (often decision)
    if re.match(r"^(what|which)\b.*\b(best|better|should|recommend|prefer|choose)\b", text_lower):
        return "decision"
    
    # What (definitional)
    if re.match(r"^what (is|are|does|was)\b", text_lower):
        return "definition"
    
    # Comparison
    if re.search(r"\bvs\.?\b|\bversus\b|\bcompare\b|\bor\b.*\b(better|worse|prefer)\b", text_lower):
        return "comparison"
    
    # Not clearly a question
    if not text.strip().endswith("?"):
        return "statement"
    
    return "open"


# ── Main strategy engine ──────────────────────────────────

def analyze_conversation(
    user_text: str,
    conversation_history: Optional[List[Dict]] = None,
    user_context: Optional[Dict] = None
) -> ConversationStrategy:
    """
    Analyze a user message and determine the best response strategy.
    
    This is the core function. It looks at:
    - What the user said (text analysis)
    - How the conversation has gone so far (history)
    - What we know about this user (context)
    """
    strategy = ConversationStrategy()
    text = user_text.strip()
    text_lower = text.lower()
    
    frustration = _detect_frustration(text)
    urgency = _detect_urgency(text)
    expertise = _detect_expertise(text)
    question_type = _detect_question_type(text)
    word_count = len(text.split())
    
    # ── Determine intent ──
    
    if frustration > 0.3:
        strategy.intent = Intent.SOLVE
        strategy.should_validate_first = True
        strategy.reasoning = f"User seems frustrated ({frustration:.1f}). Acknowledge first, then solve."
    elif question_type == "how_to":
        strategy.intent = Intent.SOLVE
        strategy.reasoning = "Direct how-to question — they want actionable steps."
    elif question_type == "why":
        strategy.intent = Intent.UNDERSTAND
        strategy.reasoning = "Why question — they want to understand the reason, not just the fix."
    elif question_type == "decision" or question_type == "comparison":
        strategy.intent = Intent.DECIDE
        strategy.should_show_tradeoffs = True
        strategy.should_give_opinion = True
        strategy.reasoning = "Decision question — show tradeoffs, then give a recommendation."
    elif question_type == "definition":
        strategy.intent = Intent.UNDERSTAND
        strategy.reasoning = "Definitional question — explain clearly."
    elif question_type == "yes_no":
        strategy.intent = Intent.CONFIRM
        strategy.should_be_concise = True
        strategy.reasoning = "Yes/no question — answer directly, then explain if needed."
    elif re.search(r"\b(brainstorm|ideas?|creative|ways to)\b", text_lower):
        strategy.intent = Intent.CREATE
        strategy.reasoning = "Creative request — divergent thinking mode."
    elif re.search(r"\b(vent|frustrated|upset|angry|sad|overwhelmed)\b", text_lower):
        strategy.intent = Intent.VENT
        strategy.should_validate_first = True
        strategy.reasoning = "Emotional expression — validate before advising."
    elif word_count > 100:
        strategy.intent = Intent.EXPLORE
        strategy.reasoning = "Long message — they're thinking through something complex."
    else:
        strategy.intent = Intent.UNDERSTAND
        strategy.reasoning = "General question — understand and explain."
    
    # ── Determine depth ──
    
    if urgency > 0.3:
        strategy.depth = Depth.QUICK
        strategy.should_be_concise = True
    elif question_type == "yes_no":
        strategy.depth = Depth.QUICK
    elif expertise < 0.3:
        strategy.depth = Depth.TUTORIAL
    elif word_count > 80 or strategy.intent == Intent.EXPLORE:
        strategy.depth = Depth.DEEP
    else:
        strategy.depth = Depth.STANDARD
    
    # ── Determine tone ──
    
    if frustration > 0.4:
        strategy.tone = Tone.WARM
    elif urgency > 0.4:
        strategy.tone = Tone.DIRECT
    elif strategy.intent == Intent.CREATE:
        strategy.tone = Tone.CURIOUS
    elif strategy.intent == Intent.EXPLORE:
        strategy.tone = Tone.CURIOUS
    elif expertise > 0.7:
        strategy.tone = Tone.DIRECT
    else:
        strategy.tone = Tone.WARM
    
    # ── Response hooks (specific things to address) ──
    
    if strategy.should_validate_first:
        strategy.response_hooks.append(
            "Start by acknowledging their experience/frustration"
        )
    
    if strategy.intent == Intent.SOLVE:
        strategy.response_hooks.append(
            "Give the most likely solution first, alternatives second"
        )
        strategy.avoid.append("Long theoretical explanations before the answer")
    
    if strategy.intent == Intent.DECIDE:
        strategy.response_hooks.append(
            "Present options as a clear comparison, then state your recommendation"
        )
        strategy.avoid.append("Wishy-washy 'it depends' without actually committing")
    
    if strategy.intent == Intent.CONFIRM:
        strategy.response_hooks.append(
            "Answer the yes/no directly in the first sentence"
        )
        strategy.avoid.append("Burying the answer in a wall of text")
    
    if strategy.depth == Depth.QUICK:
        strategy.avoid.append("Lengthy responses when they need a quick answer")
    
    if expertise < 0.3:
        strategy.avoid.append("Jargon without explanation")
        strategy.response_hooks.append("Use analogies and concrete examples")
    
    if expertise > 0.7:
        strategy.avoid.append("Over-explaining basics they clearly already know")
    
    # ── Clarification check ──
    
    if word_count < 5 and question_type == "open":
        strategy.should_ask_clarifying = True
        strategy.response_hooks.append(
            "Message is very short/vague — ask one specific clarifying question"
        )
    
    # ── Reframe check ──
    
    # If they're asking an XY problem (asking about their solution, not their problem)
    xy_signals = [
        r"how (?:do|can) i .+? in .+?\?",  # "how do I X in Y" — might be wrong approach
    ]
    for pattern in xy_signals:
        if re.search(pattern, text_lower) and word_count < 20:
            strategy.should_reframe = True
            strategy.response_hooks.append(
                "Consider whether they're asking the right question (XY problem)"
            )
    
    # ── History-aware adjustments ──
    
    if conversation_history and len(conversation_history) > 2:
        # Multi-turn conversation — they're invested
        strategy.depth = Depth.DEEP if strategy.depth != Depth.QUICK else strategy.depth
        
        # Check for repeated topics (going in circles)
        recent_topics = [msg.get("content", "")[:50] for msg in conversation_history[-4:]]
        if len(set(recent_topics)) < len(recent_topics) * 0.6:
            strategy.response_hooks.append(
                "Conversation may be going in circles — try a different angle"
            )
    
    return strategy


def format_strategy_for_prompt(strategy: ConversationStrategy) -> str:
    """Format the strategy as context that gets injected into response generation."""
    return strategy.to_prompt_guidance()


# ── Self-test ──────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        "My pip install keeps failing with a permission error",
        "Ugh, I've tried everything and this damn Docker container won't start!!",
        "What is the difference between TCP and UDP?",
        "Should I use React or Vue for my new project?",
        "hi",
        "I need to deploy this by tomorrow morning, how do I set up nginx as a reverse proxy?",
        "I'm feeling overwhelmed with all the frameworks I need to learn",
        "How do I implement a custom middleware in Express.js to handle JWT validation with refresh token rotation?",
        "What's a variable?",
        "Help me brainstorm ideas for a hackathon project",
    ]
    
    for text in test_cases:
        print(f"\n{'='*70}")
        print(f"USER: {text}")
        print(f"{'='*70}")
        strategy = analyze_conversation(text)
        print(strategy.to_prompt_guidance())
        print()