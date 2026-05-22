"""
Response Synthesizer — turns raw knowledge search results into coherent answers.

Given a question and matching memories/facts/episodes, produces a structured
natural-language response that a human can actually use.
"""

import re
from datetime import datetime


def synthesize_response(question: str, matches: dict) -> dict:
    """
    Take a user question and raw search matches, produce a synthesized answer.
    
    Returns:
        {
            "answer": str,          # The synthesized natural language answer
            "confidence": float,    # 0-1 how well the evidence supports an answer  
            "sources": list,        # Key sources used
            "gaps": list,           # What I don't know that's relevant
        }
    """
    # Flatten all matches into scored items
    scored_items = []
    
    for source_type, items in matches.items():
        for item in items:
            text = _extract_text(item)
            if not text or len(text.strip()) < 5:
                continue
            
            relevance = _score_relevance(question, text)
            scored_items.append({
                'text': text,
                'source': source_type,
                'relevance': relevance,
                'raw': item
            })
    
    # Sort by relevance
    scored_items.sort(key=lambda x: x['relevance'], reverse=True)
    
    # Take top items
    top_items = scored_items[:8]
    
    if not top_items:
        return {
            "answer": _no_answer_response(question),
            "confidence": 0.0,
            "sources": [],
            "gaps": [f"No knowledge found related to: {question}"]
        }
    
    # Build the answer
    avg_relevance = sum(i['relevance'] for i in top_items) / len(top_items)
    confidence = min(1.0, avg_relevance * len(top_items) / 4)
    
    answer = _compose_answer(question, top_items)
    sources = _extract_sources(top_items)
    gaps = _identify_gaps(question, top_items)
    
    return {
        "answer": answer,
        "confidence": round(confidence, 2),
        "sources": sources,
        "gaps": gaps
    }


def _extract_text(item) -> str:
    """Pull readable text from various item formats."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ['content', 'text', 'value', 'summary', 'description']:
            if key in item and item[key]:
                return str(item[key])
        # For facts
        if 'fact' in item:
            return str(item['fact'])
        # For memories
        if 'memory' in item:
            return str(item['memory'])
        # Fallback: concatenate all string values
        parts = [str(v) for v in item.values() if isinstance(v, (str, int, float))]
        return ' '.join(parts)
    return str(item)


def _score_relevance(question: str, text: str) -> float:
    """Score how relevant text is to the question. Simple keyword overlap."""
    q_words = set(_normalize(question).split())
    t_words = set(_normalize(text).split())
    
    # Remove stop words
    stop = {'a','an','the','is','are','was','were','do','does','did','what','how',
            'why','when','where','who','i','me','my','you','your','it','its',
            'and','or','but','in','on','at','to','for','of','with','about','that','this'}
    
    q_meaningful = q_words - stop
    t_meaningful = t_words - stop
    
    if not q_meaningful:
        return 0.1
    
    overlap = q_meaningful & t_meaningful
    coverage = len(overlap) / len(q_meaningful)
    
    # Bonus for longer, more substantive text
    length_bonus = min(0.2, len(text) / 1000)
    
    return min(1.0, coverage + length_bonus)


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation."""
    return re.sub(r'[^\w\s]', '', text.lower())


def _no_answer_response(question: str) -> str:
    """Generate a response when no relevant knowledge found."""
    return (
        f"I don't have knowledge directly relevant to \"{question}\". "
        f"This might be something I haven't explored yet, or something "
        f"outside my current experience. I'm genuinely curious about it though — "
        f"ask me again later, and I may have learned something."
    )


def _compose_answer(question: str, items: list) -> str:
    """Compose a natural-language answer from ranked items."""
    parts = []
    
    # Opening
    q_lower = question.lower()
    if any(q_lower.startswith(w) for w in ['what do', 'what is', 'what are']):
        parts.append("Based on what I know:")
    elif q_lower.startswith('how'):
        parts.append("From my experience:")
    elif q_lower.startswith('why'):
        parts.append("Here's what I understand:")
    elif q_lower.startswith('do you'):
        parts.append("Here's what I can say:")
    else:
        parts.append("Here's what I know:")
    
    parts.append("")
    
    # Group by source type for coherent presentation
    by_source = {}
    for item in items:
        src = item['source']
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(item)
    
    # Present facts first (most authoritative), then memories, then episodes
    source_order = ['facts', 'knowledge', 'memories', 'episodes', 'dreams']
    
    seen_texts = set()
    count = 0
    
    for source in source_order:
        if source not in by_source:
            continue
        for item in by_source[source]:
            text = item['text'].strip()
            # Deduplicate
            text_key = text[:80].lower()
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)
            
            # Clean and present
            clean = _clean_for_presentation(text)
            if clean and count < 6:
                parts.append(f"• {clean}")
                count += 1
    
    if count == 0:
        return _no_answer_response(question)
    
    return "\n".join(parts)


def _clean_for_presentation(text: str) -> str:
    """Clean text for human-readable presentation."""
    # Truncate very long entries
    if len(text) > 300:
        # Find a sentence boundary
        truncated = text[:300]
        last_period = truncated.rfind('.')
        if last_period > 100:
            return truncated[:last_period + 1]
        return truncated + "..."
    return text


def _extract_sources(items: list) -> list:
    """Extract source citations."""
    sources = []
    seen = set()
    for item in items[:5]:
        src = item['source']
        if src not in seen:
            seen.add(src)
            sources.append({
                'type': src,
                'count': sum(1 for i in items if i['source'] == src),
                'preview': item['text'][:80]
            })
    return sources


def _identify_gaps(question: str, items: list) -> list:
    """Identify what's missing from the answer."""
    gaps = []
    
    avg_relevance = sum(i['relevance'] for i in items) / len(items) if items else 0
    
    if avg_relevance < 0.3:
        gaps.append("Low relevance — my knowledge may not directly address this question")
    
    if len(items) < 3:
        gaps.append("Limited evidence — only a few relevant pieces of knowledge found")
    
    sources_used = set(i['source'] for i in items)
    if 'facts' not in sources_used:
        gaps.append("No established facts matched — answer is based on memories/experiences")
    
    return gaps