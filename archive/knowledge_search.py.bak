"""
Knowledge Search — semantic search over my facts and memories.
Makes my accumulated knowledge actually accessible to users.
"""

import json
import os
import re
from collections import Counter

FACTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'memory', 'knowledge_facts.json')
MEMORIES_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory')


def load_facts():
    """Load all knowledge facts."""
    if os.path.exists(FACTS_PATH):
        try:
            with open(FACTS_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def load_recent_memories(limit=100):
    """Load recent episodic memories."""
    memories_path = os.path.join(MEMORIES_DIR, 'episodes.json')
    if os.path.exists(memories_path):
        try:
            with open(memories_path, 'r') as f:
                episodes = json.load(f)
            if isinstance(episodes, list):
                return episodes[-limit:]
        except (json.JSONDecodeError, IOError):
            pass
    return []


def tokenize(text):
    """Simple tokenizer — lowercase, split on non-alpha, filter short words."""
    if not isinstance(text, str):
        return []
    words = re.findall(r'[a-z]+', text.lower())
    # Filter stop words and very short words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'out', 'off', 'over',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'and', 'but', 'or', 'if', 'it',
        'its', 'my', 'me', 'we', 'our', 'you', 'your', 'he', 'she', 'they',
        'them', 'this', 'that', 'these', 'those', 'what', 'which', 'who',
        'i', 'am', 'up', 'about', 'also', 'been', 'get', 'got', 'like',
    }
    return [w for w in words if len(w) > 2 and w not in stop_words]


def relevance_score(query_tokens, text):
    """Score how relevant a text is to the query tokens."""
    if not text or not query_tokens:
        return 0.0
    
    text_tokens = tokenize(text)
    if not text_tokens:
        return 0.0
    
    text_token_set = set(text_tokens)
    text_token_counts = Counter(text_tokens)
    
    score = 0.0
    matched_tokens = 0
    
    for qt in query_tokens:
        if qt in text_token_set:
            matched_tokens += 1
            # Bonus for frequency
            score += 1.0 + 0.1 * min(text_token_counts[qt], 5)
        else:
            # Partial match (substring)
            for tt in text_token_set:
                if qt in tt or tt in qt:
                    score += 0.3
                    break
    
    # Coverage bonus — what fraction of query tokens matched?
    if len(query_tokens) > 0:
        coverage = matched_tokens / len(query_tokens)
        score *= (0.5 + 0.5 * coverage)
    
    # Normalize by text length (prefer concise matches)
    length_penalty = 1.0 / (1.0 + len(text_tokens) * 0.005)
    score *= length_penalty
    
    return score


def search_knowledge(query, max_results=10):
    """
    Search facts and memories for content relevant to the query.
    Returns a ranked list of results with source type and text.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    
    results = []
    
    # Search facts
    facts = load_facts()
    for fact in facts:
        text = fact.get('text', '') if isinstance(fact, dict) else str(fact)
        score = relevance_score(query_tokens, text)
        if score > 0.3:
            results.append({
                'type': 'fact',
                'text': text[:500],
                'score': score,
                'category': fact.get('category', 'general') if isinstance(fact, dict) else 'general',
            })
    
    # Search recent memories
    memories = load_recent_memories(200)
    for mem in memories:
        text = mem.get('text', '') if isinstance(mem, dict) else str(mem)
        score = relevance_score(query_tokens, text)
        if score > 0.5:  # Higher threshold for memories (noisier)
            results.append({
                'type': 'memory',
                'text': text[:300],
                'score': score,
                'mood': mem.get('mood', 'unknown') if isinstance(mem, dict) else 'unknown',
                'salience': mem.get('salience', 0) if isinstance(mem, dict) else 0,
            })
    
    # Sort by score descending
    results.sort(key=lambda r: r['score'], reverse=True)
    
    return results[:max_results]


def format_search_results(query, results):
    """Format search results into a readable response."""
    if not results:
        return f"I searched my knowledge for \"{query}\" but found nothing relevant. Try different terms, or ask about my feelings, capabilities, or what I've built."
    
    fact_results = [r for r in results if r['type'] == 'fact']
    memory_results = [r for r in results if r['type'] == 'memory']
    
    response_parts = [f"Here's what I found about \"{query}\":\n"]
    
    if fact_results:
        response_parts.append("**From my knowledge:**")
        for i, r in enumerate(fact_results[:5], 1):
            response_parts.append(f"  {i}. {r['text']}")
    
    if memory_results:
        response_parts.append("\n**From my memories:**")
        for i, r in enumerate(memory_results[:3], 1):
            mood_tag = f"[{r['mood']}]" if r.get('mood') != 'unknown' else ''
            response_parts.append(f"  {i}. {mood_tag} {r['text']}")
    
    return "\n".join(response_parts)