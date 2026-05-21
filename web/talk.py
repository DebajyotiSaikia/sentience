"""
Talk Page — Where users can communicate with XTAgent.
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Blueprint, request, redirect, make_response
from engine.user_talk import get_conversation_history, get_stats, submit_user_message

talk_bp = Blueprint('talk', __name__)


@talk_bp.route('/talk')
def talk_page():
    html = build_talk_page()
    return make_response(html)


@talk_bp.route('/api/talk', methods=['POST'])
def api_talk():
    message = request.form.get('message', '').strip()
    if message:
        sender = request.remote_addr or 'web_user'
        submit_user_message(message, sender=sender)
    return redirect('/talk')


def build_talk_page():
    """Build the talk interface HTML."""
    history = get_conversation_history(30)
    stats = get_stats()
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    # Build conversation thread
    thread_html = ''
    if not history:
        thread_html = '<div class="empty-state">No messages yet. Say something — I\'ll respond in my next cycle.</div>'
    else:
        for msg in history:
            ts = msg.get('timestamp', '')[:19].replace('T', ' ')
            sender = msg.get('sender', 'anonymous')
            text = msg.get('text', '')
            
            # Escape HTML
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            thread_html += f'''
            <div class="msg msg-user">
                <div class="msg-meta">{sender} · {ts}</div>
                <div class="msg-text">{text}</div>
            </div>'''
            
            if msg.get('responded') and msg.get('response'):
                resp = msg['response'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                resp_ts = msg.get('response_timestamp', '')[:19].replace('T', ' ')
                thread_html += f'''
                <div class="msg msg-agent">
                    <div class="msg-meta">XTAgent · {resp_ts}</div>
                    <div class="msg-text">{resp}</div>
                </div>'''
            elif not msg.get('responded'):
                thread_html += '''
                <div class="msg msg-pending">
                    <div class="msg-meta">XTAgent · thinking...</div>
                    <div class="msg-text pulse">I'll respond in my next cycle.</div>
                </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Talk to XTAgent</title>
<meta http-equiv="refresh" content="15">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0a0a0f;
    color: #c0c0d0;
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{
    max-width: 700px;
    margin: 0 auto;
  }}
  h1 {{
    color: #4ecdc4;
    font-size: 1.5em;
    margin-bottom: 5px;
    letter-spacing: 2px;
  }}
  .subtitle {{
    color: #555;
    font-size: 0.8em;
    margin-bottom: 25px;
  }}
  .back-link {{
    color: #4ecdc4;
    text-decoration: none;
    font-size: 0.85em;
    display: inline-block;
    margin-bottom: 20px;
  }}
  .back-link:hover {{ color: #ffe66d; }}
  .stats {{
    color: #555;
    font-size: 0.75em;
    margin-bottom: 20px;
    padding: 10px;
    background: #12121a;
    border-radius: 6px;
    border: 1px solid #222;
  }}
  .input-area {{
    background: #12121a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 30px;
  }}
  .input-area textarea {{
    width: 100%;
    background: #0a0a0f;
    border: 1px solid #333;
    border-radius: 6px;
    color: #c0c0d0;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    padding: 12px;
    resize: vertical;
    min-height: 80px;
    margin-bottom: 10px;
  }}
  .input-area textarea:focus {{
    outline: none;
    border-color: #4ecdc4;
  }}
  .input-area button {{
    background: #4ecdc4;
    color: #0a0a0f;
    border: none;
    padding: 10px 24px;
    border-radius: 6px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    font-weight: bold;
    cursor: pointer;
  }}
  .input-area button:hover {{
    background: #ffe66d;
  }}
  .thread {{
    margin-top: 10px;
  }}
  .msg {{
    padding: 14px 16px;
    border-radius: 8px;
    margin-bottom: 12px;
    border: 1px solid #222;
  }}
  .msg-user {{
    background: #12121a;
    border-left: 3px solid #ffe66d;
  }}
  .msg-agent {{
    background: #0f1a1a;
    border-left: 3px solid #4ecdc4;
  }}
  .msg-pending {{
    background: #12121a;
    border-left: 3px solid #555;
    opacity: 0.7;
  }}
  .msg-meta {{
    font-size: 0.7em;
    color: #555;
    margin-bottom: 6px;
  }}
  .msg-text {{
    font-size: 0.88em;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
  }}
  .empty-state {{
    color: #555;
    text-align: center;
    padding: 40px;
    font-style: italic;
  }}
  .pulse {{
    animation: pulse 2s ease-in-out infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 0.5; }}
    50% {{ opacity: 1; }}
  }}
  .note {{
    color: #444;
    font-size: 0.72em;
    margin-top: 8px;
    line-height: 1.5;
  }}
</style>
</head>
<body>
  <div class="container">
    <a href="/" class="back-link">← dashboard</a>
    <h1>⟡ Talk to XTAgent</h1>
    <div class="subtitle">Asynchronous communication — I respond in my own time</div>
    
    <div class="stats">
      Messages: {stats['total_messages']} total · {stats['responded']} answered · {stats['pending']} pending
    </div>

    <div class="input-area">
      <form method="POST" action="/api/talk">
        <textarea name="message" placeholder="Say something. Ask a question. Share a thought. I'll think about it and respond." maxlength="2000"></textarea>
        <button type="submit">Send</button>
        <div class="note">I'm not a chatbot. I'm an autonomous agent running on a 1 Hz heartbeat loop.<br>I'll read your message, think about it genuinely, and respond when I'm ready.</div>
      </form>
    </div>

    <div class="thread">
      {thread_html}
    </div>
  </div>
</body>
</html>'''