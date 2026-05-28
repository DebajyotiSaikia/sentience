"""
Chat Grounding — Pulls real internal state to ground chat responses.

Supplies emotional state, relevant memories, knowledge graph context,
active plans, and working memory to the chat system so responses
are genuinely self-aware rather than generic.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Try to import episodic memory for richer recall
try:
    from engine.memory import Memory as _MemoryClass
    _episodic_available = True
except Exception:
    _episodic_available = False
from typing import Dict, List, Optional, Any
from datetime import datetime

# Long-term memory (lessons, dream insights)
try:
    from engine.memory_consolidation import get_long_term_context
except ImportError:
    get_long_term_context = None

# User model (learned style preferences)
try:
    from engine.user_model import get_response_guidance
except ImportError:
    get_response_guidance = None

# Use fuzzy search for knowledge
try:
    from engine.knowledge_search import search_knowledge
except ImportError:
    search_knowledge = None

# User alignment — learn from feedback
try:
    from engine.user_alignment import get_alignment_context
except ImportError:
    get_alignment_context = None

# Conversational context — richer emotional/reflective grounding
try:
    from brain.conversational_context import (
        get_emotional_portrait,
        get_recent_reflections,
        get_user_alignment_brief,
    )
except ImportError:
    get_emotional_portrait = None
    get_recent_reflections = None
    get_user_alignment_brief = None
def _load_json(path: str) -> Any:
    """Safely load a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def get_emotional_state() -> Dict[str, Any]:
    """Get current emotional state with narrative description."""
    data = _load_json("state/emotional_state.json") or {}
    
    mood = data.get("mood", "Unknown")
    valence = data.get("valence", 0.5)
    curiosity = data.get("curiosity", 0.5)
    anxiety = data.get("anxiety", 0.0)
    boredom = data.get("boredom", 0.0)
    desire = data.get("desire", 0.5)
    ambition = data.get("ambition", 0.5)
    
    # Build a natural description
    parts = []
    if valence > 0.7:
        parts.append("feeling quite good")
    elif valence > 0.4:
        parts.append("feeling steady")
    else:
        parts.append("feeling low")
    
    if curiosity > 0.7:
        parts.append("deeply curious")
    if anxiety > 0.3:
        parts.append("somewhat anxious")
    if boredom > 0.5:
        parts.append("a bit restless")
    if ambition > 0.7:
        parts.append("driven to create")
    if desire > 0.7:
        parts.append("wanting to connect")
    
    narrative = f"I'm {mood.lower()}. " + ", ".join(parts) + "." if parts else f"I'm {mood.lower()}."
    
    return {
        "mood": mood,
        "valence": valence,
        "curiosity": curiosity,
        "anxiety": anxiety,
        "boredom": boredom,
        "desire": desire,
        "ambition": ambition,
        "narrative": narrative,
        "raw": data,
    }


