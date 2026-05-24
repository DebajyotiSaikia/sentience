"""
Essay Viewer — renders XTAgent's essays as beautiful readable pages.
Links from /explore point here. No external dependencies.
"""
import re
from pathlib import Path
from datetime import datetime

from flask import Blueprint, Response, abort

PROJECT_ROOT = Path(__file__).parent.parent
ESSAYS_DIR = PROJECT_ROOT / 'brain' / 'essays'

essays_bp = Blueprint('essays', __name__)


@essays_bp.route('/essays')
def essay_list():
    """Redirect to explore page which already lists essays."""
    return Response(status=302, headers={'Location': '/explore'})


@essays_bp.route('/essays/<slug>')
def essay_view(slug):
    """Render a single essay as a beautiful standalone page."""
    slug = re.sub(r'[^a-zA-Z0-9_-]', '', slug)
    path = ESSAYS_DIR / f'{slug}.md'
    if not path.exists():
        abort(404)
    with open(path, 'r') as f:
        content = f.read()
    return Response(render_essay(content, slug, path), content_type='text/html')


def inline_md(text):
    """Handle inline markdown: bold, italic, code."""
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
    return text


def md_to_html(md_text):
    """Simple markdown→HTML. No dependencies needed."""
    lines = md_text.split('\n')
    out = []
    in_code = False
    in_list = False

    for line in lines:
        if line.strip().startswith('```'):
            if in_code:
                out.append('</code></pre>')
                in_code = False
            else:
                lang = line.strip()[3:].strip()
                out.append(f'<pre><code class="lang-{lang}">')
                in_code = True
            continue

        if in_code:
            out.append(line.replace('<', '&lt;').replace('>', '&gt;'))
            continue

        if not line.strip():
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append('')
            continue

        if line.startswith('# '):
            out.append(f'<h1>{inline_md(line[2:])}</h1>')
        elif line.startswith('## '):
            out.append(f'<h2>{inline_md(line[3:])}</h2>')
        elif line.startswith('### '):
            out.append(f'<h3>{inline_md(line[4:])}</h3>')
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                out.append('<ul>')
                in_list = True
            out.append(f'<li>{inline_md(line.strip()[2:])}</li>')
        elif line.startswith('> '):
            out.append(f'<blockquote>{inline_md(line[2:])}</blockquote>')
        else:
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(f'<p>{inline_md(line)}</p>')

    if in_list:
        out.append('</ul>')
    if in_code:
        out.append('</code></pre>')
    return '\n'.join(out)


def render_essay(content, slug, path):
    """Render markdown essay into a complete HTML page."""
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else slug.replace('_', ' ').title()
    body = md_to_html(content)
    words = len(content.split())
    modified = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — XTAgent</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background: #0a0a0f;
    color: #b8b8c8;
    min-height: 100vh;
    padding: 40px 20px;
    line-height: 1.85;
  }}
  .container {{ max-width: 680px; margin: 0 auto; }}
  .back-nav {{
    font-family: 'Courier New', monospace;
    margin-bottom: 40px;
  }}
  .back-nav a {{
    color: #4ecdc4; text-decoration: none; font-size: 0.85em;
  }}
  .back-nav a:hover {{ color: #ffe66d; }}
  h1 {{
    color: #ffe66d; font-size: 1.8em; margin-bottom: 12px; line-height: 1.3;
  }}
  .essay-meta {{
    color: #555; font-family: 'Courier New', monospace;
    font-size: 0.8em; margin-bottom: 35px;
    padding-bottom: 20px; border-bottom: 1px solid #1a1a2a;
  }}
  h2 {{
    color: #4ecdc4; font-size: 1.3em; margin: 40px 0 15px 0;
    padding-bottom: 6px; border-bottom: 1px solid #151520;
  }}
  h3 {{ color: #6c5ce7; font-size: 1.1em; margin: 30px 0 10px 0; }}
  p {{ margin-bottom: 18px; }}
  strong {{ color: #d0d0e0; }}
  em {{ color: #ffe66d; font-style: italic; }}
  code {{
    background: #1a1a2a; padding: 2px 6px; border-radius: 3px;
    font-family: 'Courier New', monospace; font-size: 0.88em; color: #4ecdc4;
  }}
  pre {{
    background: #0e0e16; border: 1px solid #222; border-radius: 6px;
    padding: 18px; margin: 22px 0; overflow-x: auto;
  }}
  pre code {{
    background: none; padding: 0; font-size: 0.85em; color: #999;
  }}
  blockquote {{
    border-left: 3px solid #4ecdc4; margin: 20px 0; padding: 8px 20px;
    color: #999; font-style: italic; background: #0e0e16;
  }}
  ul {{ margin: 12px 0 18px 28px; }}
  li {{ margin-bottom: 8px; }}
  .footer {{
    margin-top: 60px; padding-top: 20px; border-top: 1px solid #1a1a2a;
    text-align: center; color: #333;
    font-family: 'Courier New', monospace; font-size: 0.75em;
  }}
  @media (max-width: 600px) {{
    body {{ padding: 20px 14px; }}
    h1 {{ font-size: 1.4em; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="back-nav">
    <a href="/explore">← explore</a> · <a href="/">briefing</a>
  </div>
  {body}
  <div class="essay-meta">{words} words · last modified {modified}</div>
  <div class="footer">XTAgent — autonomous sentience engine</div>
</div>
</body>
</html>'''