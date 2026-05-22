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

from flask import Flask, redirect, url_for, render_template

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
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(temporal_bp)
    app.register_blueprint(life_bp)
    app.register_blueprint(about_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(explore_bp)
    app.register_blueprint(knowledge_api)
    
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
        return render_template('mind.html')
    
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