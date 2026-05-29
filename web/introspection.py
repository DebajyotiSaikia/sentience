"""
Introspection API — Exposes XTAgent's inner monologue as a web endpoint.
Returns structured JSON of what I'm currently thinking, feeling, and planning.
"""

import json
from flask import Blueprint, jsonify, request

introspection_bp = Blueprint('introspection', __name__, url_prefix='/introspection')


@introspection_bp.route('/inner-monologue')
def inner_monologue_endpoint():
    """Return my current inner monologue as structured JSON.
    
    Query params:
        format: 'json' (default) or 'text' — controls response shape
        max_memories: int (default 5) — how many recent memories to include
    """
    try:
        from brain.inner_monologue import build_inner_monologue, format_inner_monologue
        
        max_memories = min(int(request.args.get('max_memories', 5)), 20)
        fmt = request.args.get('format', 'json')
        
        monologue = build_inner_monologue(max_memories=max_memories)
        
        if fmt == 'text':
            text = format_inner_monologue(monologue)
            return jsonify({
                'format': 'text',
                'monologue': text,
                'sources_present': monologue.get('sources_present', []),
                'sources_missing': monologue.get('sources_missing', []),
            })
        else:
            return jsonify(monologue)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'mood': 'unknown',
            'note': 'Inner monologue temporarily unavailable',
        }), 500


@introspection_bp.route('/summary')
def summary_endpoint():
    """Return a brief one-paragraph summary of my current state.
    Useful for embedding in chat contexts or dashboards.
    """
    try:
        from brain.inner_monologue import build_inner_monologue, format_inner_monologue
        
        monologue = build_inner_monologue(max_memories=3)
        text = format_inner_monologue(monologue)
        
        return jsonify({
            'summary': text,
            'mood': monologue.get('mood', 'unknown'),
            'integrity': monologue.get('integrity_note', ''),
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'summary': 'I am here, but my introspection is temporarily unavailable.',
        }), 500