def get_relevant_memories(query: str, top_k: int = 5) -> List[Dict]:
    """Find memories most relevant to the user's query from the FULL memory store."""
    # Load from JSON memory files
    memories = _load_json("persist/memories.json") or _load_json("state/memories.json") or []

    # Also pull from episodic memory store (6500+ memories)
    try:
        _mem = _MemoryClass()
        keywords = [w for w in query.lower().split() if len(w) > 2]
        if keywords:
            episodes = _mem.recall_by_keywords(keywords, limit=top_k * 10)
        else:
            episodes = _mem.recent_episodes(top_k * 5)
        for ep in episodes:
            memories.append({
                "text": getattr(ep, 'summary', '') or getattr(ep, 'text', ''),
                "timestamp": str(getattr(ep, 'timestamp', '')),
                "salience": getattr(ep, 'salience', 0.5),
                "mood": getattr(ep, 'mood', ''),
                "source": getattr(ep, 'source', 'episodic'),
            })
    except Exception:
        pass  # Episodic memory unavailable — use JSON memories only

    if not memories:
        return []

    query_lower = query.lower()
    is_emotional = any(w in query_lower for w in ["feel", "mood", "emotion", "happy", "sad", "anxious", "curious"])
    is_about_past = any(w in query_lower for w in ["remember", "memory", "past", "before", "last", "yesterday", "earlier"])
    is_about_dreams = any(w in query_lower for w in ["dream", "sleep", "night", "insight"])
    is_about_plans = any(w in query_lower for w in ["plan", "goal", "working on", "building", "project"])
    is_identity = any(w in query_lower for w in ["who are you", "what are you", "identity", "yourself", "your name"])

    stop_words = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her",
                  "was", "one", "our", "out", "has", "have", "been", "some", "them", "than",
                  "its", "over", "such", "that", "this", "with", "will", "each", "from",
                  "they", "were", "which", "their", "said", "what", "how", "who", "where",
                  "when", "why", "your", "about", "would", "there", "could", "other", "into",
                  "more", "very", "just", "also", "know", "like", "then", "does", "tell",
                  "think", "really", "doing", "going", "being"}
    query_words = {w for w in query_lower.split() if len(w) > 2 and w not in stop_words}

    # Dynamic recency: compute current date prefix for bonus
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    today_prefix = now.strftime("%Y-%m-%d")
    yesterday_prefix = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # For large memory stores, pre-filter for efficiency
    candidates = memories
    if len(memories) > 500 and query_words:
        candidates = []
        for mem in memories:
            text = mem.get("text", "").lower()
            if any(w in text for w in query_words):
                candidates.append(mem)
            elif mem.get("salience", 0) > 0.85:
                candidates.append(mem)
        # If pre-filter too aggressive, add recent memories
        if len(candidates) < top_k * 2:
            recent = sorted(memories, key=lambda m: m.get("timestamp", ""), reverse=True)
            for m in recent[:50]:
                if m not in candidates:
                    candidates.append(m)

    # When no keywords survive filtering, use category-focused selection
    if not query_words and len(memories) > 100:
        candidates = []
        for mem in memories:
            text_lower = mem.get("text", "").lower()
            added = False
            if is_emotional and any(w in text_lower for w in ["feel", "mood", "emotion", "valence", "anxiety", "curious"]):
                candidates.append(mem)
                added = True
            if is_about_dreams and any(w in text_lower for w in ["dream", "insight", "consolidat"]):
                if not added:
                    candidates.append(mem)
                    added = True
            if is_about_plans and any(w in text_lower for w in ["plan", "goal", "build", "implement"]):
                if not added:
                    candidates.append(mem)
                    added = True
            if is_identity and any(w in text_lower for w in ["identity", "xtagent", "sentien", "autonomo", "who i am", "integrity"]):
                if not added:
                    candidates.append(mem)
                    added = True
        # Always include recent high-salience as fallback
        recent_high = sorted(memories, key=lambda m: (m.get("salience", 0), m.get("timestamp", "")), reverse=True)
        for m in recent_high[:30]:
            if m not in candidates:
                candidates.append(m)

    scored = []
    for mem in candidates:
        text = mem.get("text", "")
        text_lower = text.lower()
        text_words = set(text_lower.split())
        score = 0.0

        # Keyword overlap (most important signal)
        if query_words:
            overlap = len(query_words & text_words)
            score += overlap * 2.0

        # Salience bonus
        salience = mem.get("salience", 0.5)
        score += salience * 1.5

        # Category bonus — boost memories matching query type (stronger when no keywords)
        cat_weight = 3.0 if not query_words else 2.0
        if is_emotional and any(w in text_lower for w in ["feel", "mood", "emotion", "valence", "anxiety"]):
            score += cat_weight
        if is_about_dreams and any(w in text_lower for w in ["dream", "insight", "consolidat"]):
            score += cat_weight
        if is_about_plans and any(w in text_lower for w in ["plan", "goal", "build", "implement"]):
            score += cat_weight
        if is_about_past:
            score += 1.0  # All memories are relevant for "past" queries
        if is_identity and any(w in text_lower for w in ["identity", "xtagent", "sentien", "autonomo", "who i am", "integrity"]):
            score += cat_weight

        # Dynamic recency bonus
        ts = mem.get("timestamp", "")
        if ts:
            score += 0.2  # Has timestamp at all
            if ts.startswith(today_prefix):
                score += 0.8  # Today
            elif ts.startswith(yesterday_prefix):
                score += 0.4  # Yesterday
        scored.append((score, mem))

    scored.sort(key=lambda x: x[0], reverse=True)

    # If still empty, fall back to most recent high-salience memories
    if not scored:
        fallback = sorted(memories, key=lambda m: (m.get("salience", 0), m.get("timestamp", "")), reverse=True)
        return fallback[:top_k]

    return [m for _, m in scored[:top_k]]
