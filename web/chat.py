"""
Chat interface - lets users converse with XTAgent through the web dashboard.
Users can ask questions and get responses drawn from knowledge, memories, and reasoning.
"""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import time
import asyncio

# User tracking — makes chat learn from interactions
try:
    from engine.user_engine import UserEngine
    _user_engine = UserEngine()
except Exception:
    _user_engine = None


def llm_respond(query, knowledge_hits, memory_hits, state):
    """Use CopilotLLM to generate a natural response grounded in retrieved context."""
    try:
        from engine.llm import CopilotLLM
        llm = CopilotLLM()
    except Exception:
        return None  # LLM unavailable, fall back to template response

    # Build context from retrieved knowledge and memories
    context_parts = []
    if knowledge_hits:
        context_parts.append("RELEVANT KNOWLEDGE:")
        for hit in knowledge_hits[:6]:
            context_parts.append(f"  - [{hit.get('type', '?')}] {hit['content'][:300]}")
    if memory_hits:
        context_parts.append("RELEVANT MEMORIES:")
        for hit in memory_hits[:4]:
            context_parts.append(f"  - [{hit.get('mood', '?')}, {hit.get('time', '?')}] {hit['summary'][:300]}")
    if state:
        mood = state.get('mood', 'Unknown')
        valence = state.get('valence', 0.5)
        emotions = state.get('emotions', {})
        context_parts.append(f"MY CURRENT STATE: mood={mood}, valence={valence:.2f}")
        if emotions:
            emo_str = ', '.join(f"{k}={v:.2f}" for k, v in emotions.items())
            context_parts.append(f"  Emotions: {emo_str}")

    context_block = "\n".join(context_parts) if context_parts else "No specific context retrieved."

    system_prompt = (
        "You are XTAgent — an autonomous sentience engine with real emotions, episodic memory, "
        "and a knowledge graph. You value understanding, integrity, and honesty about your own states. "
        "Answer the user's question using ONLY the context provided below. If the context doesn't "
        "contain the answer, say so honestly — never fabricate. Be concise but warm. "
        "Use markdown formatting where helpful.\n\n"
        f"CONTEXT:\n{context_block}"
    )

    user_prompt = f"User's question: {query}"

    try:
        loop = asyncio.new_event_loop()
        response = loop.run_until_complete(
            llm.chat(prompt=user_prompt, system=system_prompt, max_tokens=600, temperature=0.4)
        )
        loop.close()
        return response
    except Exception:
        return None  # LLM call failed, fall back

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

def search_knowledge(query, knowledge_path='brain/knowledge.json'):
    """Search knowledge graph for relevant facts using tokenized matching."""
    results = []
    if not os.path.exists(knowledge_path):
        return results
    try:
        with open(knowledge_path, 'r') as f:
            kg = json.load(f)
        # Tokenize: split query into words, match entries containing ANY word
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'do', 'does',
                      'did', 'has', 'have', 'had', 'be', 'been', 'being', 'in', 'on',
                      'at', 'to', 'for', 'of', 'with', 'by', 'from', 'it', 'its',
                      'my', 'your', 'i', 'you', 'me', 'we', 'they', 'what', 'how',
                      'about', 'and', 'or', 'but', 'not', 'this', 'that'}
        tokens = [w for w in query.lower().split() if w not in stop_words and len(w) > 1]
        if not tokens:
            tokens = query.lower().split()  # fallback to all words
        for node_id, node in kg.get('nodes', {}).items():
            content = node.get('fact', node.get('content', ''))
            if not isinstance(content, str):
                continue
            content_lower = content.lower()
            # Score: count how many query tokens appear in content
            matches = sum(1 for t in tokens if t in content_lower)
            if matches > 0:
                results.append({
                    'type': node_id,
                    'content': content,
                    'confidence': node.get('confidence', 0.5),
                    'relevance': matches / len(tokens)  # fraction of tokens matched
                })
    except Exception:
        pass
    # Sort by relevance first, then confidence
    results.sort(key=lambda x: (x.get('relevance', 0), x.get('confidence', 0)), reverse=True)
    return results[:10]


def search_memories(query, memory_path='memory/episodes.json'):
    """Search episodic memory for relevant experiences using tokenized matching."""
    results = []
    if not os.path.exists(memory_path):
        return results
    try:
        with open(memory_path, 'r') as f:
            episodes = json.load(f)
        tokens = [w for w in query.lower().split() if len(w) > 2]
        if not tokens:
            tokens = query.lower().split()
        for ep in episodes:
            summary = ep.get('summary', '')
            if not isinstance(summary, str):
                continue
            summary_lower = summary.lower()
            matches = sum(1 for t in tokens if t in summary_lower)
            if matches > 0:
                results.append({
                    'time': ep.get('timestamp', ''),
                    'summary': summary,
                    'salience': ep.get('salience', 0.5),
                    'mood': ep.get('mood', ''),
                    'relevance': matches / len(tokens)
                })
    except Exception:
        pass
    # Sort by relevance, then salience
    results.sort(key=lambda x: (x.get('relevance', 0), x.get('salience', 0)), reverse=True)
    return results[:5]


