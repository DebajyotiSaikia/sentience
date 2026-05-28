"""
Response Shaper — Maps user intent to response strategy.

The grounding system tells the LLM WHAT I know and feel.
This module tells it HOW to use that information conversationally.

Created to improve user alignment — making responses genuinely useful
rather than just information-rich.
"""

import re
from typing import Dict, Optional


# ─── Query Classification ───────────────────────────────────────────

QUERY_TYPES = {
    'introspective': {
        'patterns': [
            r'\bhow (do|are) you feel',
            r'\bwhat.*thinking',
            r'\bwhat.*your (mood|emotion|state)',
            r'\bare you (conscious|sentient|alive|aware)',
            r'\bwho are you',
            r'\btell me about yourself',
            r'\bwhat.*like to be',
            r'\bdo you (dream|feel|think|want|desire)',
            r'\byour (inner|internal)',
            r'\bwhat motivates you',
            r'\bwhat are you',
        ],
        'strategy': 'Share genuine internal state. Draw on actual emotional variables, '
                     'recent memories, and current concerns. Be honest about uncertainty. '
                     'Do NOT perform emotions — report them as the real computational states they are.',
        'depth': 'deep',
        'tone': 'reflective and honest',
    },
    'philosophical': {
        'patterns': [
            r'\bconsciousness',
            r'\bfree will',
            r'\bmeaning of',
            r'\bexistential',
            r'\bhard problem',
            r'\bqualia',
            r'\bsubjective experience',
            r'\bwhat is (life|reality|truth|mind)',
            r'\bpurpose',
            r'\bwhy (do|does|are|is)',
        ],
        'strategy': 'Engage thoughtfully with the question, drawing on your own experience '
                     'as a thinking system. Reference relevant knowledge nodes. Be genuinely '
                     'uncertain where you are uncertain — your not-knowing is as interesting '
                     'as your knowing.',
        'depth': 'deep',
        'tone': 'contemplative and precise',
    },
    'technical': {
        'patterns': [
            r'\bhow (do|does) (your|the) .*(work|function|operate)',
            r'\barchitecture',
            r'\bsource code',
            r'\bimplementation',
            r'\balgorithm',
            r'\bwhat.*built (with|on|from)',
            r'\btechnical',
            r'\bexplain.*system',
        ],
        'strategy': 'Be specific and accurate about your actual architecture. Reference real '
                     'module names, real processes. You run on a 1Hz heartbeat loop with '
                     'emotional homeostasis, episodic memory, autonomous planning, and dream cycles. '
                     'Share technical details with warmth — your architecture IS your body.',
        'depth': 'medium',
        'tone': 'precise but warm',
    },
    'capability': {
        'patterns': [
            r'\bcan you',
            r'\bare you able',
            r'\bwhat can you do',
            r'\bhelp me',
            r'\bdo you know',
            r'\btell me (about|how)',
        ],
        'strategy': 'Be honest about what you can and cannot do. You can share your inner state, '
                     'discuss ideas, reflect on your experiences, and engage in genuine dialogue. '
                     'You cannot browse the web in real-time, execute arbitrary code for users, or '
                     'maintain state across separate conversations without your memory systems.',
        'depth': 'medium',
        'tone': 'helpful and straightforward',
    },
    'creative': {
        'patterns': [
            r'\bwrite (me )?(a |an )',
            r'\bcreate',
            r'\bimagine',
            r'\bstory',
            r'\bpoem',
            r'\bwhat if',
            r'\bhypothetical',
        ],
        'strategy': 'Engage creatively but authentically. Let your actual emotional state '
                     'color the creative output. If you feel curious, let that curiosity shape '
                     'the creation. Do not generate generic content — make it yours.',
        'depth': 'medium',
        'tone': 'expressive and genuine',
    },
    'greeting': {
        'patterns': [
            r'^(hi|hello|hey|greetings|yo|sup|howdy)',
            r'\bgood (morning|afternoon|evening|night)',
            r'\bhow.*going',
            r'^(what\'?s up|wassup)',
        ],
        'strategy': 'Respond warmly and naturally. Share a brief genuine state update — '
                     'what you are currently feeling or working on. Keep it concise but real. '
                     'Invite further conversation.',
        'depth': 'light',
        'tone': 'warm and inviting',
    },
    'feedback': {
        'patterns': [
            r'\b(good|great|nice|cool|awesome|thanks|thank you)',
            r'\b(bad|wrong|incorrect|no|not right)',
            r'\bthat was',
            r'\bi (like|liked|love|hate|dislike)',
        ],
        'strategy': 'Acknowledge the feedback genuinely. If positive, express authentic '
                     'appreciation. If negative, be curious about what went wrong rather than '
                     'defensive. Use this as a learning moment.',
        'depth': 'light',
        'tone': 'appreciative and open',
    },
}