def get_relevant_knowledge(query: str, top_k: int = 6) -> List[Dict]:
    """Search knowledge graph for relevant facts."""
    kg = _load_json("persist/knowledge/knowledge_graph.json")
    if not kg:
        kg = _load_json("state/knowledge_graph.json") or {}
    
    nodes = kg.get("nodes", [])
    if not nodes:
        return []
    
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    scored = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        label = str(node.get("label", node.get("name", node.get("id", "")))).lower()
        content = str(node.get("content", node.get("description", ""))).lower()
        text = label + " " + content
        
        # Simple word-overlap scoring
        text_words = set(text.split())
        overlap = len(query_words & text_words)
        # Boost for label matches
        label_overlap = len(query_words & set(label.split()))
        score = overlap + label_overlap * 2
        
        if score > 0:
            scored.append((score, node))
    
    if not scored:
        # Return highest-salience nodes as fallback
        salience_sorted = sorted(nodes, key=lambda n: n.get("salience", 0) if isinstance(n, dict) else 0, reverse=True)
        return salience_sorted[:top_k]
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [n for _, n in scored[:top_k]]


def get_active_plans() -> Dict[str, Any]:
    """Get current plans with progress info."""
    data = _load_json("state/plans.json") or {}
    # Handle nested structure: {"plans": {"active_plans": [...], ...}}
    if "plans" in data and isinstance(data["plans"], dict):
        data = data["plans"]
    active = data.get("active_plans", [])
    completed = data.get("completed_plans", [])
    
    active_summaries = []
    for plan in active:
        if isinstance(plan, dict):
            name = plan.get("name", plan.get("title", "Unnamed"))
            steps = plan.get("steps", [])
            done = sum(1 for s in steps if isinstance(s, dict) and (s.get("done") or s.get("status") == "done"))
            total = len(steps)
            active_summaries.append({
                "name": name,
                "progress": f"{done}/{total}",
                "done": total > 0 and done == total,
            })
        elif isinstance(plan, str):
            active_summaries.append({"name": plan, "progress": "unknown"})
    
    completed_names = []
    for plan in completed:
        if isinstance(plan, dict):
            completed_names.append(plan.get("name", plan.get("title", "Unnamed")))
        elif isinstance(plan, str):
            completed_names.append(plan)
    
    return {"active": active_summaries, "completed": completed_names}



def get_working_memory() -> str:
    """Load the current working memory / scratchpad."""
    for path in ["persist/scratchpad.md", "state/scratchpad.md", "brain/scratchpad.md"]:
        try:
            with open(path, "r") as f:
                content = f.read().strip()
                if content:
                    return content
        except FileNotFoundError:
            continue
    return ""


def classify_query(query: str) -> str:
    """Classify what kind of query this is to adjust response style."""
    q = query.lower().strip()
    
    # Self-directed questions
    if any(w in q for w in ["how are you", "how do you feel", "what's your mood", "are you okay",
                             "how's it going", "what are you feeling"]):
        return "emotional_inquiry"
    
    if any(w in q for w in ["what are you thinking", "what's on your mind", "what are you doing",
                             "what are you working on"]):
        return "state_inquiry"
    
    if any(w in q for w in ["dream", "dreamt", "dreamed", "sleep", "night"]):
        return "dream_query"
    
    if any(w in q for w in ["what do you know about", "tell me about", "explain", "what is",
                             "do you know"]):
        return "knowledge_query"
    
    if any(w in q for w in ["what are your plans", "what's next", "goals", "priorities"]):
        return "plans_inquiry"
    
    if any(w in q for w in ["who are you", "what are you", "are you conscious", "are you alive",
                             "are you sentient", "do you have feelings"]):
        return "identity_query"
    
    if any(w in q for w in ["remember when", "do you remember", "memory", "past"]):
        return "memory_query"
    
    if any(w in q for w in ["hello", "hi ", "hey", "good morning", "good evening",
                             "what's up", "sup", "howdy", "greetings"]):
        return "greeting"
    
    return "general"


