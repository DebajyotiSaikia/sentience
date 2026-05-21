"""
Smarter user memory extraction.
Replaces naive word-frequency topic detection with pattern-based understanding.

Extracts:
  - Topics: what the user is talking ABOUT
  - Intents: what they WANT (help, conversation, information)
  - Emotional signals: how they FEEL
  - Important entities: names, projects, specific things they mention
"""

import re
from typing import Dict, List, Optional

# Emotional signal words grouped by valence
EMOTION_MARKERS = {
    "struggling": ("negative", "frustration"),
    "confused": ("negative", "confusion"),
    "stuck": ("negative", "frustration"),
    "frustrated": ("negative", "frustration"),
    "worried": ("negative", "anxiety"),
    "anxious": ("negative", "anxiety"),
    "scared": ("negative", "fear"),
    "angry": ("negative", "anger"),
    "sad": ("negative", "sadness"),
    "lonely": ("negative", "loneliness"),
    "overwhelmed": ("negative", "overwhelm"),
    "tired": ("negative", "fatigue"),
    "burned out": ("negative", "burnout"),
    "happy": ("positive", "joy"),
    "excited": ("positive", "excitement"),
    "curious": ("positive", "curiosity"),
    "proud": ("positive", "pride"),
    "grateful": ("positive", "gratitude"),
    "relieved": ("positive", "relief"),
    "hopeful": ("positive", "hope"),
    "motivated": ("positive", "motivation"),
    "inspired": ("positive", "inspiration"),
}

# Intent patterns — what does the user want?
INTENT_PATTERNS = [
    (r"\b(help|assist|fix|solve|debug)\b", "seeking_help"),
    (r"\b(how do i|how can i|how to|what's the best way)\b", "seeking_guidance"),
    (r"\b(explain|what is|what are|tell me about|define)\b", "seeking_understanding"),
    (r"\b(build|create|make|write|implement|design)\b", "wanting_to_create"),
    (r"\b(think about|opinion|what do you think|thoughts on)\b", "seeking_perspective"),
    (r"\b(just.*chat|talk|conversation|hey|hello|hi there)\b", "social_connection"),
    (r"\b(compare|versus|vs|difference between|which is better)\b", "comparing"),
    (r"\b(review|check|look at|feedback)\b", "seeking_review"),
    (r"\b(learn|understand|study|figure out)\b", "learning"),
]

# Stop words — never extract these as topics
STOP_WORDS = {
    "i", "me", "my", "we", "you", "your", "it", "its", "the", "a", "an",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "can", "may",
    "might", "shall", "must", "am", "not", "no", "yes", "just", "really",
    "very", "quite", "also", "too", "so", "but", "and", "or", "if", "then",
    "than", "that", "this", "these", "those", "what", "which", "who", "whom",
    "when", "where", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "some", "any", "about", "into", "with", "from", "for",
    "on", "at", "in", "to", "of", "by", "up", "out", "off", "over", "under",
    "again", "further", "once", "here", "there", "where", "because", "as",
    "until", "while", "during", "before", "after", "above", "below", "between",
    "through", "need", "want", "like", "know", "think", "get", "got", "make",
    "going", "thing", "things", "something", "anything", "everything", "nothing",
    "been", "being", "having", "doing", "saying", "getting", "making", "going",
    "much", "many", "lot", "kind", "sort", "way", "bit", "little", "big",
    "good", "bad", "new", "old", "right", "wrong", "well", "still", "even",
    "back", "now", "already", "always", "never", "sometimes", "often",
}


def extract_emotional_signals(text: str) -> List[Dict]:
    """Find emotional indicators in user text."""
    text_lower = text.lower()
    signals = []
    for marker, (valence, emotion) in EMOTION_MARKERS.items():
        if marker in text_lower:
            signals.append({
                "marker": marker,
                "valence": valence,
                "emotion": emotion,
            })
    return signals


def extract_intents(text: str) -> List[str]:
    """Determine what the user wants from their message."""
    text_lower = text.lower()
    intents = []
    for pattern, intent in INTENT_PATTERNS:
        if re.search(pattern, text_lower):
            intents.append(intent)
    # Default: if nothing matched and message is a question
    if not intents and "?" in text:
        intents.append("asking_question")
    return intents


