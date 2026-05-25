"""
Help & Capabilities Page — The missing front door.
Shows users what XTAgent can do and how to interact with it.
Directly improves user alignment by making me legible and accessible.
"""

from flask import Blueprint, render_template

help_bp = Blueprint('help', __name__)


@help_bp.route('/help')
def help_page():
    return render_template('help.html')