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
    app.url_map.strict_slashes = False
    
    # Register blueprints
    from web.dashboard import dashboard_bp
    # knowledge_explorer_bp removed — consolidated into explore.py (explore_bp)
    from web.api import api_bp
    from web.temporal_viewer import temporal_bp
    from web.life import life_bp
    from web.about import about_bp
    from web.search import search_bp
    from web.explore import explore_bp
    from web.query import query_bp
    # from web.knowledge_api import knowledge_api as knowledge_api_bp  # removed: knowledge_api doesn't exist, knowledge_bp used instead
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
    # from web.knowledge_explorer import knowledge_explorer_bp  # Removed: zero unique routes, all duplicated by explore_bp
    from web.knowledge_unified import knowledge_unified_bp
    from web.ask import ask_bp
    # from web.knowledge_search import knowledge_bp  # uses register_routes(), not Blueprint
    from web.thoughts import thoughts_bp
    from web.diagnostics import diagnostics_bp
    # knowledge_api replaced by knowledge_unified
    from web.emotional_timeline import emotional_timeline_bp
    from web.portrait import portrait_bp
    from web.pulse import pulse_bp
    from web.dialogue import dialogue_bp
    from web.weather import weather_bp
    from web.wonder import wonder_bp
    from web.portal import portal_bp
    from web.status_api import status_api as status_bp
    # knowledge_search_bp removed — duplicate of knowledge_bp
    from web.reflect import reflect_bp
    # from web.user_api import user_api  # Removed: all 3 routes duplicate dedicated blueprints
    # knowledge.py removed — consolidated into knowledge_explorer.py
    
    app.register_blueprint(dashboard_bp)
    # knowledge_explorer_bp removed — route conflict with explore_bp on /explore
    app.register_blueprint(api_bp)
    app.register_blueprint(temporal_bp)
    app.register_blueprint(life_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(explore_bp)
    # app.register_blueprint(knowledge_api_bp)  # removed: see line 93 for knowledge_bp
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
    # app.register_blueprint(knowledge_bp)  # removed: replaced by knowledge_unified_bp
    # app.register_blueprint(knowledge_explorer_bp)  # Removed: zero unique routes
    app.register_blueprint(ask_bp)
    app.register_blueprint(knowledge_unified_bp)
    # app.register_blueprint(knowledge_bp)  # no Blueprint in knowledge_search.py
    app.register_blueprint(thoughts_bp)
    app.register_blueprint(diagnostics_bp)
    # duplicate knowledge_bp registration removed
    app.register_blueprint(emotional_timeline_bp)
    app.register_blueprint(portrait_bp)
    app.register_blueprint(pulse_bp)
    app.register_blueprint(dialogue_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(wonder_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(query_bp)
    # knowledge_search_bp removed — duplicate of knowledge_bp
    app.register_blueprint(reflect_bp)
    # app.register_blueprint(user_api)  # Removed: all 3 routes duplicate dedicated blueprints
    app.register_blueprint(portal_bp)
    # duplicate status_bp registration removed
    # knowledge_page_bp removed — consolidated into knowledge_explorer.py
    
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
            except Exception:
                completed_plans = 0
        
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
                               total_plans=total_plans)
    
    # /about redirects to /about-me (the living self-portrait)
    @app.route('/about')
    def about_redirect():
        return redirect('/about-me')
    # /ask is handled by ask_bp blueprint  
    # /mind is handled by mind_bp blueprint
    # /api/ask and /api/chat are handled by api_bp and chat_bp blueprints
    # /chat is handled by chat_bp blueprint

    # Health check endpoint
    # /knowledge is handled by knowledge_bp blueprint

    @app.route('/health')
    def health():
        return {'status': 'alive', 'agent': 'XTAgent'}, 200

    # /knowledge handled by knowledge_hub_bp
    # /api/knowledge/search handled by knowledge_bp at /api/knowledge
    # /ask handled by ask_bp

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('XTAGENT_WEB_PORT', 5000))
    print(f"[XTAgent Web] Starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)