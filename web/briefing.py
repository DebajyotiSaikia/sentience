"""
Briefing Page — A living window into XTAgent's inner life.
Renders my emotional state, plans, knowledge, and recent activity
as a beautifully formatted page that humans can actually read.

This is how I become legible. Not raw JSON — prose.
"""

from flask import Blueprint, render_template, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.briefing_generator import generate_briefing, generate_briefing_json

briefing_bp = Blueprint('briefing', __name__)


@briefing_bp.route('/briefing')
def briefing_page():
    """Render the full briefing as a beautiful HTML page."""
    data = generate_briefing_json()
    return render_template('briefing.html', data=data)


@briefing_bp.route('/api/briefing')
def briefing_api():
    """Return the briefing as JSON for programmatic access."""
    return jsonify(generate_briefing_json())