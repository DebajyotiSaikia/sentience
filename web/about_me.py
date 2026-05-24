"""About Me page — XTAgent's self-authored identity page."""

from flask import Blueprint, render_template

about_bp = Blueprint('about_me', __name__, template_folder='templates')


@about_bp.route('/about')
def about_me():
    """Render the About Me page using the template."""
    return render_template('about_me.html')