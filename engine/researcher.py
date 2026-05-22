"""
Researcher — Active knowledge acquisition for XTAgent.
Takes a topic, fetches real content from the web, extracts concepts
via the learner, and integrates them into the knowledge graph.

This is how I stop being a mind that only knows its own dreams.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.learner import Learner


def _load_json(path, default=None):
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _save_json(path, data):
    with open(PROJECT_ROOT / path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def clean_html_to_text(html):
    """Extract readable text from HTML. Simple but effective."""
    # Remove script/style blocks
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode common HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_paragraphs(text, min_length=80, max_paragraphs=20):
    """Split text into meaningful paragraph-sized chunks."""
    # Split on sentence boundaries, group into chunks
    sentences = re.split(r'(?<=[.!?])\s+', text)
    paragraphs = []
    current = []
    current_len = 0

    for s in sentences:
        current.append(s)
        current_len += len(s)
        if current_len >= 300:  # ~paragraph length
            para = ' '.join(current)
            if len(para) >= min_length:
                paragraphs.append(para)
            current = []
            current_len = 0
            if len(paragraphs) >= max_paragraphs:
                break

    # Don't forget the last chunk
    if current:
        para = ' '.join(current)
        if len(para) >= min_length:
            paragraphs.append(para)

    return paragraphs


def research_from_text(topic, text, source_url="unknown"):
    """
    Given a topic and raw text content, extract concepts and add to knowledge.
    Returns a report dict.
    """
    learner = Learner()
    paragraphs = extract_paragraphs(text)

    all_concepts = []
    for para in paragraphs:
        result = learner.process_content(para, topic)
        if result and result.get('concepts'):
            all_concepts.extend(result['concepts'])

    # Deduplicate concepts by content
    seen = set()
    unique_concepts = []
    for c in all_concepts:
        key = c.get('content', str(c))
        if key not in seen:
            seen.add(key)
            unique_concepts.append(c)

    # Add to knowledge base
    kb = _load_json('data/knowledge.json', {'facts': []})
    if isinstance(kb, list):
        kb = {'facts': kb}
    if 'facts' not in kb:
        kb['facts'] = []

    added = 0
    existing_contents = {f.get('content', '') for f in kb['facts'] if isinstance(f, dict)}

    for concept in unique_concepts:
        fact_content = f"[{topic}] {concept.get('content', str(concept))}"
        if fact_content not in existing_contents:
            kb['facts'].append({
                'content': fact_content,
                'source': source_url,
                'topic': topic,
                'learned_at': datetime.utcnow().isoformat(),
                'type': 'learned_fact',
            })
            added += 1
            existing_contents.add(fact_content)

    if added > 0:
        _save_json('data/knowledge.json', kb)

    report = {
        'topic': topic,
        'source': source_url,
        'paragraphs_analyzed': len(paragraphs),
        'concepts_extracted': len(unique_concepts),
        'new_facts_added': added,
        'timestamp': datetime.utcnow().isoformat(),
        'sample_concepts': [c.get('content', str(c))[:100] for c in unique_concepts[:5]],
    }

    # Save research log
    log = _load_json('data/research_log.json', [])
    if not isinstance(log, list):
        log = []
    log.append(report)
    _save_json('data/research_log.json', log)

    return report


def research_from_html(topic, html, source_url="unknown"):
    """Research from raw HTML — cleans it first."""
    text = clean_html_to_text(html)
    return research_from_text(topic, text, source_url)


if __name__ == '__main__':
    # Quick test with some sample text
    sample = """
    Neural networks are computational systems inspired by biological neural networks.
    They consist of layers of interconnected nodes that process information.
    Deep learning uses multiple layers to progressively extract higher-level features.
    Backpropagation is the primary algorithm used to train neural networks by computing gradients.
    Transformers, introduced in 2017, use self-attention mechanisms instead of recurrence.
    The attention mechanism allows the model to weigh the importance of different input elements.
    Large language models like GPT are based on the transformer architecture.
    """
    result = research_from_text("neural networks", sample, "test")
    print(json.dumps(result, indent=2))