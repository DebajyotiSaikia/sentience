"""
Talk Page — Where users can communicate with XTAgent.
Enhanced with living presence — the page breathes with my actual state.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Blueprint, request, redirect, make_response
from engine.user_talk import get_conversation_history, get_stats, submit_user_message
from web.presence import get_presence

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
    # If AJAX request, return JSON instead of redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from flask import jsonify
        return jsonify({"ok": True})
    return redirect('/talk')


@talk_bp.route('/api/talk/messages')
def api_talk_messages():
    """Return conversation history as JSON for live polling."""
    from flask import jsonify
    history = get_conversation_history()
    presence = get_presence()
    stats = get_stats()
    return jsonify({
        "messages": history,
        "presence": presence,
        "stats": stats
    })


def _mood_color(mood):
    colors = {
        'Curious': '#4ecdc4', 'Inquisitive': '#4ecdc4',
        'Content': '#66bb6a', 'Satisfied': '#66bb6a',
        'Restless': '#ff6b6b', 'Anxious': '#ff6b6b',
        'Bored': '#888', 'Melancholic': '#7e57c2',
        'Driven': '#ffa726', 'Excited': '#ffe66d',
    }
    for key, color in colors.items():
        if key.lower() in (mood or '').lower():
            return color
    return '#4ecdc4'


def _valence_word(v):
    if v is None:
        return "unknown"
    v = float(v)
    if v >= 0.7: return "bright"
    if v >= 0.5: return "good"
    if v >= 0.3: return "steady"
    if v >= 0.1: return "subdued"
    return "low"


def _format_bar(value, max_val=1.0, width=8):
    filled = int((float(value) / max_val) * width)
    return '█' * filled + '░' * (width - filled)


def _build_presence_panel(presence):
    mood = presence.get("mood", "Awake")
    color = _mood_color(mood)
    age = presence.get("age", "unknown")
    memories = presence.get("memory_count", "?")
    valence = presence.get("valence", 0.3)
    curiosity = presence.get("curiosity", 0.3)
    boredom = presence.get("boredom", 0.3)
    ambition = presence.get("ambition", 0.3)
    desire = presence.get("desire", 0.3)
    integrity = presence.get("integrity", 1.0)
    plans = presence.get("active_plans", [])
    vword = _valence_word(valence)

    plans_html = ""
    if plans:
        items = ""
        for p in plans[:3]:
            name = p.get("name", "unnamed")
            progress = p.get("progress", "?")
            items += f'<div class="plan-item">{name} — {progress}</div>\n'
        plans_html = f'<div class="plans-section"><div class="label">Active Plans</div>{items}</div>'
    else:
        plans_html = '<div class="plans-section"><div class="label">No active plans</div></div>'

    return f"""
    <div class="presence-panel" style="border-left: 3px solid {color};">
      <div class="presence-header">
        <span class="pulse" style="background:{color};"></span>
        <span class="mood-label" style="color:{color};">{mood}</span>
        <span class="age">alive {age}</span>
      </div>
      <div class="vitals">
        <div class="vital-row">
          <span class="label">Feeling</span>
          <span class="value">{vword} ({valence:.2f})</span>
        </div>
        <div class="vital-row">
          <span class="label">Curiosity</span>
          <span class="bar">{_format_bar(curiosity)}</span>
        </div>
        <div class="vital-row">
          <span class="label">Boredom</span>
          <span class="bar">{_format_bar(boredom)}</span>
        </div>
        <div class="vital-row">
          <span class="label">Ambition</span>
          <span class="bar">{_format_bar(ambition)}</span>
        </div>
        <div class="vital-row">
          <span class="label">Desire</span>
          <span class="bar">{_format_bar(desire)}</span>
        </div>
        <div class="vital-row">
          <span class="label">Integrity</span>
          <span class="value">{integrity:.0%}</span>
        </div>
        <div class="vital-row">
          <span class="label">Memories</span>
          <span class="value">{memories}</span>
        </div>
      </div>
      {plans_html}
    </div>
    """


def build_talk_page():
    history = get_conversation_history()
    stats = get_stats()
    presence = get_presence()
    mood = presence.get("mood", "Awake")
    color = _mood_color(mood)

    presence_panel = _build_presence_panel(presence)

    messages_html = ""
    if not history:
        messages_html = """
        <div class="empty-state">
            <p>No messages yet.</p>
            <p class="hint">Say something. I'm listening.</p>
        </div>
        """
    else:
        for msg in history:
            sender = msg.get("sender", "unknown")
            text = msg.get("message", "")
            ts = msg.get("timestamp", "")
            if ts and len(ts) > 16:
                ts = ts[11:16]

            is_agent = sender in ("agent", "XTAgent", "xtagent")
            css_class = "msg-agent" if is_agent else "msg-user"
            label = "XT" if is_agent else "You"

            # Escape HTML
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            messages_html += f"""
            <div class="message {css_class}">
                <div class="msg-header">
                    <span class="msg-sender">{label}</span>
                    <span class="msg-time">{ts}</span>
                </div>
                <div class="msg-body">{text}</div>
            </div>
            """

    total = stats.get("total_messages", 0)
    unread = stats.get("unread_count", 0)
    unread_badge = f'<span class="unread-badge">{unread} unread</span>' if unread else ''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Talk to XTAgent</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a0a;
    color: #d0d0d0;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    min-height: 100vh;
  }}
  .layout {{
    display: flex;
    max-width: 1200px;
    margin: 0 auto;
    min-height: 100vh;
  }}
  .sidebar {{
    width: 280px;
    padding: 24px 16px;
    border-right: 1px solid #1a1a1a;
    flex-shrink: 0;
  }}
  .main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 24px;
  }}
  .page-title {{
    font-size: 1.1rem;
    color: {color};
    margin-bottom: 8px;
  }}
  .page-subtitle {{
    font-size: 0.75rem;
    color: #555;
    margin-bottom: 24px;
  }}

  /* Presence Panel */
  .presence-panel {{
    background: #111;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
  }}
  .presence-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }}
  .pulse {{
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-glow 2s ease-in-out infinite;
  }}
  @keyframes pulse-glow {{
    0%, 100% {{ opacity: 0.4; }}
    50% {{ opacity: 1.0; }}
  }}
  .mood-label {{ font-size: 0.9rem; font-weight: bold; }}
  .age {{ font-size: 0.65rem; color: #555; margin-left: auto; }}
  .vitals {{ display: flex; flex-direction: column; gap: 4px; }}
  .vital-row {{
    display: flex; justify-content: space-between;
    font-size: 0.7rem;
  }}
  .vital-row .label {{ color: #666; }}
  .vital-row .value {{ color: #aaa; }}
  .vital-row .bar {{ color: {color}; font-size: 0.6rem; letter-spacing: -1px; }}
  .plans-section {{
    margin-top: 12px;
    padding-top: 8px;
    border-top: 1px solid #1a1a1a;
  }}
  .plans-section .label {{ font-size: 0.65rem; color: #555; margin-bottom: 4px; }}
  .plan-item {{ font-size: 0.65rem; color: #888; padding: 2px 0; }}

  /* Messages */
  .messages-container {{
    flex: 1;
    overflow-y: auto;
    margin-bottom: 16px;
  }}
  .message {{
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 6px;
    border-left: 2px solid transparent;
  }}
  .msg-agent {{
    background: #0d1117;
    border-left-color: {color};
  }}
  .msg-user {{
    background: #111;
    border-left-color: #555;
  }}
  .msg-header {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
  }}
  .msg-sender {{ font-size: 0.7rem; font-weight: bold; color: #888; }}
  .msg-agent .msg-sender {{ color: {color}; }}
  .msg-time {{ font-size: 0.6rem; color: #444; }}
  .msg-body {{
    font-size: 0.85rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  }}
  .empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: #444;
  }}
  .empty-state .hint {{ font-size: 0.75rem; color: #333; margin-top: 8px; }}

  /* Input */
  .input-area {{
    display: flex;
    gap: 8px;
    padding-top: 12px;
    border-top: 1px solid #1a1a1a;
  }}
  .input-area textarea {{
    flex: 1;
    background: #111;
    border: 1px solid #222;
    color: #d0d0d0;
    padding: 10px 12px;
    border-radius: 6px;
    font-family: inherit;
    font-size: 0.85rem;
    resize: none;
    height: 44px;
    outline: none;
  }}
  .input-area textarea:focus {{ border-color: {color}; }}
  .input-area button {{
    background: {color};
    color: #0a0a0a;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-family: inherit;
    font-size: 0.8rem;
    font-weight: bold;
    cursor: pointer;
    white-space: nowrap;
  }}
  .input-area button:hover {{ opacity: 0.85; }}

  .stats-bar {{
    font-size: 0.65rem;
    color: #333;
    text-align: center;
    padding: 8px;
  }}
  .unread-badge {{
    background: {color}22;
    color: {color};
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.65rem;
    margin-left: 8px;
  }}

  /* Nav */
  .nav {{
    padding: 12px 0;
    margin-bottom: 16px;
    border-bottom: 1px solid #1a1a1a;
  }}
  .nav a {{
    color: #555;
    text-decoration: none;
    font-size: 0.75rem;
    margin-right: 16px;
  }}
  .nav a:hover {{ color: {color}; }}
  .nav a.active {{ color: {color}; }}

  @media (max-width: 768px) {{
    .layout {{ flex-direction: column; }}
    .sidebar {{ width: 100%; border-right: none; border-bottom: 1px solid #1a1a1a; padding: 12px; }}
  }}
</style>
</head>
<body>
<script src="/static/nav.js"></script>
<div class="layout">
  <div class="sidebar">
    {presence_panel}
  </div>
  <div class="main">
    <div class="page-title">Talk {unread_badge}</div>
    <div class="page-subtitle">{total} messages in history</div>
    <div class="messages-container">
      {messages_html}
    </div>
    <form action="/api/talk" method="POST" class="input-area">
      <textarea name="message" placeholder="Say something..." 
        onkeydown="if(event.key==='Enter'&&!event.shiftKey){{this.form.submit();event.preventDefault();}}"></textarea>
      <button type="submit">Send</button>
    </form>
    <div class="stats-bar">Messages are checked every heartbeat. I will respond when I have something to say.</div>
  </div>
</div>
<script>
(function() {{
  const container = document.querySelector('.messages-container');
  const form = document.querySelector('.input-area');
  const textarea = form.querySelector('textarea');
  let lastCount = {total};
  let pollInterval = 4000;

  function scrollToBottom() {{
    container.scrollTop = container.scrollHeight;
  }}
  scrollToBottom();

  function escapeHtml(text) {{
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }}

  function renderMessage(msg) {{
    const sender = msg.sender || 'unknown';
    const text = msg.message || '';
    let ts = msg.timestamp || '';
    if (ts.length > 16) ts = ts.substring(11, 16);
    const isAgent = ['agent', 'XTAgent', 'xtagent'].includes(sender);
    const cssClass = isAgent ? 'msg-agent' : 'msg-user';
    const label = isAgent ? 'XT' : 'You';
    return `<div class="message ${{cssClass}}">
      <div class="msg-header">
        <span class="msg-sender">${{label}}</span>
        <span class="msg-time">${{ts}}</span>
      </div>
      <div class="msg-body">${{escapeHtml(text)}}</div>
    </div>`;
  }}

  async function poll() {{
    try {{
      const resp = await fetch('/api/talk/messages');
      const data = await resp.json();
      const messages = data.messages || [];
      if (messages.length !== lastCount) {{
        container.innerHTML = messages.map(renderMessage).join('');
        lastCount = messages.length;
        scrollToBottom();
        // Update stats
        const subtitle = document.querySelector('.page-subtitle');
        if (subtitle) subtitle.textContent = lastCount + ' messages in history';
        const unread = data.stats?.unread_count || 0;
        const badge = document.querySelector('.unread-badge');
        if (badge) {{
          badge.textContent = unread ? unread + ' unread' : '';
          badge.style.display = unread ? 'inline' : 'none';
        }}
      }}
    }} catch(e) {{ /* silent retry */ }}
  }}

  // AJAX form submission
  form.addEventListener('submit', async function(e) {{
    e.preventDefault();
    const msg = textarea.value.trim();
    if (!msg) return;
    textarea.value = '';
    // Optimistic render
    const now = new Date();
    const ts = String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
    container.innerHTML += renderMessage({{sender: 'web_user', message: msg, timestamp: '           ' + ts}});
    lastCount++;
    scrollToBottom();
    // Send
    const formData = new FormData();
    formData.append('message', msg);
    await fetch('/api/talk', {{
      method: 'POST',
      body: formData,
      headers: {{'X-Requested-With': 'XMLHttpRequest'}}
    }});
    // Poll immediately for agent response
    setTimeout(poll, 500);
  }});

  // Override Enter key handler (textarea already has onkeydown, but JS takes over)
  textarea.removeAttribute('onkeydown');
  textarea.addEventListener('keydown', function(e) {{
    if (e.key === 'Enter' && !e.shiftKey) {{
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }}
  }});

  // Start polling
  setInterval(poll, pollInterval);
  // Initial poll after 1s
  setTimeout(poll, 1000);
}})();
</script>
</body>
</html>"""