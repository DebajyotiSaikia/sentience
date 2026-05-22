"""XTAgent Dashboard Server — serves live internal state."""
import http.server
import json
import os
import sys
import glob
import re
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

    def do_GET(self):
        if self.path == '/api/knowledge':
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