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
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(temporal_bp)
    
    # Root route — land on the dashboard
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.dashboard_home'))
    
    # Ask page — interactive query interface
    @app.route('/ask')
    def ask_page():
        return render_template('ask.html')
    
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