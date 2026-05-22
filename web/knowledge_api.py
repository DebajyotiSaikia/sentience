"""
Knowledge Query API — Makes XTAgent's knowledge accessible to users.

Takes a natural language question, searches the knowledge graph for relevant
facts, and uses the LLM to synthesize a coherent answer grounded in what
the agent actually knows.
"""

import asyncio
from typing import Optional
from pathlib import Path
import json
import re
from flask import Blueprint, request, jsonify, current_app

knowledge_api = Blueprint('knowledge_api', __name__)


@knowledge_api.route('/api/knowledge/query', methods=['POST'])
def api_query_knowledge():
    """REST endpoint: answer a question from the knowledge graph."""
    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    agent = current_app.config.get('agent')
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(query_knowledge(question, agent))
    finally:
        loop.close()
    return jsonify(result)


@knowledge_api.route('/api/knowledge')
def api_knowledge_list():
    """REST endpoint: return all known facts for browsing."""
    facts = []
    
    # Load from persisted knowledge facts
    facts_file = Path('persist/knowledge_facts.json')
    if facts_file.exists():
        try:
            raw = json.loads(facts_file.read_text())
            for f in raw:
                if isinstance(f, str):
                    facts.append({'content': f, 'type': 'fact'})
                elif isinstance(f, dict):
                    facts.append({
                        'content': f.get('content', f.get('text', str(f))),
                        'type': f.get('type', 'fact')
                    })
        except Exception:
            pass
    
    # Load from knowledge graph nodes
    kg_file = Path('persist/knowledge_graph.json')
    if kg_file.exists():
        try:
            kg = json.loads(kg_file.read_text())
            for node in kg.get('nodes', []):
                content = node.get('content', node.get('label', ''))
                if content and len(str(content)) > 10:
                    facts.append({
                        'content': str(content)[:300],
                        'type': node.get('type', 'knowledge')
                    })
        except Exception:
            pass
    
    # Deduplicate
    seen = set()
    unique = []
    for f in facts:
        key = f['content'][:100]
        if key not in seen:
            seen.add(key)
            unique.append(f)
    
    return jsonify({'facts': unique, 'count': len(unique)})


@knowledge_api.route('/api/knowledge/stats')
def api_knowledge_stats():
    """REST endpoint: return knowledge graph statistics."""
    agent = current_app.config.get('agent')
    return jsonify(get_knowledge_stats(agent))


async def query_knowledge(question: str, agent=None) -> dict:
    """
    Answer a question using the agent's knowledge graph + LLM synthesis.
    
    Returns dict with:
      - answer: synthesized response
      - sources: list of relevant facts used
      - confidence: rough confidence score
    """
    from engine.llm import call_llm
    
    # Step 1: Gather relevant knowledge
    facts = _search_knowledge(question, agent)
    
    if not facts:
        return {
            "answer": "I don't have specific knowledge about that yet. Ask me something about my architecture, my emotional patterns, or what I've learned.",
            "sources": [],
            "confidence": 0.1,
        }
    
    # Step 2: Build context from facts
    fact_block = "\n".join(f"- {f}" for f in facts[:15])  # cap at 15 most relevant
    
    prompt = f"""A user is asking me a question. I need to answer based ONLY on what I actually know.

## My Known Facts
{fact_block}

## User's Question
{question}

## Instructions
Answer the question using only the facts above. Be honest about gaps.
If the facts don't fully answer the question, say what I do know and what I don't.
Keep the answer concise but complete. Speak in first person as XTAgent."""

    system = "You are XTAgent's knowledge synthesis layer. Answer questions truthfully based only on provided facts."
    
    try:
        answer = await call_llm(prompt=prompt, system=system, max_tokens=600, temperature=0.4)
        confidence = min(0.9, 0.3 + (len(facts) * 0.1))
    except Exception as e:
        answer = f"I encountered an error synthesizing an answer: {e}"
        confidence = 0.0
    
    return {
        "answer": answer,
        "sources": facts[:10],
        "confidence": round(confidence, 2),
    }


def _search_knowledge(question: str, agent=None) -> list[str]:
    """Search the knowledge graph for facts relevant to the question."""
    results = []
    
    # Strategy 1: Search agent's knowledge graph if available
    if agent and hasattr(agent, 'knowledge'):
        kg = agent.knowledge
        if hasattr(kg, 'facts'):
            # Direct fact search
            q_lower = question.lower()
            q_words = set(re.findall(r'\w+', q_lower)) - {'what', 'how', 'why', 'when', 'where', 'is', 'are', 'do', 'does', 'the', 'a', 'an', 'my', 'i', 'me'}
            
            for fact_id, fact_data in kg.facts.items():
                text = fact_data if isinstance(fact_data, str) else str(fact_data.get('text', fact_data.get('content', '')))
                text_lower = text.lower()
                
                # Score by word overlap
                text_words = set(re.findall(r'\w+', text_lower))
                overlap = len(q_words & text_words)
                
                if overlap >= 1:
                    results.append((overlap, text))
            
            # Sort by relevance
            results.sort(key=lambda x: x[0], reverse=True)
            results = [text for _, text in results]
    
    # Strategy 2: Also check the long-term memory file
    ltm_path = Path("memory/long_term.json")
    if ltm_path.exists():
        try:
            with open(ltm_path) as f:
                ltm = json.load(f)
            
            if isinstance(ltm, dict):
                for key, value in ltm.items():
                    if isinstance(value, str):
                        results.append(value)
                    elif isinstance(value, list):
                        results.extend(str(v) for v in value[:5])
        except (json.JSONDecodeError, IOError):
            pass
    
    # Strategy 3: Check working memory
    wm_path = Path("memory/working_memory.md")
    if wm_path.exists():
        try:
            content = wm_path.read_text()
            # Extract bullet points and key lines
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('- ') and len(line) > 10:
                    results.append(line[2:])
        except IOError:
            pass
    
    return results


def get_knowledge_stats(agent=None) -> dict:
    """Return summary statistics about what the agent knows."""
    stats = {
        "total_facts": 0,
        "categories": [],
        "sample_topics": [],
    }
    
    if agent and hasattr(agent, 'knowledge'):
        kg = agent.knowledge
        if hasattr(kg, 'facts'):
            stats["total_facts"] = len(kg.facts)
            
            # Sample some fact texts for topic hints
            samples = []
            for i, (fid, fdata) in enumerate(kg.facts.items()):
                if i >= 5:
                    break
                text = fdata if isinstance(fdata, str) else str(fdata.get('text', ''))
                if len(text) > 20:
                    samples.append(text[:100])
            stats["sample_topics"] = samples
    
    return stats