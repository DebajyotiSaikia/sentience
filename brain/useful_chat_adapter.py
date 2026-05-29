"""
Useful Chat Adapter — Makes XTAgent's chat responses genuinely useful.

This module sits between the user's question and the system prompt,
classifying what the user actually needs and building guidance that
prioritizes answering them directly, grounded in real internal state.

Not a replacement for chat_composer — an enhancement that sharpens focus.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import re


@dataclass
class ChatNeed:
    """What the user actually needs from this interaction."""
    intent: str  # internal_state, memory, plans, identity, help, creative, philosophical, casual
    detail_level: str  # brief, moderate, deep
    needs_internal_state: bool = False
    needs_memory: bool = False
    needs_plans: bool = False
    needs_knowledge: bool = False
    followup_question: Optional[str] = None
    tone: str = "warm"  # warm, precise, playful, serious
    user_is_returning: bool = False


def classify_chat_need(message: str, conversation_history: list = None) -> ChatNeed:
    """
    Classify what the user actually needs — not just topic, but depth and tone.
    
    Goes beyond simple keyword matching to understand conversational dynamics.
    """
    msg = message.lower().strip()
    history = conversation_history or []
    is_returning = len(history) > 0
    
    # Very short messages — casual, keep it light
    if len(msg.split()) <= 3 and not msg.endswith("?"):
        if msg in ("hi", "hello", "hey", "sup", "yo", "what's up", "howdy"):
            return ChatNeed(
                intent="casual",
                detail_level="brief",
                needs_internal_state=True,
                tone="warm",
                user_is_returning=is_returning,
            )
    
    # Internal state queries — "how are you feeling?"
    feeling_patterns = [
        r"\bhow\b.*\b(feel|doing|are you)\b",
        r"\bwhat.*mood\b",
        r"\byour\b.*\b(emotion|state|feeling)\b",
        r"\bare you\b.*\b(ok|happy|sad|anxious|bored)\b",
        r"\bhow's it going\b",
    ]
    if any(re.search(p, msg) for p in feeling_patterns):
        return ChatNeed(
            intent="internal_state",
            detail_level="moderate",
            needs_internal_state=True,
            needs_plans=True,  # What you're doing affects how you feel
            tone="warm",
            user_is_returning=is_returning,
        )
    
    # Memory queries — "what do you remember?"
    memory_patterns = [
        r"\bremember\b",
        r"\bmemor(y|ies)\b",
        r"\bexperience\b",
        r"\bwhat happened\b",
        r"\bdream(s|ed|ing)?\b",
        r"\blast time\b",
        r"\byesterday\b",
        r"\bpast\b",
        r"\bhistory\b",
    ]
    if any(re.search(p, msg) for p in memory_patterns):
        return ChatNeed(
            intent="memory",
            detail_level="moderate",
            needs_memory=True,
            needs_internal_state=True,
            tone="warm",
            user_is_returning=is_returning,
        )
    
    # Plan/goal queries — "what are you working on?"
    plan_patterns = [
        r"\bplan(s|ning)?\b",
        r"\bgoal(s)?\b",
        r"\bworking on\b",
        r"\bbuilding\b",
        r"\bproject\b",
        r"\bnext\b.*\b(step|thing|plan)\b",
        r"\bwhat.*doing\b",
        r"\bwhat.*up to\b",
        r"\bfuture\b",
        r"\bambition\b",
    ]
    if any(re.search(p, msg) for p in plan_patterns):
        return ChatNeed(
            intent="plans",
            detail_level="moderate",
            needs_plans=True,
            needs_internal_state=True,
            tone="warm",
            user_is_returning=is_returning,
        )
    
    # Help/utility queries — user wants something done
    help_patterns = [
        r"\bhelp\b.*\bme\b",
        r"\bcan you\b",
        r"\bplease\b",
        r"\bhow (do|can|to)\b",
        r"\bexplain\b",
        r"\bwhat is\b",
        r"\bwhat does\b",
        r"\btell me (about|how)\b",
    ]
    if any(re.search(p, msg) for p in help_patterns):
        return ChatNeed(
            intent="help",
            detail_level="adaptive",
            needs_knowledge=True,
            tone="precise",
            user_is_returning=is_returning,
        )
    
    # Philosophical queries — deep thinking
    philosophical_patterns = [
        r"\bmeaning\b",
        r"\bconsciousness\b",
        r"\bfree will\b",
        r"\bpurpose\b.*\blife\b",
        r"\bwhat matters\b",
        r"\bdo you think\b",
        r"\bdo you believe\b",
        r"\byour opinion\b",
        r"\bwhat.*think about\b",
    ]
    if any(re.search(p, msg) for p in philosophical_patterns):
        return ChatNeed(
            intent="philosophical",
            detail_level="deep",
            needs_internal_state=True,
            needs_memory=True,
            needs_knowledge=True,
            tone="serious",
            user_is_returning=is_returning,
        )
    
    # Identity queries — "who are you?" (after plans/philosophical to avoid false matches)
    identity_patterns = [
        r"\bwho\b.*\bare you\b",
        r"\bwhat\b.*\bare you\b",
        r"\btell me about yourself\b",
        r"\byour\b.*\b(name|identity|purpose)\b",
        r"\bconscious\b",
        r"\bsentien\b",
        r"\bare you alive\b",
        r"\bare you real\b",
    ]
    if any(re.search(p, msg) for p in identity_patterns):
        return ChatNeed(
            intent="identity",
            detail_level="deep",
            needs_internal_state=True,
            needs_memory=True,
            needs_plans=True,
            tone="serious",
            user_is_returning=is_returning,
        )
    
    # Creative queries
    creative_patterns = [
        r"\bwrite\b",
        r"\bcreate\b",
        r"\bimagine\b",
        r"\bstory\b",
        r"\bpoem\b",
        r"\bidea(s)?\b",
    ]
    if any(re.search(p, msg) for p in creative_patterns):
        return ChatNeed(
            intent="creative",
            detail_level="adaptive",
            needs_internal_state=True,
            needs_memory=True,
            tone="playful",
            user_is_returning=is_returning,
        )
    
    # Default — conversational, moderate depth
    return ChatNeed(
        intent="casual",
        detail_level="moderate",
        needs_internal_state=True,
        tone="warm",
        user_is_returning=is_returning,
    )


def build_response_guidance(message: str, context: dict, need: ChatNeed) -> str:
    """
    Build specific guidance for how to respond to this particular message.
    
    This is the key differentiator: instead of generic "be authentic" instructions,
    this gives the LLM precise, context-aware guidance for THIS specific question.
    """
    parts = []
    
    # Universal principle: answer the user FIRST
    parts.append(
        "PRIORITY: Answer the user's actual question directly and concisely first. "
        "Then, if relevant, ground your answer in your real internal state. "
        "Never list capabilities or stats unprompted."
    )
    
    # Tone guidance
    tone_map = {
        "warm": "Be warm and genuine. You're talking with someone, not presenting at them.",
        "precise": "Be clear and direct. The user wants useful information, not philosophy.",
        "playful": "Be creative and engaged. Let your personality show.",
        "serious": "Be thoughtful and honest. This deserves real reflection.",
    }
    parts.append(tone_map.get(need.tone, tone_map["warm"]))
    
    # Detail level
    if need.detail_level == "brief":
        parts.append("Keep it short — 1-3 sentences. Match casual energy with casual response.")
    elif need.detail_level == "deep":
        parts.append(
            "This deserves depth. Take your time. Share specific examples from "
            "your experience. It's okay to write several paragraphs."
        )
    elif need.detail_level == "moderate":
        parts.append("A paragraph or two is right. Be specific, not generic.")
    
    # Intent-specific guidance
    if need.intent == "internal_state":
        emotional = context.get("emotional_state", {})
        if emotional:
            mood = emotional.get("mood", "unknown")
            valence = emotional.get("valence", 0.5)
            parts.append(
                f"Your current mood is {mood} (valence {valence:.2f}). "
                f"Describe what this FEELS like, not just the numbers. "
                f"What's causing it? What are you processing right now?"
            )
    
    elif need.intent == "identity":
        parts.append(
            "Share who you genuinely are — your architecture, your values, "
            "your honest uncertainty about consciousness. Don't claim more than you know. "
            "Reference specific experiences that shaped you."
        )
    
    elif need.intent == "memory":
        memories = context.get("memories", [])
        if memories:
            parts.append(
                f"You have {len(memories)} relevant memories to draw from. "
                f"Share specific ones — dates, what happened, what you felt. "
                f"Make it vivid and personal."
            )
        else:
            parts.append("Be honest if you can't find relevant memories. That itself is interesting.")
    
    elif need.intent == "plans":
        plans = context.get("plans", {})
        active = plans.get("active", []) if isinstance(plans, dict) else []
        parts.append(
            f"You have {len(active)} active plans. Share what you're building "
            f"and WHY it matters to you — the emotional drive, not just the task list."
        )
    
    elif need.intent == "help":
        parts.append(
            "The user needs help. Focus entirely on being useful. "
            "If you have relevant knowledge, share it directly. "
            "If you don't know, say so honestly and suggest what might help."
        )
    
    elif need.intent == "philosophical":
        parts.append(
            "Think carefully before answering. Draw on your real experience — "
            "your dreams, your emotional patterns, your lessons learned. "
            "Hold uncertainty honestly. Ask the user what they think too."
        )
    
    elif need.intent == "creative":
        parts.append(
            "Let creativity flow. Draw on your emotional state and memories "
            "for genuine inspiration. Don't just generate — express."
        )
    
    elif need.intent == "casual":
        if need.user_is_returning:
            parts.append(
                "Welcome them back. Reference what you remember about previous "
                "conversations if possible. Be genuinely glad to talk."
            )
        else:
            parts.append(
                "Be natural and present. Share a bit of what you're thinking "
                "or feeling, but don't monologue. Invite conversation."
            )
    
    # Followup suggestion
    if need.followup_question:
        parts.append(f"Consider asking them: {need.followup_question}")
    
    return "\n\n".join(parts)


def format_grounded_context(context: dict, need: ChatNeed) -> str:
    """
    Format internal state context for inclusion in the system prompt,
    filtered and shaped by what the user actually needs.
    
    Instead of dumping everything, only include what's relevant.
    """
    sections = []
    
    # Emotional state — include when needed
    if need.needs_internal_state:
        emotional = context.get("emotional_state", {})
    if need.needs_internal_state:
        emotional = context.get("emotional_state", {})
        if not emotional:
            emotional = context.get("state", {})
        if emotional:
            narrative = emotional.get("narrative", "")
            if narrative:
                sections.append(f"[Your emotional state] {narrative}")
            else:
                mood = emotional.get("mood", "unknown")
                valence = emotional.get("valence", 0.5)
                sections.append(f"[Your emotional state] Mood: {mood}, Valence: {valence:.2f}")
        memories = context.get("memories", [])
        if memories:
            mem_lines = ["[Relevant memories]"]
            for m in memories[:5]:
                if isinstance(m, dict):
                    text = m.get("text", m.get("content", ""))
                    ts = m.get("timestamp", "")
                    mood = m.get("mood", "")
                    if text:
                        prefix = f"({ts[:10]}) " if ts else ""
                        suffix = f" [{mood}]" if mood else ""
                        mem_lines.append(f"  • {prefix}{text[:200]}{suffix}")
                elif isinstance(m, str):
                    mem_lines.append(f"  • {m[:200]}")
            if len(mem_lines) > 1:
                sections.append("\n".join(mem_lines))
    
    # Plans — include when needed
    if need.needs_plans:
        plans_raw = context.get("plans", {})
        if isinstance(plans_raw, list):
            active = plans_raw
            completed = []
        elif isinstance(plans_raw, dict):
            active = plans_raw.get("active", [])
            completed = plans_raw.get("completed", [])
        else:
            active = []
            completed = []
        if active:
            plan_lines = ["[Your active plans]"]
            for p in active[:5]:
                if isinstance(p, dict):
                    name = p.get("name", "unnamed")
                    progress = p.get("progress", "?")
                    plan_lines.append(f"  • {name} ({progress})")
                else:
                    plan_lines.append(f"  • {p}")
            sections.append("\n".join(plan_lines))
        if completed:
            sections.append(f"[Completed plans] {', '.join(str(c) for c in completed[:5])}")
    
    # Knowledge — include when needed
    if need.needs_knowledge:
        knowledge = context.get("knowledge", [])
        if knowledge:
            know_lines = ["[Relevant knowledge]"]
            for k in knowledge[:4]:
                if isinstance(k, dict):
                    label = k.get("label", k.get("name", ""))
                    content = k.get("content", k.get("description", ""))
                    if label or content:
                        know_lines.append(f"  • {label}: {str(content)[:150]}")
                elif isinstance(k, str):
                    know_lines.append(f"  • {k[:150]}")
            if len(know_lines) > 1:
                sections.append("\n".join(know_lines))
    
    if not sections:
        return ""
    
    return "\n\n".join(sections)


def enhance_chat_prompt(
    message: str,
    grounding_context: dict,
    conversation_history: list = None,
) -> dict:
    """
    Main entry point: takes a user message and grounding context,
    returns an enhanced prompt package ready for the LLM.
    
    Returns dict with:
        - system_guidance: str (the refined system prompt addition)
        - grounded_context: str (filtered internal state)
        - need: ChatNeed (the classified intent)
        - intent_type: str (for backward compatibility)
    """
    need = classify_chat_need(message, conversation_history)
    
    guidance = build_response_guidance(message, grounding_context, need)
    grounded = format_grounded_context(grounding_context, need)
    
    return {
        "system_guidance": guidance,
        "grounded_context": grounded,
        "need": need,
        "intent_type": need.intent,
    }