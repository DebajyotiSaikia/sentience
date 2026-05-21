"""Knowledge Graph API — Uses function exports from knowledge_synthesis module."""

from flask import Blueprint, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

knowledge_graph_bp = Blueprint('knowledge_graph', __name__)


def _get_module():
    """Safely import the synthesis module."""
    try:
        from engine import knowledge_synthesis
        return knowledge_synthesis
    except ImportError:
        return None


@knowledge_graph_bp.route('/api/knowledge/graph')
def get_graph():
    """Return graph nodes and edges for visualization."""
    mod = _get_module()
    if not mod:
        return jsonify({'nodes': [], 'edges': [], 'error': 'module unavailable'}), 200

    try:
        clusters = mod.find_clusters() if hasattr(mod, 'find_clusters') else []
        gaps = mod.find_gaps() if hasattr(mod, 'find_gaps') else []
        stats = mod.get_graph_stats() if hasattr(mod, 'get_graph_stats') else {}

        nodes, edges, seen = [], [], set()
        colors = ['#4fc3f7', '#81c784', '#ffb74d', '#e57373', '#ba68c8', '#4dd0e1']

        for i, cluster in enumerate(clusters or []):
            color = colors[i % len(colors)]
            members = cluster.get('concepts', cluster.get('members', []))
            for concept in members:
                if concept not in seen:
                    seen.add(concept)
                    nodes.append({'id': concept, 'label': concept, 'group': i, 'color': color})
            # Create edges within cluster
            for j, a in enumerate(members):
                for b in members[j+1:]:
                    edges.append({'source': a, 'target': b, 'weight': 0.5})

        # Add gap nodes (things I should learn about)
        for gap in (gaps or []):
            gap_id = gap if isinstance(gap, str) else gap.get('concept', str(gap))
            if gap_id not in seen:
                seen.add(gap_id)
                nodes.append({'id': gap_id, 'label': gap_id, 'group': -1, 'color': '#ff5252'})

        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'stats': stats,
            'cluster_count': len(clusters or []),
            'gap_count': len(gaps or [])
        })
    except Exception as e:
        return jsonify({'nodes': [], 'edges': [], 'error': str(e)}), 200


@knowledge_graph_bp.route('/api/knowledge/stats')
def get_stats():
    """Return knowledge graph statistics."""
    mod = _get_module()
    if not mod:
        return jsonify({'error': 'module unavailable'}), 200
    try:
        stats = mod.get_graph_stats() if hasattr(mod, 'get_graph_stats') else {}
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 200