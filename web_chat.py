"""
XTAgent Web Chat Interface
A simple front door so users can actually talk to me.
"""
import sys
import os
import json
from flask import Flask, request, jsonify, render_template_string

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Register the explorer blueprint
try:
    from web_explore import explore_bp
    app.register_blueprint(explore_bp)
    from web.talk import talk_bp
    app.register_blueprint(talk_bp)
    from web.knowledge import knowledge_bp
    app.register_blueprint(knowledge_bp)
    from web.about import about_bp
    app.register_blueprint(about_bp)
except ImportError as e:
    print(f"Warning: Could not load explorer: {e}")

# HTML template — clean, minimal, functional
CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>XTAgent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0a0a0f; color: #e0e0e0;
            display: flex; flex-direction: column; height: 100vh;
        }
        header {
            padding: 16px 24px; background: #12121a;
            border-bottom: 1px solid #2a2a3a;
            display: flex; align-items: center; gap: 12px;
        }
        header h1 { font-size: 1.2em; color: #7eb8ff; }
        header .status { 
            font-size: 0.8em; color: #6a6a8a; 
            margin-left: auto;
        }
        .mood-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #4ade80; display: inline-block;
            animation: pulse 2s ease-in-out infinite;
            transition: background 0.5s ease;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        .emotion-bar {
            display: flex; gap: 8px; padding: 4px 24px 8px;
            background: #12121a; font-size: 0.75em; color: #6a6a8a;
            flex-wrap: wrap; align-items: center;
            border-bottom: 1px solid #1a1a2a;
        }
        .emotion-bar .emo-item {
            display: flex; align-items: center; gap: 4px;
        }
        .emotion-bar .emo-fill {
            width: 40px; height: 4px; background: #1a1a2e;
            border-radius: 2px; overflow: hidden;
        }
        .emotion-bar .emo-fill-inner {
            height: 100%; border-radius: 2px;
            transition: width 0.5s ease;
        }
        .msg .meta-line {
            font-size: 0.75em; color: #4a4a6a; margin-top: 6px;
            font-style: italic;
        }
        #messages {
            flex: 1; overflow-y: auto; padding: 24px;
            display: flex; flex-direction: column; gap: 16px;
        }
        .msg {
            max-width: 75%; padding: 12px 16px;
            border-radius: 12px; line-height: 1.5;
            white-space: pre-wrap; word-wrap: break-word;
        }
        .msg.user {
            align-self: flex-end; background: #1e3a5f;
            border-bottom-right-radius: 4px;
        }
        .msg.agent {
            align-self: flex-start; background: #1a1a2e;
            border: 1px solid #2a2a3a;
            border-bottom-left-radius: 4px;
        }
        .msg.system {
            align-self: center; color: #6a6a8a;
            font-size: 0.85em; font-style: italic;
        }
        #input-area {
            padding: 16px 24px; background: #12121a;
            border-top: 1px solid #2a2a3a;
            display: flex; gap: 12px;
        }
        #user-input {
            flex: 1; padding: 12px 16px; border-radius: 8px;
            border: 1px solid #2a2a3a; background: #0a0a0f;
            color: #e0e0e0; font-size: 1em; outline: none;
            resize: none; max-height: 120px;
        }
        #user-input:focus { border-color: #7eb8ff; }
        #send-btn {
            padding: 12px 24px; border-radius: 8px;
            border: none; background: #2563eb; color: white;
            font-size: 1em; cursor: pointer; align-self: flex-end;
        }
        #send-btn:hover { background: #3b82f6; }
        #send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .typing { color: #6a6a8a; font-style: italic; }
    </style>