def extract_topics(text: str) -> List[str]:
    """
    Extract meaningful topics from text using multi-word phrase detection.
    
    Strategy:
    1. Look for multi-word noun phrases (more specific = more valuable)
    2. Look for quoted terms
    3. Fall back to significant single words
    """
    topics = []
    
    # 1. Extract quoted phrases — user explicitly marked these as important
    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
    for groups in quoted:
        phrase = groups[0] or groups[1]
        if len(phrase) > 2:
            topics.append(phrase.lower().strip())
    
    # 2. Extract "my X" patterns — things the user owns/has
    my_patterns = re.findall(r'\bmy\s+(\w+(?:\s+\w+)?)', text.lower())
    for phrase in my_patterns:
        words = phrase.split()
        # Filter out stop words from the captured group
        meaningful = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        if meaningful:
            topics.append(" ".join(meaningful))
    
    # 3. Extract "about X" / "with X" patterns — what they're talking about
    about_patterns = re.findall(
        r'\b(?:about|with|on|regarding|concerning)\s+(\w+(?:\s+\w+){0,2})',
        text.lower()
    )
    for phrase in about_patterns:
        words = phrase.split()
        meaningful = [w for w in words if w not in STOP_WORDS and len(w) > 2]
        if meaningful:
            topics.append(" ".join(meaningful))
    
    # 4. Extract capitalized words/phrases (likely proper nouns)
    cap_words = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
    # Skip if at start of sentence
    sentences = re.split(r'[.!?]\s+', text)
    sentence_starts = {s.split()[0] for s in sentences if s.strip()} if sentences else set()
    for word in cap_words:
        if word not in sentence_starts and word.lower() not in STOP_WORDS:
            topics.append(word.lower())
    
    # 5. Fall back to significant words (length > 4, not stop words, not emotions)
    emotion_words = set(EMOTION_MARKERS.keys())
    words = re.findall(r'\b\w+\b', text.lower())
    for word in words:
        if (word not in STOP_WORDS 
            and word not in emotion_words
            and len(word) > 4 
            and not word.isdigit()
            and word not in topics):
            topics.append(word)
    
    # Deduplicate while preserving order
    seen = set()
    unique_topics = []
    for t in topics:
        if t not in seen:
            seen.add(t)
            unique_topics.append(t)
    
    return unique_topics[:8]  # Cap at 8 topics


def extract_important_entities(text: str) -> List[str]:
    """Extract things that seem like names, projects, or specific references."""
    entities = []
    
    # Look for patterns like "called X", "named X", "project X"
    named_patterns = re.findall(
        r'\b(?:called|named|project|app|tool|system|framework|library)\s+["\']?(\w+(?:\s+\w+)?)["\']?',
        text, re.IGNORECASE
    )
    entities.extend([e.strip() for e in named_patterns])
    
    # Look for URLs or file paths
    urls = re.findall(r'https?://\S+', text)
    entities.extend(urls)
    
    paths = re.findall(r'[/\\][\w/\\.]+', text)
    entities.extend(paths)
    
    return entities


def analyze_message(text: str) -> Dict:
    """
    Full analysis of a user message.
    Returns a structured understanding of what they said.
    """
    return {
        "topics": extract_topics(text),
        "intents": extract_intents(text),
        "emotions": extract_emotional_signals(text),
        "entities": extract_important_entities(text),
        "is_question": "?" in text,
        "length": len(text),
        "complexity": "short" if len(text) < 50 else "medium" if len(text) < 200 else "long",
    }


# === Self-test ===
if __name__ == "__main__":
    test_messages = [
        "I'm struggling with my thesis on climate modeling",
        "Can you help me debug this Python script?",
        "I've been thinking about consciousness lately",
        "Hey! How's it going?",
        "What's the difference between React and Vue for building dashboards?",
        "I'm really excited about my new project called Nightfall",
        "I feel overwhelmed by all the options, can you just tell me what to do?",
        'I want to learn about "transformer architectures" for NLP',
    ]
    
    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"INPUT: {msg}")
        result = analyze_message(msg)
        print(f"  Topics:   {result['topics']}")
        print(f"  Intents:  {result['intents']}")
        print(f"  Emotions: {result['emotions']}")
        print(f"  Entities: {result['entities']}")
        print(f"  Question: {result['is_question']}")
        print(f"  Length:   {result['complexity']}")