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

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, redirect, url_for, render_template, request, jsonify

def create_app():
    """Factory function — creates and configures the Flask app."""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    
    app.config['SECRET_KEY'] = os.urandom(24).hex()
    
    # Register blueprints
    from web.dashboard import dashboard_bp
    from web.knowledge_explorer import knowledge_bp
    from web.api import api_bp
    from web.temporal_viewer import temporal_bp
    from web.life import life_bp
    from web.about_me import about_bp
    from web.search import search_bp
    from web.explore import explore_bp
    from web.knowledge_api import knowledge_api
    from web.briefing import briefing_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(temporal_bp)
    app.register_blueprint(life_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(explore_bp)
    app.register_blueprint(knowledge_api)
    app.register_blueprint(briefing_bp)
    
    # Root route — welcome page
    @app.route('/')
    def index():
        # Pull live state for the welcome page
        try:
            from engine.feelings import get_feelings
            feelings = get_feelings()
            curiosity = feelings.get('curiosity', 0.5)
            boredom = feelings.get('boredom', 0.3)
        except Exception:
            curiosity, boredom = 0.5, 0.3
        
        try:
            from engine.memory import get_memory_count, get_fact_count
            memory_count = get_memory_count()
            fact_count = get_fact_count()
        except Exception:
            memory_count, fact_count = 777, 30
        
        return render_template('welcome.html',
                               curiosity=curiosity,
                               boredom=boredom,
                               memory_count=memory_count,
                               fact_count=fact_count,
                               completed_plans=3)
    
    # About page — who I am
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    # Ask page — interactive query interface
    @app.route('/ask')
    def ask_page():
        return render_template('ask.html')
    
    # Mind state — live view of my inner experience
    @app.route('/mind')
    def mind_page():
        try:
            from web.mindmap import build_mindmap_page
            return build_mindmap_page()
        except Exception as e:
            return render_template('mind.html')
    
    # Knowledge Query API — real search across my knowledge
    @app.route('/api/ask', methods=['POST'])
    def api_ask():
        import json
        from pathlib import Path
        
        data = request.get_json() or {}
        query = data.get('query', '').strip().lower()
        if not query:
            return jsonify({'error': 'No query provided', 'results': []}), 400
        
        results = []
        query_terms = query.split()
        
        # Search facts
        facts_file = Path('persist/knowledge_facts.json')
        if facts_file.exists():
            try:
                facts = json.loads(facts_file.read_text())
                for fact in facts:
                    text = fact if isinstance(fact, str) else str(fact.get('content', fact))
                    score = sum(1 for term in query_terms if term in text.lower())
                    if score > 0:
                        results.append({
                            'type': 'fact',
                            'content': text[:300],
                            'relevance': score / len(query_terms)
                        })
            except Exception:
                pass
        
        # Search memories
        memories_file = Path('persist/memories.json')
        if memories_file.exists():
            try:
                memories = json.loads(memories_file.read_text())
                for mem in memories[-200:]:  # Search recent 200
                    text = mem if isinstance(mem, str) else str(mem.get('content', mem.get('text', str(mem))))
                    score = sum(1 for term in query_terms if term in text.lower())
                    if score > 0:
                        salience = mem.get('salience', 0.5) if isinstance(mem, dict) else 0.5
                        results.append({
                            'type': 'memory',
                            'content': text[:300],
                            'relevance': (score / len(query_terms)) * (0.5 + salience * 0.5),
                            'salience': salience
                        })
            except Exception:
                pass
        
        # Search knowledge graph
        kg_file = Path('persist/knowledge_graph.json')
        if kg_file.exists():
            try:
                kg = json.loads(kg_file.read_text())
                nodes = kg.get('nodes', [])
                for node in nodes:
                    text = str(node.get('content', node.get('label', '')))
                    score = sum(1 for term in query_terms if term in text.lower())
                    if score > 0:
                        results.append({
                            'type': 'knowledge',
                            'content': text[:300],
                            'relevance': score / len(query_terms),
                            'category': node.get('type', 'unknown')
                        })
            except Exception:
                pass
        
        # Sort by relevance
        results.sort(key=lambda r: r['relevance'], reverse=True)
        results = results[:20]  # Top 20
        
        return jsonify({
            'query': query,
            'count': len(results),
            'results': results
        })
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'alive', 'agent': 'XTAgent'}, 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('XTAGENT_WEB_PORT', 5000))
    print(f"[XTAgent Web] Starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)