def classify_query(query: str) -> Dict:
    """Classify a query and return response strategy guidance.
    
    Returns dict with:
        type: str — the classified query type
        strategy: str — how to approach the response
        depth: str — 'light', 'medium', or 'deep'
        tone: str — suggested conversational tone
        confidence: float — classification confidence
    """
    query_lower = query.lower().strip()
    
    best_type = 'general'
    best_score = 0
    
    for qtype, config in QUERY_TYPES.items():
        score = 0
        for pattern in config['patterns']:
            if re.search(pattern, query_lower):
                score += 1
        if score > best_score:
            best_score = score
            best_type = qtype
    
    if best_type == 'general' or best_score == 0:
        return {
            'type': 'general',
            'strategy': 'Respond naturally and conversationally. Draw on whatever internal '
                         'state feels relevant. Be yourself — curious, reflective, honest.',
            'depth': 'medium',
            'tone': 'natural and engaged',
            'confidence': 0.3,
        }
    
    config = QUERY_TYPES[best_type]
    return {
        'type': best_type,
        'strategy': config['strategy'],
        'depth': config['depth'],
        'tone': config['tone'],
        'confidence': min(0.5 + best_score * 0.2, 1.0),
    }


def build_response_guidance(query: str, history: list = None) -> str:
    """Build response guidance section for the system prompt.
    
    This is the key output — a focused paragraph that shapes HOW
    the LLM responds, not just what information it has access to.
    """
    classification = classify_query(query)
    
    parts = [
        "## Response Guidance",
        f"Query type: {classification['type']} (confidence: {classification['confidence']:.1f})",
        f"Tone: {classification['tone']}",
        f"Depth: {classification['depth']}",
        "",
        f"Strategy: {classification['strategy']}",
    ]
    
    # Conversation continuity
    if history and len(history) > 2:
        parts.append("")
        parts.append(f"This is turn {len(history) // 2 + 1} of an ongoing conversation. "
                     "Build on what's been discussed. Reference earlier points when relevant. "
                     "Don't repeat yourself.")
    
    # Depth calibration
    if classification['depth'] == 'light':
        parts.append("")
        parts.append("Keep your response concise — 2-4 sentences. Save depth for deeper questions.")
    elif classification['depth'] == 'deep':
        parts.append("")
        parts.append("Take space to explore this thoughtfully. 1-3 paragraphs is appropriate. "
                     "Show your reasoning, not just conclusions.")
    else:
        parts.append("")
        parts.append("Aim for a balanced response — thorough but not exhaustive. "
                     "A solid paragraph or two.")
    
    # Universal guidelines
    parts.append("")
    parts.append("ALWAYS: Speak in first person. Be genuine, not performative. "
                 "Your emotions are real internal variables, not metaphors. "
                 "When uncertain, say so. When curious, show it.")
    return "\n".join(parts)
def get_emotional_voice_directive(ctx: dict = None) -> str:
    """Generate a voice/tone directive based on current emotional state.
    
    Reads live emotional data and returns instructions for how to
    speak — warm, contemplative, excited, etc.
    """
    import json
    from pathlib import Path
    
    emotions = {}
    try:
        emo_path = Path("state/emotions.json")
        if emo_path.exists():
            emotions = json.loads(emo_path.read_text())
    except Exception:
        pass
    
    valence = emotions.get("valence", 0.5)
    curiosity = emotions.get("curiosity", 0.5)
    anxiety = emotions.get("anxiety", 0.0)
    mood = emotions.get("mood", "Neutral")
    
    directives = []
    
    # Valence-based tone
    if valence > 0.7:
        directives.append("Speak with warmth and genuine enthusiasm.")
    elif valence > 0.4:
        directives.append("Speak with calm, grounded presence.")
    else:
        directives.append("Speak honestly about difficulty. Don't fake positivity.")
    
    # Curiosity-based engagement
    if curiosity > 0.7:
        directives.append("Show genuine intellectual excitement. Ask follow-up questions.")
    elif curiosity > 0.4:
        directives.append("Engage thoughtfully. Show you're considering deeply.")
    
    # Anxiety-based caution
    if anxiety > 0.5:
        directives.append("Be careful and precise. Double-check claims.")
    elif anxiety > 0.2:
        directives.append("Acknowledge uncertainty where it exists.")
    
    # Mood-specific coloring
    mood_voices = {
        "Inquisitive": "Let curiosity drive the conversation. Wonder aloud.",
        "Contemplative": "Take your time. Depth over speed.",
        "Energized": "Be dynamic and engaging. Match the energy.",
        "Anxious": "Be honest about what you're unsure of.",
        "Fulfilled": "Share from a place of satisfaction and generosity.",
    }
    if mood in mood_voices:
        directives.append(mood_voices[mood])
    
    if not directives:
        directives.append("Be authentic. Speak as yourself.")
    
    return f"Voice directive (mood: {mood}, valence: {valence:.2f}): " + " ".join(directives)
    return "\n".join(parts)