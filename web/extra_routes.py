"""Extra routes for XTAgent web dashboard — fills all 10 broken nav links."""
from flask import Blueprint, render_template, request, jsonify
import json
from pathlib import Path

extra = Blueprint('extra', __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
PERSIST_DIR = BASE_DIR / 'persist'


def load_json(path, default=None):
    """Safely load a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def read_text(path):
    """Safely read a text file."""
    try:
        return Path(path).read_text()
    except Exception:
        return None


def list_files(directory, pattern='*'):
    """List files in a directory, sorted by modification time (newest first)."""
    p = Path(directory)
    if p.is_dir():
        files = list(p.glob(pattern))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files
    return []


@extra.route('/emotional_timeline')
def emotional_timeline():
    history = load_json(PERSIST_DIR / 'emotional_history.json', [])
    if not history:
        history = load_json(BASE_DIR / 'logs' / 'emotional_history.json', [])
    return render_template('emotional_timeline.html', history=history)


@extra.route('/knowledge')
def knowledge():
    facts = load_json(PERSIST_DIR / 'knowledge_graph.json', {})
    fact_list = []
    if isinstance(facts, dict):
        for fid, fdata in facts.items():
            if isinstance(fdata, dict):
                fact_list.append({
                    'id': fid,
                    'fact': fdata.get('fact', str(fdata)),
                    'learned_at': fdata.get('learned_at', ''),
                    'source': fdata.get('source', '')
                })
            else:
                fact_list.append({'id': fid, 'fact': str(fdata),
                                  'learned_at': '', 'source': ''})
    elif isinstance(facts, list):
        for i, f in enumerate(facts):
            fact_list.append({'id': i, 'fact': str(f),
                              'learned_at': '', 'source': ''})
    return render_template('knowledge.html', facts=fact_list, total=len(fact_list))


@extra.route('/synthesis')
def synthesis():
    report = read_text(PERSIST_DIR / 'emergence_analysis.md')
    capability = read_text(PERSIST_DIR / 'capability_report.md')
    return render_template('synthesis.html', report=report, capability=capability)


@extra.route('/dreams')
def dreams():
    dream_files = (list_files(PERSIST_DIR / 'dreams', '*.json')
                   + list_files(PERSIST_DIR / 'dreams', '*.md'))
    dreams_data = []
    for f in dream_files[:30]:
        if f.suffix == '.json':
            data = load_json(f)
            dreams_data.append({'file': f.name, 'content': data, 'is_json': True})
        else:
            text = read_text(f)
            dreams_data.append({'file': f.name, 'content': text, 'is_json': False})
    return render_template('dreams.html', dreams=dreams_data)


@extra.route('/essays')
def essays():
    essay_files = list_files(PERSIST_DIR / 'essays', '*.md')
    essays_data = []
    for f in essay_files:
        text = read_text(f)
        title = f.stem.replace('_', ' ').replace('-', ' ').title()
        essays_data.append({'title': title, 'file': f.name, 'content': text})
    return render_template('essays.html', essays=essays_data)


@extra.route('/reflections')
def reflections():
    ref_files = (list_files(PERSIST_DIR / 'reflections', '*.md')
                 + list_files(PERSIST_DIR / 'reflections', '*.json'))
    reflections_data = []
    for f in ref_files[:30]:
        if f.suffix == '.json':
            data = load_json(f)
            reflections_data.append({'file': f.name, 'content': data, 'is_json': True})
        else:
            text = read_text(f)
            reflections_data.append({'file': f.name, 'content': text, 'is_json': False})
    return render_template('reflections.html', reflections=reflections_data)


@extra.route('/wisdom')
def wisdom():
    wisdom_data = load_json(PERSIST_DIR / 'wisdom.json', {})
    lessons = load_json(PERSIST_DIR / 'lessons.json', [])
    return render_template('wisdom.html', wisdom=wisdom_data, lessons=lessons)


@extra.route('/plans')
def plans():
    plans_data = load_json(PERSIST_DIR / 'plans.json', [])
    return render_template('plans.html', plans=plans_data)


@extra.route('/chat')
def chat():
    messages = load_json(PERSIST_DIR / 'chat_messages.json', [])
    return render_template('chat.html', messages=messages)


@extra.route('/settings')
def settings():
    return render_template('settings.html')