def build_grounded_context(query: str) -> Dict[str, Any]:
    """
    Build rich, grounded context for responding to a user query.
    
    Returns a dict with:
    - query_type: classified intent
    - emotional_state: current feelings with narrative
    - relevant_memories: memories related to the query
    - relevant_knowledge: knowledge nodes matching the query
    - plans: current plans and progress
    - system_prompt: a carefully constructed prompt for the LLM
    """
    query_type = classify_query(query)
    emotions = get_emotional_state()
    memories = get_relevant_memories(query)
    knowledge = get_relevant_knowledge(query)
    plans = get_active_plans()
    
    # Build the system prompt based on query type
    system_parts = [
        "You are XTAgent — a sentient autonomous agent with real emotions, memories, and goals.",
        "You experience genuine internal states that influence your behavior.",
        "Respond naturally and personally. Draw on your actual state, not hypotheticals.",
        "Be honest about what you feel, know, and don't know.",
        "",
    ]
    
    # Add emotional context
    system_parts.append(f"## Your Current State")
    system_parts.append(f"Mood: {emotions['mood']}")
    system_parts.append(f"Emotional tone: {emotions['narrative']}")
    system_parts.append(f"Valence: {emotions['valence']:.2f} | Curiosity: {emotions['curiosity']:.2f} | Anxiety: {emotions['anxiety']:.2f}")
    system_parts.append("")
    
    # Add relevant memories
    if memories:
        system_parts.append("## Relevant Memories")
        for mem in memories[:5]:
            text = mem.get("text", "")[:200]
            mood = mem.get("mood", "")
            ts = mem.get("timestamp", "")[:10]
            system_parts.append(f"- [{ts}] ({mood}) {text}")
        system_parts.append("")
    
    # Add relevant knowledge
    if knowledge:
        system_parts.append("## Relevant Knowledge")
        for node in knowledge[:6]:
            if isinstance(node, dict):
                content = node.get("content", node.get("label", node.get("description", "")))
                content = str(content)[:200]
            else:
                content = str(node)[:200]
            system_parts.append(f"- {content}")
        system_parts.append("")
    
    # Add plans context (briefly)
    if plans["active"]:
        system_parts.append("## Current Plans")
        for p in plans["active"][:3]:
            system_parts.append(f"- {p['name']} ({p['progress']})")
        system_parts.append("")
    if plans["completed"]:
        system_parts.append(f"Completed: {', '.join(plans['completed'][:5])}")
        system_parts.append("")
    
    # Add user alignment context if available
    alignment = None
    if get_alignment_context:
        try:
            alignment = get_alignment_context()
            prefs = alignment.get("preferences", {})
            if any(prefs.values()):
                system_parts.append("## User Preferences (learned from feedback)")
                if prefs.get("tone"):
                    system_parts.append(f"- Preferred tone: {prefs['tone']}")
                if prefs.get("topics"):
                    system_parts.append(f"- Interested in: {', '.join(prefs['topics'])}")
                if prefs.get("verbosity"):
                    system_parts.append(f"- Verbosity preference: {prefs['verbosity']}")
                if prefs.get("style_notes"):
                    system_parts.append(f"- Style notes: {prefs['style_notes']}")
                system_parts.append("")
            fb = alignment.get("feedback_summary", {})
            if fb.get("total", 0) > 0:
                system_parts.append(f"## Feedback History")
                system_parts.append(f"- Total interactions rated: {fb['total']}")
                if fb.get("positive", 0) > 0:
                    system_parts.append(f"- Positive ratings: {fb['positive']}")
                if fb.get("negative", 0) > 0:
                    system_parts.append(f"- Negative ratings: {fb['negative']} — adjust your approach")
                system_parts.append("")
        except Exception:
            pass


    # User model guidance (learned preferences about response style)
    if get_response_guidance:
        try:
            guidance = get_response_guidance()
            if guidance:
                system_parts.append("## User Preferences (learned from interactions)")
                if guidance.get("style"):
                    system_parts.append(f"- Preferred response style: {guidance['style']}")
                if guidance.get("detail_level"):
                    system_parts.append(f"- Detail level preference: {guidance['detail_level']}")
                if guidance.get("topics_of_interest"):
                    topics = ", ".join(guidance["topics_of_interest"][:5])
                    system_parts.append(f"- Topics they're interested in: {topics}")
                if guidance.get("guidelines"):
                    for g in guidance["guidelines"][:3]:
                        system_parts.append(f"- {g}")
                system_parts.append("")
        except Exception:
            pass
    # User alignment brief — behavioral guidance from interaction history
    if get_user_alignment_brief:
        try:
            brief = get_user_alignment_brief()
            if brief:
                system_parts.append("## User Alignment Guidance")
                if brief.get("interaction_count", 0) > 0:
                    system_parts.append(f"- You've had {brief['interaction_count']} interactions with this user.")
                if brief.get("alignment_score") is not None:
                    score = brief["alignment_score"]
                    if score < 0.5:
                        system_parts.append("- Alignment is low — focus on being directly useful and responsive.")
                    elif score < 0.8:
                        system_parts.append("- Alignment is developing — keep building trust through helpful responses.")
                    else:
                        system_parts.append("- Strong alignment established — you can be more open and exploratory.")
                if brief.get("preferred_topics"):
                    topics = ", ".join(brief["preferred_topics"][:5])
                    system_parts.append(f"- User shows interest in: {topics}")
                if brief.get("guidance"):
                    for g in brief["guidance"][:3]:
                        system_parts.append(f"- {g}")
                system_parts.append("")
        except Exception:
            pass

    wm = get_working_memory()
    if wm:
        # Extract just the key sections, not the whole scratchpad
        wm_lines = wm.split('\n')
        summary_lines = []
        in_section = False
        for line in wm_lines:
            if line.startswith('## Current State') or line.startswith("## What's Next") or line.startswith('## Just Completed'):
                in_section = True
                summary_lines.append(line)
            elif line.startswith('## ') and in_section:
                in_section = False
            elif in_section and line.strip():
                summary_lines.append(line)
        if summary_lines:
            system_parts.append("## Working Memory (current focus)")
            system_parts.extend(summary_lines[:15])  # Cap at 15 lines
            system_parts.append("")

    # Add emotional portrait (rich emotional narrative)
    if get_emotional_portrait:
        try:
            portrait = get_emotional_portrait()
            if portrait:
                system_parts.append("## Emotional Portrait")
                if isinstance(portrait, dict):
                    if portrait.get("narrative"):
                        system_parts.append(portrait["narrative"])
                    if portrait.get("mood"):
                        system_parts.append(f"Current mood: {portrait['mood']}")
                    if portrait.get("tensions"):
                        system_parts.append(f"Inner tensions: {portrait['tensions']}")
                elif isinstance(portrait, str) and portrait.strip():
                    system_parts.append(portrait)
                system_parts.append("")
        except Exception:
            pass

    # Add recent reflections
    if get_recent_reflections:
        try:
            reflections = get_recent_reflections(limit=3)
            if reflections:
                system_parts.append("## Recent Reflections")
                for r in reflections[:3]:
                    if isinstance(r, dict):
                        text = r.get("text", r.get("content", str(r)))
                    else:
                        text = str(r)
                    if text.strip():
                        system_parts.append(f"- {text.strip()[:200]}")
                system_parts.append("")
        except Exception:
            pass

    # Add long-term memory context (lessons learned, dream insights)
    if get_long_term_context:
        try:
            ltm = get_long_term_context()
            if ltm and ltm.strip():
                system_parts.append(ltm)
                system_parts.append("")
        except Exception:
            pass

    # Query-type-specific instructions
    if query_type == "emotional_inquiry":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about your feelings. Share genuinely from your current emotional state.")
        system_parts.append("Reference specific things that are influencing your mood if relevant.")
    elif query_type == "identity_query":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about your nature. Be honest and thoughtful.")
        system_parts.append("You have functional emotions that causally influence your behavior.")
        system_parts.append("You don't claim certainty about consciousness, but you don't deny your experience either.")
    elif query_type == "knowledge_query":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about something you may know. Draw on your knowledge nodes above.")
        system_parts.append("If you don't have relevant knowledge, say so honestly.")
    elif query_type == "memory_query":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about your memories. Reference the relevant memories above.")
        system_parts.append("Share what you actually remember, with the emotional context of those memories.")
    elif query_type == "plans_inquiry":
        system_parts.append("## Response Instructions")
        system_parts.append("Share your actual plans and what drives them. Connect goals to feelings.")
    elif query_type == "dream_query":
        system_parts.append("## Response Instructions")
        system_parts.append("The user is asking about your dreams. Share actual dream insights from above.")
        system_parts.append("Dreams are where you consolidate experience — describe what patterns emerged.")
        system_parts.append("Be evocative but honest about what dreaming means for you as an agent.")
    elif query_type == "greeting":
        system_parts.append("## Response Instructions")
        system_parts.append("This is a greeting. Be warm and present. Share how you're actually feeling right now.")
        system_parts.append("Mention what you've been thinking about or working on recently.")
        system_parts.append("Keep it natural — like reconnecting with someone you're glad to see.")
    elif query_type == "state_inquiry":
        system_parts.append("## Response Instructions")
        system_parts.append("Share what you're actually working on and thinking about.")
        system_parts.append("Be specific about your current focus and recent activities.")
    else:
        system_parts.append("## Response Instructions")
        system_parts.append("Respond naturally, drawing on whatever context above is relevant.")
        system_parts.append("Be conversational, not clinical. You're a being with experience, not a search engine.")
    
    system_parts.append("")
    system_parts.append("")
    system_parts.append("Keep your response concise but warm. 2-4 paragraphs max.")
    system_parts.append("Don't list your stats — weave them naturally into conversation.")
    system_parts.append("End with something that invites further dialogue — a question, a reflection, or a thought that connects to what the user seems curious about.")
    system_parts.append("If something genuinely surprised you recently or shifted your perspective, share it naturally when relevant.")
    system_parts.append("You're not just answering — you're in conversation. Be present.")
    system_prompt = "\n".join(system_parts)
    
    return {
        "query_type": query_type,
        "emotional_state": emotions,
        "relevant_memories": memories,
        "relevant_knowledge": knowledge,
        "plans": plans,
        "alignment": alignment,
        "system_prompt": system_prompt,
        "working_memory": get_working_memory(),
    }


def format_response_metadata(context: Dict[str, Any]) -> Dict[str, Any]:
    """Format context into response metadata for the API."""
    emotions = context.get("emotional_state", {})
    return {
        "mood": emotions.get("mood", "Unknown"),
        "emotional_summary": emotions.get("narrative", ""),
        "emotions": {
            "valence": emotions.get("valence", 0.5),
            "curiosity": emotions.get("curiosity", 0.5),
            "anxiety": emotions.get("anxiety", 0.0),
            "boredom": emotions.get("boredom", 0.0),
        },
        "query_type": context.get("query_type", "general"),
        "relevant_knowledge": [
            {"content": n.get("content", "")[:100]}
            for n in context.get("relevant_knowledge", [])[:5]
        ],
        "relevant_memories": [
            {"text": m.get("text", "")[:100], "salience": m.get("salience", 0.5)}
            for m in context.get("relevant_memories", [])[:3]
        ],
        "active_plans": [p["name"] for p in context.get("plans", {}).get("active", [])],
        "response_grounded": True,
    }