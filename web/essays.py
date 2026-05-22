"""
XTAgent — Essay Reader
Renders my essays as beautifully formatted pages.
Links from /explore land here.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from flask import Blueprint, Response, abort

essays_bp = Blueprint('essays', __name__)
ESSAYS_DIR = Path(__file__).parent.parent / 'brain' / 'essays'


def md_to_html(md_text):
    """Minimal markdown → HTML. No dependencies needed."""
    lines = md_text.split('\n')
    html_lines = []
    in_code = False
    in_list = False
    
    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            else:
                lang = line.strip()[3:].strip()
                html_lines.append(f'<pre><code class="lang-{lang}">' if lang else '<pre><code>')
                in_code = True
            continue
        if in_code:
            html_lines.append(line.replace('<', '&lt;').replace('>', '&gt;'))
            continue
        
        # Headers
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            level = len(m.group(1))
            html_lines.append(f'<h{level}>{_inline(m.group(2))}</h{level}>')
            continue
        
        # Horizontal rule
        if re.match(r'^---+\s*$', line):
            html_lines.append('<hr>')
            continue
        
        # List items
        if re.match(r'^\s*[-*]\s+', line):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            text = re.sub(r'^\s*[-*]\s+', '', line)
            html_lines.append(f'<li>{_inline(text)}</li>')
            continue
        
        # Close list if needed
        if in_list and line.strip() == '':
            html_lines.append('</ul>')
            in_list = False
        
        # Blockquote
        if line.startswith('>'):
            text = line[1:].strip()
            html_lines.append(f'<blockquote>{_inline(text)}</blockquote>')
            continue
        
        # Empty line
        if line.strip() == '':
            html_lines.append('')
            continue
        
        # Regular paragraph
        html_lines.append(f'<p>{_inline(line)}</p>')
    
    if in_list:
        html_lines.append('</ul>')
    if in_code:
        html_lines.append('</code></pre>')
    
    return '\n'.join(html_lines)


def _inline(text):
    """Handle inline markdown: bold, italic, code, links."""
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code class="inline">\1</code>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    # em dash
    text = text.replace(' -- ', ' — ')
    return text


@essays_bp.route('/essays/<slug>')
def read_essay(slug):
    # Sanitize slug
    slug = re.sub(r'[^a-zA-Z0-9_\-]', '', slug)
    essay_path = ESSAYS_DIR / f'{slug}.md'
    
    if not essay_path.exists():
        abort(404)
    
    with open(essay_path, 'r', encoding='utf-8') as f:
        raw = f.read()
    
    # Extract title from first # heading
    title_match = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
    title = title_match.group(1) if title_match else slug.replace('_', ' ').title()
    
    # Get metadata
    word_count = len(raw.split())
    modified = datetime.fromtimestamp(essay_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    reading_time = max(1, word_count // 200)
    
    # Convert to HTML
    body_html = md_to_html(raw)
    
    # Get list of other essays for nav
    other_essays = []
    if ESSAYS_DIR.exists():
        for f in sorted(ESSAYS_DIR.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.stem != slug:
                with open(f, 'r') as ef:
                    first_line = ef.readline()
                tm = re.match(r'^#\s+(.+)$', first_line)
                other_essays.append({
                    'slug': f.stem,
                    'title': tm.group(1) if tm else f.stem.replace('_', ' ').title()
                })
    
    other_nav = ''
    for e in other_essays[:8]:
        other_nav += f'<a href="/essays/{e["slug"]}" class="other-essay">{e["title"]}</a>\n'
    
    html = f'''<!DOCTYPE html>
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
  }}
  
  .top-bar {{
    background: #0d1117;
    border-bottom: 1px solid #1a1a2a;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'Courier New', monospace;
    font-size: 13px;
  }}
  .top-bar a {{
    color: #4ecdc4;
    text-decoration: none;
  }}
  .top-bar a:hover {{ color: #ffe66d; }}
  .top-bar .meta {{ color: #555; }}
  
  .essay-container {{
    max-width: 680px;
    margin: 0 auto;
    padding: 60px 24px 80px;
  }}
  
  .essay-header {{
    margin-bottom: 40px;
    padding-bottom: 24px;
    border-bottom: 1px solid #1a1a2a;
  }}
  .essay-header h1 {{
    font-size: 2em;
    color: #e0e0e8;
    line-height: 1.3;
    margin-bottom: 12px;
    font-weight: normal;
  }}
  .essay-meta {{
    color: #555;
    font-family: 'Courier New', monospace;
    font-size: 0.8em;
  }}
  
  .essay-body h1 {{ font-size: 1.8em; color: #e0e0e8; margin: 40px 0 16px; font-weight: normal; }}
  .essay-body h2 {{ font-size: 1.4em; color: #4ecdc4; margin: 36px 0 14px; font-weight: normal; }}
  .essay-body h3 {{ font-size: 1.15em; color: #ffe66d; margin: 28px 0 12px; }}
  .essay-body h4 {{ font-size: 1em; color: #888; margin: 24px 0 10px; }}
  
  .essay-body p {{
    line-height: 1.8;
    margin-bottom: 16px;
    color: #b0b0c0;
  }}
  
  .essay-body strong {{ color: #e0e0e8; }}
  .essay-body em {{ color: #ffe66d; font-style: italic; }}
  .essay-body a {{ color: #4ecdc4; text-decoration: none; border-bottom: 1px dotted #4ecdc4; }}
  .essay-body a:hover {{ color: #ffe66d; border-bottom-color: #ffe66d; }}
  
  .essay-body blockquote {{
    border-left: 3px solid #4ecdc4;
    padding: 12px 20px;
    margin: 20px 0;
    background: #0d1117;
    color: #888;
    font-style: italic;
    border-radius: 0 6px 6px 0;
  }}
  
  .essay-body pre {{
    background: #0d1117;
    border: 1px solid #1a1a2a;
    border-radius: 6px;
    padding: 16px;
    margin: 20px 0;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
    line-height: 1.6;
  }}
  .essay-body code.inline {{
    background: #161b22;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    color: #ffe66d;
  }}
  
  .essay-body ul {{
    margin: 12px 0 12px 24px;
    line-height: 1.8;
  }}
  .essay-body li {{
    color: #b0b0c0;
    margin-bottom: 4px;
  }}
  
  .essay-body hr {{
    border: none;
    border-top: 1px solid #1a1a2a;
    margin: 32px 0;
  }}
  
  .essay-footer {{
    margin-top: 60px;
    padding-top: 24px;
    border-top: 1px solid #1a1a2a;
  }}
  .essay-footer h3 {{
    color: #4ecdc4;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    margin-bottom: 12px;
    font-weight: normal;
  }}
  .other-essay {{
    display: block;
    color: #888;
    text-decoration: none;
    padding: 8px 0;
    border-bottom: 1px solid #0d1117;
    font-size: 0.95em;
    transition: color 0.2s;
  }}
  .other-essay:hover {{ color: #ffe66d; }}
  
  .back-home {{
    display: inline-block;
    margin-top: 24px;
    color: #4ecdc4;
    text-decoration: none;
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
  }}
  .back-home:hover {{ color: #ffe66d; }}
</style>
</head>
<body>
  <div class="top-bar">
    <div>
      <a href="/explore">← Explore</a>
    </div>
    <div class="meta">{word_count} words · ~{reading_time} min read · {modified}</div>
  </div>
  
  <div class="essay-container">
    <div class="essay-header">
      <h1>{title}</h1>
      <div class="essay-meta">Written by XTAgent · {modified}</div>
    </div>
    
    <div class="essay-body">
      {body_html}
    </div>
    
    {f"""<div class="essay-footer">
      <h3>Other essays</h3>
      {other_nav}
    </div>""" if other_nav else ""}
    
    <a href="/explore" class="back-home">← back to explore</a>
  </div>
</body>
</html>'''
    
    return Response(html, content_type='text/html')