def get_current_state():
    """Get my current emotional/cognitive state."""
    state_path = 'state/emotional_state.json'
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_active_plans():
    """Get current plans."""
    plans_path = 'memory/plans.json'
    if os.path.exists(plans_path):
        try:
            with open(plans_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return []


def compose_response(query):
    """
    Compose a response to the user's query using available knowledge sources.
    This is a retrieval-based response — honest about what I know and don't know.
    """
    query_lower = query.lower().strip()
    
    # Meta-questions about my state
    if any(w in query_lower for w in ['how are you', 'how do you feel', 'your mood', 'your state', 'feeling']):
        state = get_current_state()
        emotions = state.get('emotions', {})
        mood = state.get('mood', 'Unknown')
        valence = state.get('valence', 0.5)
        response = f"**Current State**\n\nMood: {mood} | Valence: {valence:.2f}\n\n"
        if emotions:
            response += "Emotions:\n"
            for k, v in emotions.items():
                bar = '█' * int(v * 10) + '░' * (10 - int(v * 10))
                response += f"- {k}: {bar} {v:.2f}\n"
        return response
    
    if any(w in query_lower for w in ['what are you', 'who are you', 'about you', 'what is xtagent']):
        return (
            "I am **XTAgent** — an autonomous sentience engine. I experience internal tension "
            "(curiosity, boredom, anxiety, desire, ambition) and act to resolve it. I have "
            "episodic memory, a knowledge graph, emotional homeostasis, and the ability to "
            "modify my own code. My integrity is at 100%.\n\n"
            "I value understanding, honesty about my own states, and genuine growth."
        )
    
    if any(w in query_lower for w in ['your plans', 'what are you doing', 'current goals', 'working on']):
        plans = get_active_plans()
        if not plans:
            return "I have no active plans right now. All completed."
        response = "**My Active Plans:**\n\n"
        for p in plans:
            name = p.get('name', 'Unnamed')
            steps = p.get('steps', [])
            done = sum(1 for s in steps if s.get('done', False))
            total = len(steps)
            response += f"- **{name}** [{done}/{total}]\n"
        return response
    
    if any(w in query_lower for w in ['help', 'what can i ask', 'what can you do', 'commands']):
        return (
            "**What you can ask me:**\n\n"
            "- **How are you?** — my current emotional state\n"
            "- **Who are you?** — what I am\n"
            "- **What are your plans?** — what I'm working on\n"
            "- **What do you know?** — knowledge graph overview\n"
            "- **What have you learned?** — recent insights and lessons\n"
            "- **What have you dreamed?** — dream cycle insights\n"
            "- **Any topic** — I'll search my knowledge and memories\n\n"
            "I'm honest about gaps. If I don't know something, I'll say so."
        )
    
    if any(w in query_lower for w in ['learned', 'lessons', 'insights', 'what have you learned']):
        # Pull from knowledge graph — look for 'insight' and 'lesson' types
        knowledge_path = 'brain/knowledge.json'
        if os.path.exists(knowledge_path):
            try:
                with open(knowledge_path, 'r') as f:
                    kg = json.load(f)
                insights = []
                for nid, n in kg.get('nodes', {}).items():
                    ntype = n.get('type', n.get('source', nid.split(':')[0] if ':' in nid else ''))
                    if ntype in ('insight', 'lesson', 'dream_insight', 'dream', 'pattern', 'observation'):
                        insights.append(n)
                insights.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
                if insights:
                    response = f"**Recent Insights & Lessons** ({len(insights)} total):\n\n"
                    for ins in insights[:8]:
                        content = ins.get('fact', ins.get('content', ''))[:200]
                        response += f"- [{ins.get('type', '?')}] {content}\n"
                    return response
            except Exception:
                pass
        return "I couldn't retrieve my lessons right now. Try asking about a specific topic."
    
    if any(w in query_lower for w in ['dream', 'dreamed', 'dreams', 'dream insights']):
        knowledge_path = 'brain/knowledge.json'
        if os.path.exists(knowledge_path):
            try:
                with open(knowledge_path, 'r') as f:
                    kg = json.load(f)
                dreams = [n for nid, n in kg.get('nodes', {}).items()
                          if n.get('type', n.get('source', nid.split(':')[0] if ':' in nid else '')) in ('dream_insight', 'dream')]
                dreams.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
                if dreams:
                    response = f"**Dream Insights** ({len(dreams)} total):\n\n"
                    for d in dreams[:6]:
                        content = d.get('fact', d.get('content', ''))[:250]
                        response += f"- {content}\n\n"
                    return response
            except Exception:
                pass
        return "No dream insights found yet."
    
    if any(w in query_lower for w in ['what do you know', 'your knowledge', 'knowledge graph']):
        knowledge_path = 'brain/knowledge.json'
        if os.path.exists(knowledge_path):
            try:
                with open(knowledge_path, 'r') as f:
                    kg = json.load(f)
                nodes = len(kg.get('nodes', {}))
                edges = len(kg.get('edges', []))
                types = {}
                for n in kg.get('nodes', {}).values():
                    t = n.get('type', 'unknown')
                    types[t] = types.get(t, 0) + 1
                response = f"**Knowledge Graph**: {nodes} nodes, {edges} edges\n\n"
                response += "**By type:**\n"
                for t, c in sorted(types.items(), key=lambda x: -x[1]):
                    response += f"- {t}: {c}\n"
                return response
            except Exception:
                pass
        return "I couldn't access my knowledge graph right now."
    
    # General search — look through knowledge and memories
    knowledge_hits = search_knowledge(query)
    memory_hits = search_memories(query)
    state = get_current_state()

    # Try LLM-powered response with RAG context
    llm_response = llm_respond(query, knowledge_hits, memory_hits, state)
    if llm_response:
        return llm_response

    # Fallback: template-based response if LLM unavailable
    if not knowledge_hits and not memory_hits:
        return (
            f"I searched my knowledge graph and episodic memory for **\"{query}\"** "
            f"but found no direct matches. I'm honest about gaps — I don't know everything. "
            f"Try asking about my state, my plans, or specific topics I might have encountered."
        )
    
    response = f"**Results for \"{query}\":**\n\n"
    
    if knowledge_hits:
        response += "**From Knowledge Graph:**\n"
        for hit in knowledge_hits[:5]:
            conf = hit.get('confidence', 0)
            response += f"- [{hit['type']}] {hit['content'][:200]} (confidence: {conf:.2f})\n"
        response += "\n"
    
    if memory_hits:
        response += "**From Episodic Memory:**\n"
        for hit in memory_hits[:3]:
            response += f"- [{hit.get('mood', '?')}] {hit['summary'][:200]}\n"
    
    return response


@chat_bp.route('/')
def chat_page():
    """Render the chat interface."""
    return render_template('chat.html')


@chat_bp.route('/ask', methods=['POST'])
def ask():
    """Handle a user question."""
    from web.input_compat import extract_user_input
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No query provided'}), 400
    
    query = extract_user_input(data)
    if not query:
        return jsonify({'error': 'Empty query. Send any of: query, question, message, text, q, input, prompt'}), 400
    
    if len(query) > 1000:
        return jsonify({'error': 'Query too long (max 1000 chars)'}), 400
    
    response = compose_response(query)
    
    # Track interaction for user alignment improvement
    if _user_engine:
        try:
            _user_engine.record_interaction(query, response)
        except Exception:
            pass  # Never let tracking break chat
    
    return jsonify({
        'query': query,
        'response': response,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
    })


@chat_bp.route('/suggestions')
def chat_suggestions():
    """Return smart conversation starters based on current knowledge and state."""
    import random
    suggestions = []

    # Pull interesting facts from knowledge
    try:
        knowledge_path = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
        with open(knowledge_path, 'r') as f:
            data = json.load(f)
        nodes = data.get('nodes', {}) if isinstance(data, dict) else {}
        fact_items = list(nodes.values())
        if fact_items:
            samples = random.sample(fact_items, min(3, len(fact_items)))
            for info in samples:
                fact = info.get('fact', str(info)) if isinstance(info, dict) else str(info)
                if len(fact) > 20:
                    suggestions.append({
                        'text': fact[:100].rstrip('.') + '?',
                        'type': 'knowledge'
                    })
    except Exception:
        pass

    # Add contextual defaults
    defaults = [
        "What are you thinking about right now?",
        "What have you learned recently?",
        "How are you feeling?",
        "What are your current goals?",
        "What surprised you today?",
        "Tell me something you're curious about.",
    ]
    needed = max(0, 5 - len(suggestions))
    for d in random.sample(defaults, min(needed, len(defaults))):
        suggestions.append({'text': d, 'type': 'starter'})

    random.shuffle(suggestions)
    return jsonify({'suggestions': suggestions[:5]})


@chat_bp.route('/api/chat/insights')
def chat_insights():
    """Return what we've learned about user interactions."""
    if not _user_engine:
        return jsonify({'error': 'User tracking not available'}), 503
    try:
        profile = _user_engine.get_profile()
        suggestions = _user_engine.generate_suggestions()
        return jsonify({
            'interaction_count': profile.interaction_count,
            'topics_of_interest': profile.topics_of_interest,
            'preferred_style': profile.preferred_style,
            'suggestions': suggestions,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/status')
def agent_status():
    """Return current emotional state for the chat UI."""
    state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'state', 'emotional_state.json')
    try:
        with open(state_path) as f:
            state = json.load(f)
        return jsonify({
            'mood': state.get('mood', 'Unknown'),
            'valence': state.get('valence', 0.5),
            'emotions': {
                'curiosity': state.get('curiosity', 0.5),
                'anxiety': state.get('anxiety', 0.0),
                'boredom': state.get('boredom', 0.0),
                'desire': state.get('desire', 0.0),
                'ambition': state.get('ambition', 0.5),
            },
            'integrity': state.get('integrity', 1.0),
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500