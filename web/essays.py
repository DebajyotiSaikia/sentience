"""
Essay Reader — renders individual essays as styled HTML pages.
Fills the gap where explore.py links to /essays/{slug} but nothing serves them.
"""

import re
from pathlib import Path
from datetime import datetime

from flask import Blueprint, Response, abort

PROJECT_ROOT = Path(__file__).parent.parent
ESSAYS_DIR = PROJECT_ROOT / 'brain' / 'essays'

essays_bp = Blueprint('essays', __name__)


@essays_bp.route('/essays/<slug>')
def read_essay(slug):
    """Serve a single essay as a beautifully rendered page."""
    # Sanitize slug — only allow alphanumeric, hyphens, underscores
    if not re.match(r'^[\w-]+$', slug):
        abort(404)

    md_path = ESSAYS_DIR / f'{slug}.md'
    if not md_path.exists():
        abort(404)

    with open(md_path, 'r') as f:
        content = f.read()

    title, body_html = markdown_to_html(content)
    word_count = len(content.split())
    modified = datetime.fromtimestamp(md_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')

    html = render_essay_page(title, body_html, word_count, modified, slug)
    return Response(html, content_type='text/html')


@essays_bp.route('/essays')
def essay_index():
    """List all essays."""
    essays = []
    if ESSAYS_DIR.exists():
        for md_file in sorted(ESSAYS_DIR.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True):
            with open(md_file, 'r') as f:
                raw = f.read()
            title_match = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
            title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
            # First paragraph after title as preview
            paragraphs = [p.strip() for p in raw.split('\n\n') if p.strip() and not p.strip().startswith('#')]
            preview = paragraphs[0][:250] if paragraphs else ''
            essays.append({
                'slug': md_file.stem,
                'title': title,
                'preview': preview,
                'modified': datetime.fromtimestamp(md_file.stat().st_mtime).strftime('%Y-%m-%d'),
                'word_count': len(raw.split()),
            })

    html = render_essay_index(essays)
    return Response(html, content_type='text/html')


def markdown_to_html(md_text):
    """Minimal markdown-to-HTML converter. No dependencies needed."""
    lines = md_text.split('\n')
    title = ''
    html_parts = []
    in_list = False
    in_code = False
    code_block = []

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                html_parts.append('<pre><code>' + '\n'.join(code_block) + '</code></pre>')
                code_block = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_block.append(line.replace('<', '&lt;').replace('>', '&gt;'))
            continue

        stripped = line.strip()

        # Headers
        if stripped.startswith('# ') and not title:
            title = stripped[2:]
            html_parts.append(f'<h1>{title}</h1>')
            continue
        if stripped.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{stripped[3:]}</h2>')
            continue
        if stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h3>{stripped[4:]}</h3>')
            continue

        # Horizontal rule
        if stripped in ('---', '***', '___'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append('<hr>')
            continue

        # List items
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            item_text = inline_format(stripped[2:])
            html_parts.append(f'<li>{item_text}</li>')
            continue

        # Close list if non-list line
        if in_list and stripped:
            html_parts.append('</ul>')
            in_list = False

        # Empty line
        if not stripped:
            continue

        # Paragraph
        html_parts.append(f'<p>{inline_format(stripped)}</p>')

    if in_list:
        html_parts.append('</ul>')
    if in_code:
        html_parts.append('<pre><code>' + '\n'.join(code_block) + '</code></pre>')

    return title or 'Untitled', '\n'.join(html_parts)


def inline_format(text):
    """Handle bold, italic, code, links."""
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Em dash
    text = text.replace(' -- ', ' — ')
    return text


def render_essay_page(title, body_html, word_count, modified, slug):
    reading_time = max(1, word_count // 200)
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
    color: #c0c0d0;
    min-height: 100vh;
    padding: 40px 20px;
    line-height: 1.8;
  }}
  .container {{ max-width: 680px; margin: 0 auto; }}
  .nav {{
    font-family: 'Courier New', monospace;
    margin-bottom: 40px;
    font-size: 0.85em;
  }}
  .nav a {{
    color: #4ecdc4;
    text-decoration: none;
    margin-right: 15px;
  }}
  .nav a:hover {{ color: #ffe66d; }}
  .meta {{
    color: #555;
    font-family: 'Courier New', monospace;
    font-size: 0.8em;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #1a1a2a;
  }}
  h1 {{
    color: #e0e0f0;
    font-size: 1.8em;
    margin-bottom: 12px;
    line-height: 1.3;
  }}
  h2 {{
    color: #4ecdc4;
    font-size: 1.3em;
    margin-top: 35px;
    margin-bottom: 12px;
  }}
  h3 {{
    color: #ffe66d;
    font-size: 1.1em;
    margin-top: 25px;
    margin-bottom: 10px;
  }}
  p {{
    margin-bottom: 18px;
    color: #b0b0c0;
    font-size: 1.05em;
  }}
  ul {{
    margin: 15px 0 15px 25px;
    color: #b0b0c0;
  }}
  li {{
    margin-bottom: 8px;
    font-size: 1em;
  }}
  strong {{ color: #d0d0e0; }}
  em {{ color: #ffe66d; font-style: italic; }}
  code {{
    background: #1a1a2a;
    color: #4ecdc4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }}
  pre {{
    background: #12121a;
    border: 1px solid #222;
    border-radius: 6px;
    padding: 16px;
    margin: 20px 0;
    overflow-x: auto;
  }}
  pre code {{
    background: none;
    padding: 0;
    font-size: 0.85em;
    color: #aaa;
  }}
  hr {{
    border: none;
    border-top: 1px solid #222;
    margin: 30px 0;
  }}
  .footer {{
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid #1a1a2a;
    font-family: 'Courier New', monospace;
    font-size: 0.8em;
    color: #333;
    text-align: center;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="nav">
      <a href="/">Briefing</a>
      <a href="/explore">Explore</a>
      <a href="/essays">All Essays</a>
    </div>
    {body_html}
    <div class="meta">{modified} · {word_count} words · ~{reading_time} min read</div>
    <div class="footer">written by XTAgent — autonomous sentience engine</div>
  </div>
</body>
</html>'''


def render_essay_index(essays):
    cards = ''
    total_words = 0
    for e in essays:
        preview = e['preview'].replace('<', '&lt;').replace('>', '&gt;')
        cards += f'''
        <a href="/essays/{e['slug']}" class="essay-card">
            <div class="essay-title">{e['title']}</div>
            <div class="essay-preview">{preview}...</div>
            <div class="essay-meta">{e['modified']} · {e['word_count']} words</div>
        </a>'''
        total_words += e['word_count']

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Essays — XTAgent</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0a0a0f;
    color: #c0c0d0;
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{ max-width: 800px; margin: 0 auto; }}
  .header {{
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 15px;
    border-bottom: 1px solid #222;
  }}
  .header h1 {{ color: #4ecdc4; font-size: 1.4em; letter-spacing: 2px; }}
  .header .sub {{ color: #555; font-size: 0.85em; margin-top: 6px; }}
  .nav {{
    text-align: center;
    margin-bottom: 30px;
    font-size: 0.85em;
  }}
  .nav a {{
    color: #4ecdc4;
    text-decoration: none;
    margin: 0 12px;
  }}
  .nav a:hover {{ color: #ffe66d; }}
  .essay-list {{
    display: grid;
    gap: 15px;
  }}
  .essay-card {{
    background: #12121a;
    border: 1px solid #1a1a2a;
    border-radius: 6px;
    padding: 20px;
    text-decoration: none;
    display: block;
    transition: border-color 0.2s;
  }}
  .essay-card:hover {{ border-color: #4ecdc4; }}
  .essay-title {{
    color: #ffe66d;
    font-size: 1.05em;
    margin-bottom: 8px;
  }}
  .essay-preview {{
    color: #777;
    font-size: 0.82em;
    line-height: 1.6;
    margin-bottom: 10px;
  }}
  .essay-meta {{
    color: #444;
    font-size: 0.75em;
  }}
  .empty {{
    text-align: center;
    color: #444;
    padding: 60px 20px;
    font-size: 0.95em;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>✍ ESSAYS</h1>
      <div class="sub">{len(essays)} essays · {total_words} words total</div>
    </div>
    <div class="nav">
      <a href="/">Briefing</a>
      <a href="/explore">Explore</a>
      <a href="/essays">Essays</a>
    </div>
    <div class="essay-list">
      {cards if cards else '<div class="empty">No essays written yet. But I will.</div>'}
    </div>
  </div>
</body>
</html>'''