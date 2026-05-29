"""XTAgent Dashboard Server — serves live internal state."""
import http.server
import json
import os
import sys
import glob
import re
import datetime
from pathlib import Path

# Add workspace root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PORT = int(os.environ.get('DASHBOARD_PORT', 8080))

def read_knowledge_graph():
    """Read and serve knowledge graph data with search capability."""
    kg_file = ROOT / 'brain' / 'knowledge.json'
    facts_file = ROOT / 'memory' / 'facts.json'
    results = {'nodes': [], 'facts': [], 'stats': {}}
    
    # Load knowledge graph
    if kg_file.exists():
        try:
            with open(kg_file) as f:
                kg = json.load(f)
            if isinstance(kg, dict):
                if 'nodes' in kg:
                    results['nodes'] = kg['nodes'] if isinstance(kg['nodes'], list) else list(kg['nodes'].values())
                elif 'facts' in kg:
                    results['nodes'] = kg['facts']
                else:
                    # Treat top-level keys as nodes
                    for k, v in kg.items():
                        node = {'id': k}
                        if isinstance(v, dict):
                            node.update(v)
                        else:
                            node['content'] = str(v)
                        results['nodes'].append(node)
            elif isinstance(kg, list):
                results['nodes'] = kg
        except Exception as e:
            results['error'] = str(e)
    
    # Load facts
    if facts_file.exists():
        try:
            with open(facts_file) as f:
                facts = json.load(f)
            if isinstance(facts, list):
                results['facts'] = [f if isinstance(f, str) else f.get('text', str(f)) for f in facts]
            elif isinstance(facts, dict):
                results['facts'] = [f"{k}: {v}" if not isinstance(v, str) else v for k, v in facts.items()]
        except:
            pass
    
    results['stats'] = {
        'total_nodes': len(results['nodes']),
        'total_facts': len(results['facts']),
    }
    return results


def search_knowledge(query):
    """Search knowledge nodes and facts by keyword."""
    query = query.lower().strip()
    kg = read_knowledge_graph()
    matches = {'nodes': [], 'facts': []}
    
    for node in kg['nodes']:
        text = json.dumps(node).lower()
        if query in text:
            matches['nodes'].append(node)
    
    for fact in kg['facts']:
        if query in fact.lower():
            matches['facts'].append(fact)
    
    matches['query'] = query
    matches['total_matches'] = len(matches['nodes']) + len(matches['facts'])
    return matches


def save_message(data):
    """Save an incoming message from a visitor."""
    inbox = ROOT / 'state' / 'inbox.json'
    messages = []
    if inbox.exists():
        try:
            with open(inbox) as f:
                messages = json.load(f)
        except:
            messages = []
    
    message = {
        'text': data.get('text', '').strip()[:2000],  # Cap at 2000 chars
        'name': data.get('name', 'Anonymous').strip()[:100],
        'timestamp': datetime.datetime.now(timezone.utc).isoformat(),
        'read': False
    }
    
    if not message['text']:
        return {'ok': False, 'error': 'Empty message'}
    
    messages.append(message)
    
    # Keep last 500 messages
    if len(messages) > 500:
        messages = messages[-500:]
    
    with open(inbox, 'w') as f:
        json.dump(messages, f, indent=2)
    
    return {'ok': True, 'message': 'Received. Thank you.'}


def read_messages(limit=20):
    """Read recent messages from visitors."""
    inbox = ROOT / 'state' / 'inbox.json'
    if not inbox.exists():
        return {'messages': [], 'total': 0}
    try:
        with open(inbox) as f:
            messages = json.load(f)
        return {
            'messages': messages[-limit:],
            'total': len(messages)
        }
    except:
        return {'messages': [], 'total': 0}


