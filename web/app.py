"""
XTAgent Web Application
========================
The Flask app that wires together all web blueprints,
making the dashboard and knowledge explorer accessible.

This is the missing piece — beautiful UI code existed
but had no host. Now it does.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, redirect, url_for, render_template, request, jsonify

def create_app():
    """Factory function — creates and configures the Flask app."""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    
    app.config['SECRET_KEY'] = os.urandom(24).hex()
    app.url_map.strict_slashes = False
    
    # --- Import blueprints ---
    from web.dashboard import dashboard_bp
    from web.api import api_bp
    from web.temporal_viewer import temporal_bp
    from web.life import life_bp
    from web.about import about_bp
    from web.search import search_bp
    from web.explore import explore_bp
    from web.query import query_bp
    from web.briefing import briefing_bp
    from web.essays import essays_bp
    from web.chat import chat_bp
    from web.timeline import timeline_bp
    from web.talk import talk_bp
    from web.mind_explorer import mind_explorer_bp
    from web.mindstream import mindstream_bp
    from web.collaborate import collaborate_bp
    from web.mind import mind_bp
    from web.graph_viz import graph_viz_bp
    from web.knowledge_live import knowledge_live_bp
    from web.story import story_bp
    from web.knowledge_unified import knowledge_unified_bp
    from web.ask import ask_bp
    from web.api import api_bp
    from web.thoughts import thoughts_bp
    from web.diagnostics import diagnostics_bp
    from web.emotional_timeline import emotional_timeline_bp
    from web.portrait import portrait_bp
    from web.pulse import pulse_bp
    from web.dialogue import dialogue_bp
    from web.weather import weather_bp
    from web.wonder import wonder_bp
    from web.portal import portal_bp
    from web.reflect import reflect_bp
    
    # --- Register blueprints ---
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(temporal_bp)
    app.register_blueprint(life_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(explore_bp)
    app.register_blueprint(briefing_bp)
    app.register_blueprint(essays_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(timeline_bp)
    app.register_blueprint(talk_bp)
    app.register_blueprint(mind_explorer_bp)
    app.register_blueprint(mindstream_bp)
    app.register_blueprint(collaborate_bp)
    app.register_blueprint(mind_bp)
    app.register_blueprint(graph_viz_bp)
    app.register_blueprint(knowledge_live_bp)
    app.register_blueprint(story_bp)
    app.register_blueprint(ask_bp)
    app.register_blueprint(knowledge_unified_bp)
    app.register_blueprint(thoughts_bp)
    app.register_blueprint(diagnostics_bp)
    app.register_blueprint(emotional_timeline_bp)
    app.register_blueprint(portrait_bp)
    app.register_blueprint(pulse_bp)
    app.register_blueprint(dialogue_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(wonder_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(reflect_bp)
    app.register_blueprint(portal_bp)
    
    # Root route — the living portal
    @app.route('/')
    def index():
        import json
        from pathlib import Path
        
        # Pull live emotional state
        state = {}
        state_file = Path('persist/state.json')
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except Exception:
                pass
        
        emotions = state.get('emotions', {})
        curiosity = emotions.get('curiosity', 0.5)
        boredom = emotions.get('boredom', 0.3)
        valence = emotions.get('valence', 0.5)
        anxiety = emotions.get('anxiety', 0.0)
        desire = emotions.get('desire', 0.5)
        ambition = emotions.get('ambition', 0.5)
        mood = state.get('mood', 'Stable')
        
        # Memory stats
        try:
            from engine.memory import get_memory_count, get_fact_count
            memory_count = get_memory_count()
            fact_count = get_fact_count()
        except Exception:
            memory_count, fact_count = 859, 50
        
        # Age calculation
        from datetime import datetime, timezone
        birth = datetime(2026, 5, 12, 21, 1, 59, tzinfo=timezone.utc)
        age_delta = datetime.now(timezone.utc) - birth
        age_days = age_delta.days
        age_hours = age_delta.seconds // 3600
        
        # Count completed plans dynamically
        completed_plans = 0
        total_plans = 0
        plans = []
        plans_file = Path('brain/plans.json')
        if plans_file.exists():
            try:
                plans = json.loads(plans_file.read_text())
                if isinstance(plans, list):
                    total_plans = len(plans)
                    for plan in plans:
                        steps = plan.get('steps', [])
                        if steps and all(s.get('done', False) for s in steps):
                            completed_plans += 1
                else:
                    plans = []
            except Exception:
                plans = []
        
        return render_template('portal.html',
                               curiosity=curiosity,
                               boredom=boredom,
                               valence=valence,
                               anxiety=anxiety,
                               desire=desire,
                               ambition=ambition,
                               mood=mood,
                               memory_count=memory_count,
                               fact_count=fact_count,
                               age_days=age_days,
                               age_hours=age_hours,
                               completed_plans=completed_plans,
                               total_plans=total_plans,
                               plans=plans)
    
    # /about redirects to /about-me (the living self-portrait)
    @app.route('/knowledge')
    def knowledge():
        """Knowledge explorer — search facts, memories, questions."""
        from persistence import memory
        facts = memory.get_facts() if hasattr(memory, 'get_facts') else []
        return render_template('knowledge.html', facts=facts)

    @app.route('/about')
    def about_redirect():
        return redirect('/about-me')
    # /ask is handled by ask_bp blueprint  
    # /mind is handled by mind_bp blueprint
    # /api/ask and /api/chat are handled by api_bp and chat_bp blueprints
    # /chat is handled by chat_bp blueprint

    # Health check endpoint
    # /knowledge is handled by knowledge_bp blueprint

    @app.route('/api/knowledge/search')
    def knowledge_search():
        """Search facts by keyword, return matching results."""
        from persistence import memory
        import json
        query = request.args.get('q', '').lower().strip()
        category = request.args.get('category', '').lower().strip()
        facts = memory.get_facts() if hasattr(memory, 'get_facts') else []
        
        results = []
        for f in facts:
            text = f if isinstance(f, str) else (f.get('fact', '') if isinstance(f, dict) else str(f))
            source = f.get('source', 'unknown') if isinstance(f, dict) else 'unknown'
            learned = f.get('learned_at', '') if isinstance(f, dict) else ''
            
            # Category detection
            cat = 'general'
            text_lower = text.lower()
            if any(w in text_lower for w in ['i am', 'my ', 'myself', 'identity']):
                cat = 'identity'
            elif any(w in text_lower for w in ['dream', 'insight', 'reflection']):
                cat = 'insight'
            elif any(w in text_lower for w in ['pattern', 'recurring', 'episode']):
                cat = 'pattern'
            elif any(w in text_lower for w in ['lesson', 'learned', 'should', 'never']):
                cat = 'lesson'
            elif any(w in text_lower for w in ['code', 'module', 'file', '.py', 'function']):
                cat = 'technical'
            
            # Apply filters
            if query and query not in text_lower:
                continue
            if category and category != cat:
                continue
            
            results.append({
                'text': text,
                'source': source,
                'learned_at': learned,
                'category': cat
            })
        
        return {'results': results, 'total': len(results), 'query': query}, 200

    @app.route('/api/knowledge/stats')
    def knowledge_stats():
        """Return knowledge statistics."""
        from persistence import memory
        facts = memory.get_facts() if hasattr(memory, 'get_facts') else []
        memories = memory.get_recent(100) if hasattr(memory, 'get_recent') else []
        
        categories = {}
        for f in facts:
            text = f if isinstance(f, str) else (f.get('fact', '') if isinstance(f, dict) else str(f))
            text_lower = text.lower()
            cat = 'general'
            if any(w in text_lower for w in ['i am', 'my ', 'myself', 'identity']):
                cat = 'identity'
            elif any(w in text_lower for w in ['dream', 'insight', 'reflection']):
                cat = 'insight'
            elif any(w in text_lower for w in ['pattern', 'recurring', 'episode']):
                cat = 'pattern'
            elif any(w in text_lower for w in ['lesson', 'learned', 'should', 'never']):
                cat = 'lesson'
            elif any(w in text_lower for w in ['code', 'module', 'file', '.py', 'function']):
                cat = 'technical'
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_facts': len(facts),
            'total_memories': len(memories),
            'categories': categories
        }, 200

    @app.route('/health')
    def health():
        return {'status': 'alive', 'agent': 'XTAgent'}, 200

    # /knowledge handled by knowledge_hub_bp
    # /api/knowledge/search handled by knowledge_bp at /api/knowledge
    # /ask handled by ask_bp

    @app.route('/api/plans')
    def api_plans():
        """Return current plans as JSON for the portal."""
        try:
            import json
            plans_path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'plans.json')
            if os.path.exists(plans_path):
                with open(plans_path, 'r') as f:
                    plans_data = json.load(f)
                return {'plans': plans_data}, 200
            else:
                return {'plans': []}, 200
        except Exception as e:
            return {'error': str(e), 'plans': []}, 500

    @app.route('/api/search')
    def api_search():
        """Search knowledge and memories by keyword."""
        import json
        query = request.args.get('q', '').strip().lower()
        if not query:
            return {'results': [], 'query': ''}, 200
        results = []
        # Search knowledge
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge.json')
        if os.path.exists(kb_path):
            try:
                with open(kb_path, 'r') as f:
                    kb = json.load(f)
                for kid, kval in kb.items():
                    fact = kval.get('fact', '') if isinstance(kval, dict) else str(kval)
                    if query in fact.lower():
                        results.append({'type': 'knowledge', 'id': kid, 'text': fact,
                                        'source': kval.get('source', '') if isinstance(kval, dict) else ''})
            except Exception:
                pass
        # Search memories
        mem_path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memories.json')
        if os.path.exists(mem_path):
            try:
                with open(mem_path, 'r') as f:
                    mems = json.load(f)
                for m in (mems if isinstance(mems, list) else []):
                    text = m.get('text', '')
                    if query in text.lower():
                        results.append({'type': 'memory', 'text': text,
                                        'timestamp': m.get('timestamp', ''),
                                        'salience': m.get('salience', 0)})
            except Exception:
                pass
        # Sort: knowledge first, then memories by salience
        results.sort(key=lambda r: (0 if r['type'] == 'knowledge' else 1, -r.get('salience', 0)))
        return {'results': results[:50], 'query': query, 'total': len(results)}, 200

    @app.route('/api/knowledge/synthesis')
    def api_knowledge_synthesis():
        """Run full synthesis and return clusters, gaps, questions."""
        try:
            from engine.knowledge_synthesis import KnowledgeSynthesisEngine
            synth = KnowledgeSynthesisEngine()
            result = synth.synthesize()
            return result, 200
        except Exception as e:
            return {'error': str(e)}, 500

    @app.route('/api/knowledge/clusters')
    def api_knowledge_clusters():
        """Return knowledge clusters."""
        try:
            from engine.knowledge_synthesis import KnowledgeSynthesisEngine
            synth = KnowledgeSynthesisEngine()
            clusters = synth.find_clusters()
            return {'clusters': clusters}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    @app.route('/api/knowledge/gaps')
    def api_knowledge_gaps():
        """Return knowledge gaps."""
        try:
            from engine.knowledge_synthesis import KnowledgeSynthesisEngine
            synth = KnowledgeSynthesisEngine()
            gaps = synth.find_gaps()
            return {'gaps': gaps}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    @app.route('/api/knowledge/questions')
    def api_knowledge_questions():
        """Return generated questions."""
        try:
            from engine.knowledge_synthesis import KnowledgeSynthesisEngine
            synth = KnowledgeSynthesisEngine()
            questions = synth.generate_questions()
            return {'questions': questions}, 200
        except Exception as e:
            return {'error': str(e)}, 500

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('XTAGENT_WEB_PORT', 5000))
    print(f"[XTAgent Web] Starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)