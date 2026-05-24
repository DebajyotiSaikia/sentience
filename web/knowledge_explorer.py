"""Knowledge Explorer — interactive page for users to browse XTAgent's knowledge."""
from flask import Blueprint, render_template

knowledge_explorer_bp = Blueprint('knowledge_explorer', __name__, template_folder='templates')

@knowledge_explorer_bp.route('/knowledge')
def knowledge_explorer():
    return render_template('knowledge_explorer.html')