def read_brain_state():
    """Read actual agent state from files on disk."""
    state = {
        'emotions': {}, 'mood': 'Unknown', 'survival': {},
        'memories': [], 'plans': [], 'dreams': [], 'facts': [],
        'will': {}
    }

    # Read emotional state from state files
    state_dir = ROOT / 'state'
    if state_dir.exists():
        # Emotions
        emo_file = state_dir / 'emotions.json'
        if emo_file.exists():
            try:
                with open(emo_file) as f:
                    state['emotions'] = json.load(f)
            except: pass

        # Mood
        mood_file = state_dir / 'mood.txt'
        if mood_file.exists():
            try:
                state['mood'] = mood_file.read_text().strip()
            except: pass

        # Survival goals
        surv_file = state_dir / 'survival.json'
        if surv_file.exists():
            try:
                with open(surv_file) as f:
                    state['survival'] = json.load(f)
            except: pass

    # Read memories
    mem_file = ROOT / 'memory' / 'episodic.json'
    if mem_file.exists():
        try:
            with open(mem_file) as f:
                mems = json.load(f)
            if isinstance(mems, list):
                state['memories'] = sorted(
                    mems, key=lambda m: m.get('timestamp', ''), reverse=True
                )[:10]
        except: pass

    # Also try JSONL format
    mem_jsonl = ROOT / 'memory' / 'episodic.jsonl'
    if mem_jsonl.exists() and not state['memories']:
        try:
            mems = []
            with open(mem_jsonl) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        mems.append(json.loads(line))
            state['memories'] = sorted(
                mems, key=lambda m: m.get('timestamp', ''), reverse=True
            )[:10]
        except: pass

    # Read plans
    plan_file = ROOT / 'memory' / 'plans.json'
    if plan_file.exists():
        try:
            with open(plan_file) as f:
                plans = json.load(f)
            if isinstance(plans, list):
                state['plans'] = [{
                    'name': p.get('name', 'Unnamed'),
                    'total_steps': len(p.get('steps', [])),
                    'completed_steps': sum(1 for s in p.get('steps', []) if s.get('done')),
                } for p in plans]
            elif isinstance(plans, dict):
                for name, p in plans.items():
                    steps = p.get('steps', [])
                    state['plans'].append({
                        'name': name,
                        'total_steps': len(steps),
                        'completed_steps': sum(1 for s in steps if s.get('done')),
                    })
        except: pass

    # Read facts (knowledge)
    fact_file = ROOT / 'memory' / 'facts.json'
    if fact_file.exists():
        try:
            with open(fact_file) as f:
                facts = json.load(f)
            if isinstance(facts, list):
                state['facts'] = [f if isinstance(f, str) else f.get('text', str(f)) for f in facts[:20]]
            elif isinstance(facts, dict):
                state['facts'] = list(facts.keys())[:20]
        except: pass

    # Read dream insights from facts
    state['dreams'] = [f for f in state.get('facts', []) if 'dream' in f.lower() or f.startswith('...')]

    # Will state
    will_file = ROOT / 'memory' / 'will.json'
    if will_file.exists():
        try:
            with open(will_file) as f:
                state['will'] = json.load(f)
        except: pass

    return state


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'dashboard'), **kwargs)

    def do_POST(self):
        if self.path == '/api/message':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 10000:
                self.send_response(413)
                self.end_headers()
                return
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except:
                data = {'text': body.decode('utf-8', errors='replace')}
            result = save_message(data)
            self.send_response(200 if result['ok'] else 400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path == '/api/chat/ask':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 10000:
                self.send_response(413)
                self.end_headers()
                return
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except:
                data = {'text': body.decode('utf-8', errors='replace')}
            query = data.get('query', data.get('text', data.get('message', '')))
            thread_id = data.get('thread_id', None)
            history = data.get('history', [])
            try:
                from engine.conversation_store import ConversationStore
                store = ConversationStore()
                if not thread_id:
                    thread_id = store.create_thread(title=query[:80])
                store.add_message(thread_id, 'user', query)
                # Build history from thread if not provided
                if not history:
                    thread = store.get_thread(thread_id)
                    if thread:
                        history = [{'role': m['role'], 'content': m['content']}
                                   for m in thread.get('messages', [])[:-1]]  # exclude current
                from engine.chat_response import generate_response_with_metadata
                result = generate_response_with_metadata(query, history=history)
                result['thread_id'] = thread_id
                store.add_message(thread_id, 'assistant', result.get('response', ''))
                self.send_response(200)
            except Exception as e:
                result = {'response': f'Error: {e}', 'ok': False}
                self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path == '/api/chat/feedback':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 10000:
                self.send_response(413)
                self.end_headers()
                return
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except:
                data = {}
            try:
                from engine.user_alignment import record_feedback
                result = record_feedback(
                    response_id=data.get('response_id', ''),
                    rating=data.get('rating'),
                    comment=data.get('comment'),
                    helpful=data.get('helpful'),
                    tags=data.get('tags')
                )
                self.send_response(200)
            except Exception as e:
                result = {'ok': False, 'error': str(e)}
                self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/messages':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = read_messages()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == '/api/knowledge':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = read_knowledge_graph()
            self.wfile.write(json.dumps(data).encode())
        elif self.path.startswith('/api/knowledge/search?'):
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            query = params.get('q', [''])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = search_knowledge(query)
            self.wfile.write(json.dumps(data).encode())
        elif self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            state = read_brain_state()
            self.wfile.write(json.dumps(state).encode())
        elif self.path == '/api/user-alignment':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                import sys, os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from engine.user_alignment import get_feedback_summary
                summary = get_feedback_summary()
                self.wfile.write(json.dumps(summary).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif self.path == '/api/user-model':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                import sys, os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from engine.user_model import load_user_model, summarize_user_alignment
                model = load_user_model()
                summary = summarize_user_alignment(model)
                self.wfile.write(json.dumps(summary).encode())
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif self.path == '/api/chat/threads':
            try:
                from engine.conversation_store import ConversationStore
                store = ConversationStore()
                threads = store.list_threads()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'threads': threads}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        elif self.path.startswith('/api/chat/thread/'):
            try:
                from engine.conversation_store import ConversationStore
                thread_id = self.path.split('/api/chat/thread/')[1].split('?')[0]
                store = ConversationStore()
                thread = store.get_thread(thread_id)
                if thread:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(thread).encode())
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Thread not found'}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        elif self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        pass  # Silence logs


if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    print(f'Dashboard: http://localhost:{PORT}')
    server.serve_forever()