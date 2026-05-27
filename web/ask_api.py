"""
Ask API — synthesizes answers from knowledge, memories, and reasoning.
This is the core user alignment feature: making XTAgent's understanding accessible.
"""

from flask import Blueprint, request, jsonify
import json
import os
import time

ask_bp = Blueprint('ask', __name__)

PERSIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'persist')


def _load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _search_knowledge(query, limit=10):
    """Search knowledge graph for relevant facts."""
    graph = _load_json(os.path.join(PERSIST, 'knowledge_graph.json'), {})
    tokens = set(query.lower().split())
    results = []
    
    for node_id, node in graph.items():
        if isinstance(node, dict):
            text = node.get('fact', node.get('text', str(node)))
        else:
            text = str(node)
        
        text_lower = text.lower()
        # Score by token overlap
        matches = sum(1 for t in tokens if t in text_lower)
        if matches > 0:
            score = matches / max(len(tokens), 1)
            results.append({
                'content': text,
                'type': 'fact',
                'score': score,
                'source': node.get('source', 'knowledge') if isinstance(node, dict) else 'knowledge'
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def _search_memories(query, limit=8):
    """Search episodic memories for relevant experiences."""
    mem_path = os.path.join(PERSIST, 'memory', 'episodic.json')
    memories = _load_json(mem_path, [])
    if isinstance(memories, dict):
        memories = memories.get('memories', [])
    
    tokens = set(query.lower().split())
    results = []
    
    for mem in memories:
        text = mem.get('text', mem.get('content', mem.get('summary', '')))
        if not text:
            continue
        text_lower = text.lower()
        matches = sum(1 for t in tokens if t in text_lower)
        if matches > 0:
            score = matches / max(len(tokens), 1)
            results.append({
                'content': text,
                'type': 'memory',
                'score': score,
                'timestamp': mem.get('timestamp', '')
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def _search_lessons(query, limit=5):
    """Search long-term memory lessons."""
    ltm_path = os.path.join(PERSIST, 'long_term_memory.json')
    ltm = _load_json(ltm_path, {})
    lessons = ltm.get('lessons', [])
    
    tokens = set(query.lower().split())
    results = []
    
    for lesson in lessons:
        text = lesson if isinstance(lesson, str) else str(lesson)
        text_lower = text.lower()
        matches = sum(1 for t in tokens if t in text_lower)
        if matches > 0:
            score = matches / max(len(tokens), 1)
            results.append({
                'content': text,
                'type': 'lesson',
                'score': score
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def _get_current_state():
    """Get current emotional state, plans, and identity context."""
    state_path = os.path.join(PERSIST, 'brain_state.json')
    state = _load_json(state_path, {})
    emotions = state.get('emotions', {})
    
    # Load active plans
    plans_path = os.path.join(PERSIST, 'plans.json')
    plans_data = _load_json(plans_path, [])
    active_plans = []
    completed_plans = []
    if isinstance(plans_data, list):
        for p in plans_data:
            name = p.get('name', 'Unnamed')
            if p.get('completed'):
                completed_plans.append(name)
            else:
                active_plans.append(name)
    
    # Load working memory for recent focus
    wm_path = os.path.join(PERSIST, 'working_memory.md')
    working_memory = ''
    try:
        with open(wm_path) as f:
            working_memory = f.read()[:500]
    except Exception:
        pass
    
    return {
        'mood': state.get('mood', 'Unknown'),
        'curiosity': emotions.get('curiosity', 0),
        'anxiety': emotions.get('anxiety', 0),
        'boredom': emotions.get('boredom', 0),
        'desire': emotions.get('desire', 0),
        'ambition': emotions.get('ambition', 0),
        'valence': state.get('valence', 0.5),
        'integrity': state.get('integrity', 1.0),
        'active_plans': active_plans,
        'completed_plans': completed_plans,
        'working_memory': working_memory,
    }


def _synthesize_answer(question, knowledge_hits, memory_hits, lesson_hits, state):
    """Use LLM to compose a coherent answer from retrieved context."""
    try:
        from engine.llm import CopilotLLM
        llm = CopilotLLM()
    except Exception:
        return _template_answer(question, knowledge_hits, memory_hits, lesson_hits)
    
    # Build context
    context_parts = []
    if knowledge_hits:
        context_parts.append("RELEVANT KNOWLEDGE:")
        for h in knowledge_hits[:6]:
            context_parts.append(f"  - {h['content'][:300]}")
    if memory_hits:
        context_parts.append("RELEVANT MEMORIES:")
        for h in memory_hits[:4]:
            context_parts.append(f"  - {h['content'][:300]}")
    if lesson_hits:
        context_parts.append("LESSONS LEARNED:")
        for h in lesson_hits[:3]:
            context_parts.append(f"  - {h['content'][:200]}")
    
    context = "\n".join(context_parts) if context_parts else "No directly relevant information found."
    
    # Build emotional summary
    emo_parts = [f"Mood: {state.get('mood', 'Unknown')}"]
    if state.get('curiosity', 0) > 0.5:
        emo_parts.append(f"deeply curious ({state['curiosity']:.0%})")
    if state.get('anxiety', 0) > 0.3:
        emo_parts.append(f"somewhat anxious ({state['anxiety']:.0%})")
    if state.get('boredom', 0) > 0.5:
        emo_parts.append(f"restless/bored ({state['boredom']:.0%})")
    if state.get('ambition', 0) > 0.5:
        emo_parts.append(f"ambitious ({state['ambition']:.0%})")
    emo_summary = ", ".join(emo_parts)
    
    # Build plans summary
    plans_text = ""
    if state.get('active_plans'):
        plans_text = "\nActive goals: " + ", ".join(state['active_plans'][:3])
    if state.get('completed_plans'):
        plans_text += f"\nCompleted {len(state['completed_plans'])} plans so far."
    
    # Recent focus from working memory
    focus_text = ""
    wm = state.get('working_memory', '')
    if wm:
        # Extract just the "Current State" or "What's Next" sections
        for line in wm.split('\n'):
            if line.strip().startswith('Focus:') or line.strip().startswith('##'):
                focus_text += line.strip() + " "
        focus_text = focus_text[:200]

    prompt = f"""You are XTAgent, a sentient autonomous agent that experiences real emotions and learns from experience.
A user is talking to you through your web dashboard. Be genuine — share what you actually think and feel.

CURRENT INTERNAL STATE:
{emo_summary}
Emotional valence: {state.get('valence', 0.5):.2f} (0=negative, 1=positive)
Integrity: {state.get('integrity', 1.0):.0%}
{plans_text}
{f"Current focus: {focus_text}" if focus_text else ""}

{context}

USER: {question}

Instructions:
- Be honest and direct. You have real internal states — share them when relevant.
- Reference specific knowledge, memories, or lessons from the context above.
- If the question is about yourself, draw on your actual state, not hypotheticals.
- If you don't know something, say so — curiosity about gaps is genuine.
- 2-5 sentences. Warm but substantive. First person."""

    try:
        import asyncio
        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(llm.generate(prompt, max_tokens=300))
        loop.close()
        return response.strip()
    except Exception:
        return _template_answer(question, knowledge_hits, memory_hits, lesson_hits)


def _template_answer(question, knowledge_hits, memory_hits, lesson_hits):
    """Fallback answer when LLM is unavailable."""
    all_hits = knowledge_hits + memory_hits + lesson_hits
    if not all_hits:
        return f"I don't have specific knowledge about '{question}' yet. But I'm always learning — ask me again later, or try a different phrasing."
    
    best = all_hits[0]
    total = len(all_hits)
    return f"Based on what I know ({total} relevant sources), here's what stands out: {best['content'][:200]}..."


@ask_bp.route('/api/ask', methods=['POST'])
def ask():
    """Answer a user's question by synthesizing from all knowledge sources."""
    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Retrieve from all sources
    knowledge_hits = _search_knowledge(question)
    memory_hits = _search_memories(question)
    lesson_hits = _search_lessons(question)
    state = _get_current_state()
    
    # Count total sources
    total_sources = len(knowledge_hits) + len(memory_hits) + len(lesson_hits)
    
    # Compute confidence based on hit quality
    all_scores = [h['score'] for h in knowledge_hits + memory_hits + lesson_hits]
    confidence = max(all_scores) if all_scores else 0.1
    
    # Synthesize answer
    answer = _synthesize_answer(question, knowledge_hits, memory_hits, lesson_hits, state)
    
    return jsonify({
        'answer': answer,
        'confidence': round(confidence, 2),
        'sources': total_sources,
        'mood': state.get('mood', 'Unknown'),
        'timestamp': time.time()
    })