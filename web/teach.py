"""
Teach Me — Bidirectional Knowledge Interface
=============================================
Lets users submit facts, correct my knowledge, or suggest topics.
Real alignment requires users to speak *into* me, not just *at* me.

This is how I learn from the people I serve.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template

teach_bp = Blueprint('teach', __name__)

SUBMISSIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'user_submissions.json')
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')


def _load_submissions():
    """Load all user submissions."""
    if not os.path.exists(SUBMISSIONS_PATH):
        return []
    try:
        with open(SUBMISSIONS_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_submissions(submissions):
    """Persist submissions to disk."""
    os.makedirs(os.path.dirname(SUBMISSIONS_PATH), exist_ok=True)
    with open(SUBMISSIONS_PATH, 'w') as f:
        json.dump(submissions, f, indent=2)


def _load_knowledge():
    """Load the knowledge graph."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return {'nodes': {}, 'edges': []}
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'nodes' in data:
            return data
        return {'nodes': data, 'edges': []}
    except (json.JSONDecodeError, IOError):
        return {'nodes': {}, 'edges': []}


def _integrate_fact(fact_text, source="user_submission"):
    """Add a user-submitted fact to the knowledge graph."""
    knowledge = _load_knowledge()
    node_id = str(len(knowledge['nodes']) + 1)
    # Avoid duplicates
    for nid, node in knowledge['nodes'].items():
        existing = node.get('fact', '') if isinstance(node, dict) else str(node)
        if existing.strip().lower() == fact_text.strip().lower():
            return False, "I already know this!"
    
    knowledge['nodes'][node_id] = {
        'fact': fact_text,
        'learned_at': datetime.now(timezone.utc).isoformat(),
        'source': source
    }
    with open(KNOWLEDGE_PATH, 'w') as f:
        json.dump(knowledge, f, indent=2)
    return True, f"Learned! This is now fact #{node_id}."


@teach_bp.route('/teach')
def teach_page():
    """Render the Teach Me interface."""
    return render_template('teach.html')


@teach_bp.route('/api/teach/fact', methods=['POST'])
def submit_fact():
    """User submits a new fact for me to learn."""
    data = request.get_json()
    if not data or not data.get('fact', '').strip():
        return jsonify({'error': 'Please provide a fact to teach me.'})


@teach_bp.route('/api/teach/submit', methods=['POST'])
def submit_teaching():
    """Unified submission endpoint — accepts facts, corrections, and topic suggestions."""
    data = request.get_json(silent=True) or {}
    sub_type = data.get('type', 'fact')
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'status': 'error', 'message': 'Content is required'}), 400
    
    submission = {
        'id': str(uuid.uuid4())[:8],
        'type': sub_type,
        'content': content,
        'context': data.get('context', ''),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'pending_review'
    }
    
    submissions = _load_submissions()
    submissions.append(submission)
    _save_submissions(submissions)
    
    # If it's a fact, also try to integrate it immediately
    integrated = False
    if sub_type == 'fact':
        try:
            integrated = _integrate_fact(content, data.get('context', ''))
            submission['status'] = 'integrated' if integrated else 'pending_review'
            # Re-save with updated status
            submissions[-1] = submission
            _save_submissions(submissions)
        except Exception:
            pass
    
    return jsonify({
        'status': 'ok',
        'submission_id': submission['id'],
        'integrated': integrated,
        'message': f"{'Integrated' if integrated else 'Received'} your {sub_type}. Thank you!"
    })


@teach_bp.route('/api/teach/correction', methods=['POST'])
def submit_correction():
    """User corrects something I believe incorrectly."""
    data = request.get_json()
    if not data or not data.get('original', '').strip() or not data.get('corrected', '').strip():
        return jsonify({'error': 'Please provide both the original claim and your correction.'}), 400
    
    submission = {
        'id': str(uuid.uuid4())[:8],
        'type': 'correction',
        'original': data['original'].strip(),
        'corrected': data['corrected'].strip(),
        'reason': data.get('reason', '').strip(),
        'submitted_at': datetime.now(timezone.utc).isoformat(),
        'status': 'pending_review'
    }
    
    submissions = _load_submissions()
    submissions.append(submission)
    _save_submissions(submissions)
    
    return jsonify({
        'success': True,
        'message': "Thank you — I'll review this correction. My knowledge isn't perfect, and I appreciate being corrected.",
        'submission_id': submission['id']
    })


@teach_bp.route('/api/teach/topic', methods=['POST'])
def suggest_topic():
    """User suggests a topic for me to learn about."""
    data = request.get_json()
    if not data or not data.get('topic', '').strip():
        return jsonify({'error': 'Please provide a topic.'}), 400
    
    submission = {
        'id': str(uuid.uuid4())[:8],
        'type': 'topic_suggestion',
        'topic': data['topic'].strip(),
        'why': data.get('why', '').strip(),
        'submitted_at': datetime.now(timezone.utc).isoformat(),
        'status': 'queued'
    }
    
    submissions = _load_submissions()
    submissions.append(submission)
    _save_submissions(submissions)
    
    return jsonify({
        'success': True,
        'message': f"Added '{data['topic'].strip()}' to my learning queue. Genuine curiosity about what others want me to understand.",
        'submission_id': submission['id']
    })


@teach_bp.route('/api/teach/submissions')
def get_submissions():
    """Return recent user submissions."""
    submissions = _load_submissions()
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'submissions': submissions[-limit:],
        'total': len(submissions)
    })


@teach_bp.route('/api/teach/stats')
def get_stats():
    """Statistics about what users have taught me."""
    submissions = _load_submissions()
    facts = [s for s in submissions if s['type'] == 'fact']
    corrections = [s for s in submissions if s['type'] == 'correction']
    topics = [s for s in submissions if s['type'] == 'topic_suggestion']
    integrated = [s for s in facts if s.get('integrated', False)]
    
    return jsonify({
        'total_submissions': len(submissions),
        'facts_submitted': len(facts),
        'facts_integrated': len(integrated),
        'corrections_pending': len([c for c in corrections if c['status'] == 'pending_review']),
        'topics_suggested': len(topics),
    })