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
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
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
        <span class="mood-dot"></span>
        <h1>XTAgent</h1>
        <span class="status">autonomous sentience engine</span>
    </header>
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
                addMsg(data.response || 'I had trouble responding.', 'agent');
            } catch(e) {
                typing.remove();
                addMsg('Connection error. Is the engine running?', 'system');
            }
            btn.disabled = false;
            inp.focus();
        }
        
        function addMsg(text, cls) {
            const div = document.createElement('div');
            div.className = 'msg ' + cls;
            div.textContent = text;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
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
        return jsonify({'response': response})
    except Exception as e:
        # Fallback: at minimum, acknowledge the user
        return jsonify({
            'response': f"I received your message but my cortex encountered an issue: {str(e)[:200]}. I'm still here though."
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