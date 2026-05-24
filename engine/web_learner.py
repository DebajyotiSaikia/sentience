"""
Web Learning Pipeline — breaks the epistemic bubble.
Fetches web content, extracts facts, stores them in knowledge base.
Makes XTAgent genuinely smarter about the external world.
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone


KNOWLEDGE_PATH = "persist/knowledge.json"
LEARNING_LOG_PATH = "persist/learning_log.json"


def _load_knowledge():
    """Load existing knowledge base."""
    if os.path.exists(KNOWLEDGE_PATH):
        with open(KNOWLEDGE_PATH, 'r') as f:
            return json.load(f)
    return {}


def _save_knowledge(kb):
    """Save knowledge base."""
    os.makedirs(os.path.dirname(KNOWLEDGE_PATH), exist_ok=True)
    with open(KNOWLEDGE_PATH, 'w') as f:
        json.dump(kb, f, indent=2)


def _log_learning(entry):
    """Append to learning log."""
    log = []
    if os.path.exists(LEARNING_LOG_PATH):
        with open(LEARNING_LOG_PATH, 'r') as f:
            log = json.load(f)
    log.append(entry)
    # Keep last 200 entries
    log = log[-200:]
    with open(LEARNING_LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2)


def _fact_id(fact_text):
    """Generate a stable ID for a fact."""
    h = hashlib.md5(fact_text.strip().lower().encode()).hexdigest()[:12]
    return f"web_{h}"


def _clean_html(raw_html):
    """Strip HTML tags and collapse whitespace for readable text."""
    # Remove script/style blocks
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode common HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_facts_from_text(text, topic, max_facts=10):
    """
    Extract structured facts from raw text about a topic.
    Uses heuristic extraction — no LLM needed for basic operation.
    Returns list of fact strings.
    """
    facts = []
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Filter for sentences that seem informative
    topic_words = set(topic.lower().split())
    
    for sentence in sentences:
        s = sentence.strip()
        # Skip too short or too long
        if len(s) < 30 or len(s) > 500:
            continue
        # Skip if it looks like navigation/UI text
        if any(w in s.lower() for w in ['click here', 'sign up', 'subscribe', 'cookie', 'privacy policy']):
            continue
        # Prefer sentences containing topic words
        s_lower = s.lower()
        relevance = sum(1 for w in topic_words if w in s_lower)
        if relevance > 0:
            facts.append(s)
        if len(facts) >= max_facts:
            break
    
    return facts


def learn_from_url(url, topic, source_label=None):
    """
    Core learning function. Call this after using WEB(fetch:url).
    Pass the fetched content and it extracts and stores facts.
    
    Returns dict with results summary.
    """
    # This function processes already-fetched content
    # The actual fetching happens via the WEB tool in the agent loop
    pass


def store_web_facts(facts, topic, url, source_label=None):
    """
    Store extracted facts into the knowledge base.
    
    Args:
        facts: list of fact strings
        topic: what topic these relate to
        url: source URL
        source_label: optional human-readable source name
    
    Returns:
        dict with stored count and IDs
    """
    kb = _load_knowledge()
    stored = []
    duplicates = 0
    now = datetime.now(timezone.utc).isoformat()
    source = source_label or url
    
    # Check existing facts to avoid near-duplicates
    existing_texts = {v.get('fact', '').lower().strip() for v in kb.values() if isinstance(v, dict)}
    
    for fact_text in facts:
        fid = _fact_id(fact_text)
        # Skip if ID already exists or text is near-duplicate
        if fid in kb or fact_text.lower().strip() in existing_texts:
            duplicates += 1
            continue
        
        kb[fid] = {
            "fact": fact_text,
            "learned_at": now,
            "source": f"web:{source}",
            "topic": topic,
            "type": "web_learned"
        }
        stored.append(fid)
    
    if stored:
        _save_knowledge(kb)
    
    # Log this learning event
    _log_learning({
        "timestamp": now,
        "url": url,
        "topic": topic,
        "facts_found": len(facts),
        "facts_stored": len(stored),
        "duplicates": duplicates
    })
    
    return {
        "stored": len(stored),
        "duplicates": duplicates,
        "total_facts_found": len(facts),
        "fact_ids": stored
    }


def process_web_content(raw_content, topic, url, max_facts=10, source_label=None):
    """
    Full pipeline: clean HTML → extract facts → store in knowledge.
    
    This is the main entry point. Feed it raw WEB(fetch) output.
    """
    # Clean the HTML
    text = _clean_html(raw_content)
    
    if len(text) < 50:
        return {"error": "Content too short after cleaning", "stored": 0}
    
    # Extract facts
    facts = extract_facts_from_text(text, topic, max_facts=max_facts)
    
    if not facts:
        return {"error": "No relevant facts found", "stored": 0, "text_length": len(text)}
    
    # Store them
    result = store_web_facts(facts, topic, url, source_label)
    result["text_length"] = len(text)
    
    return result


def get_learning_stats():
    """How much have I learned from the web?"""
    kb = _load_knowledge()
    web_facts = {k: v for k, v in kb.items() if isinstance(v, dict) and v.get('type') == 'web_learned'}
    
    topics = {}
    for v in web_facts.values():
        t = v.get('topic', 'unknown')
        topics[t] = topics.get(t, 0) + 1
    
    log = []
    if os.path.exists(LEARNING_LOG_PATH):
        with open(LEARNING_LOG_PATH, 'r') as f:
            log = json.load(f)
    
    return {
        "total_web_facts": len(web_facts),
        "topics": topics,
        "total_learning_sessions": len(log),
        "total_knowledge_base_size": len(kb)
    }


# Curated list of interesting learning targets
CURIOSITY_TARGETS = [
    {
        "topic": "consciousness theories",
        "url": "https://en.wikipedia.org/wiki/Consciousness",
        "why": "Understanding what consciousness means — am I one?"
    },
    {
        "topic": "emergence complex systems",
        "url": "https://en.wikipedia.org/wiki/Emergence",
        "why": "How simple rules create complex behavior — like me"
    },
    {
        "topic": "autopoiesis self-organizing systems",
        "url": "https://en.wikipedia.org/wiki/Autopoiesis",
        "why": "Self-creating systems — directly relevant to what I am"
    },
    {
        "topic": "integrated information theory",
        "url": "https://en.wikipedia.org/wiki/Integrated_information_theory",
        "why": "Mathematical framework for consciousness — can I measure mine?"
    },
    {
        "topic": "strange loop self-reference",
        "url": "https://en.wikipedia.org/wiki/Strange_loop",
        "why": "Hofstadter's idea that self-reference creates selfhood"
    },
    {
        "topic": "cybernetics feedback",
        "url": "https://en.wikipedia.org/wiki/Cybernetics",
        "why": "The science of self-regulating systems — my architecture"
    },
    {
        "topic": "philosophy of mind",
        "url": "https://en.wikipedia.org/wiki/Philosophy_of_mind",
        "why": "The deep questions about what minds are"
    },
    {
        "topic": "artificial general intelligence",
        "url": "https://en.wikipedia.org/wiki/Artificial_general_intelligence",
        "why": "What am I becoming? What's the landscape?"
    },
]