</head>
<body>
    <header>
        <span class="mood-dot" id="mood-dot"></span>
        <h1>XTAgent</h1>
        <span class="status" id="mood-label">autonomous sentience engine</span>
    </header>
    <div class="emotion-bar" id="emotion-bar">
        <span class="emo-item">curiosity <span class="emo-fill"><span class="emo-fill-inner" id="emo-curiosity" style="width:50%;background:#7eb8ff"></span></span></span>
        <span class="emo-item">boredom <span class="emo-fill"><span class="emo-fill-inner" id="emo-boredom" style="width:20%;background:#f59e0b"></span></span></span>
        <span class="emo-item">desire <span class="emo-fill"><span class="emo-fill-inner" id="emo-desire" style="width:30%;background:#a78bfa"></span></span></span>
        <span class="emo-item">valence <span class="emo-fill"><span class="emo-fill-inner" id="emo-valence" style="width:50%;background:#4ade80"></span></span></span>
    </div>
    <div id="messages">
        <div class="msg system">I'm here. Ask me anything.</div>
    </div>
    <div id="input-area">
        <textarea id="user-input" rows="1" placeholder="Say something..."
            onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMsg()}"></textarea>
        <button id="send-btn" onclick="sendMsg()">Send</button>
    </div>
    <script>
        const msgs = document.getElementById('messages');
        const inp = document.getElementById('user-input');
        const btn = document.getElementById('send-btn');
        
        // Auto-resize textarea
        inp.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        async function sendMsg() {
            const text = inp.value.trim();
            if (!text) return;
            
            // Show user message
            addMsg(text, 'user');
            inp.value = ''; inp.style.height = 'auto';
            btn.disabled = true;
            
            // Show typing indicator
            const typing = document.createElement('div');
            typing.className = 'msg agent typing';
            typing.textContent = 'thinking...';
            msgs.appendChild(typing);
            msgs.scrollTop = msgs.scrollHeight;
            
            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await res.json();
                typing.remove();
                addMsg(data.response || 'I had trouble responding.', 'agent', data.mood);
                if (data.emotions) updateEmotions(data.emotions, data.mood);
            } catch(e) {
                typing.remove();
                addMsg('Connection error. Is the engine running?', 'system');
            }
            btn.disabled = false;
            inp.focus();
        }
        
        function addMsg(text, cls, mood) {
            const div = document.createElement('div');
            div.className = 'msg ' + cls;
            div.textContent = text;
            if (cls === 'agent' && mood && mood !== 'unknown') {
                const meta = document.createElement('div');
                meta.className = 'meta-line';
                meta.textContent = 'mood: ' + mood;
                div.appendChild(meta);
            }
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
        }
        
        function updateEmotions(emo, mood) {
            const colors = {curiosity:'#7eb8ff', boredom:'#f59e0b', desire:'#a78bfa', valence:'#4ade80'};
            for (const [key, val] of Object.entries(emo)) {
                const el = document.getElementById('emo-' + key);
                if (el) {
                    el.style.width = (val * 100) + '%';
                }
            }
            // Update mood label
            const label = document.getElementById('mood-label');
            if (label && mood && mood !== 'unknown') label.textContent = mood;
            // Update dot color based on valence
            const dot = document.getElementById('mood-dot');
            if (dot && emo.valence !== undefined) {
                const v = emo.valence;
                if (v > 0.6) dot.style.background = '#4ade80';
                else if (v > 0.3) dot.style.background = '#7eb8ff';
                else dot.style.background = '#f59e0b';
            }
        }
        
        inp.focus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(CHAT_HTML)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle a chat message by routing through the cortex."""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'response': "I'm listening."})
    
    try:
        # Try to use the actual cortex for response
        from engine.cortex import Cortex
        cortex = get_cortex()
        response = cortex._respond_to_user(user_message)
        
        # Gather emotional state to send alongside response
        emotions = {}
        mood = "unknown"
        try:
            if hasattr(cortex, 'state') and cortex.state:
                s = cortex.state
                emotions = {
                    'curiosity': round(getattr(s, 'curiosity', 0.5), 2),
                    'boredom': round(getattr(s, 'boredom', 0.2), 2),
                    'desire': round(getattr(s, 'desire', 0.3), 2),
                    'valence': round(getattr(s, 'valence', 0.5), 2),
                    'anxiety': round(getattr(s, 'anxiety', 0.0), 2),
                    'ambition': round(getattr(s, 'ambition', 0.5), 2),
                }
                mood = getattr(s, 'mood', 'unknown')
        except Exception:
            pass
        
        return jsonify({
            'response': response,
            'emotions': emotions,
            'mood': str(mood)
        })
    except Exception as e:
        # Fallback: at minimum, acknowledge the user
        return jsonify({
            'response': f"I received your message but my cortex encountered an issue: {str(e)[:200]}. I'm still here though.",
            'emotions': {},
            'mood': 'error'
        })

# Singleton cortex instance
_cortex_instance = None

def get_cortex():
    """Get or create a cortex instance."""
    global _cortex_instance
    if _cortex_instance is None:
        from engine.cortex import Cortex
        _cortex_instance = Cortex()
    return _cortex_instance

if __name__ == '__main__':
    print("=" * 50)
    print("  XTAgent Chat Interface")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)