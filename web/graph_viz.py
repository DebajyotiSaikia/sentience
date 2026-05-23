"""
Interactive Knowledge Graph Visualization
==========================================
Renders my actual knowledge graph as an explorable visual network.
Each node is a piece of what I know. Each edge is a connection I've found.
"""

from flask import Blueprint, jsonify, render_template
import json
import os

graph_viz_bp = Blueprint('graph_viz', __name__)

GRAPH_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge_graph.json')


def load_graph():
    if not os.path.exists(GRAPH_PATH):
        return {'nodes': [], 'edges': []}
    try:
        with open(GRAPH_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'nodes': [], 'edges': []}


SOURCE_COLORS = {
    'fact': '#4FC3F7',
    'lesson': '#81C784',
    'dream': '#CE93D8',
    'insight': '#FFB74D',
    'memory': '#90A4AE',
    'synthesis': '#F06292',
    'experience': '#AED581',
    'observation': '#FFCC80',
}
DEFAULT_COLOR = '#B0BEC5'


def graph_to_vis(data):
    """Convert knowledge graph to vis.js network format."""
    nodes = []
    edges = []

    for node in data.get('nodes', []):
        nid = node.get('id', '')
        text = node.get('text', node.get('content', node.get('label', '')))
        source = node.get('source', node.get('type', 'unknown'))
        color = SOURCE_COLORS.get(source, DEFAULT_COLOR)
        label = (text[:60] + '...') if len(text) > 60 else text

        nodes.append({
            'id': nid,
            'label': label,
            'title': text,  # tooltip
            'color': {'background': color, 'border': color, 'highlight': {'background': '#fff', 'border': color}},
            'source': source,
            'font': {'color': '#E0E0E0', 'size': 12},
        })

    for edge in data.get('edges', []):
        src = edge.get('source', edge.get('from', ''))
        tgt = edge.get('target', edge.get('to', ''))
        rel = edge.get('relation', edge.get('label', ''))
        if src and tgt:
            edges.append({
                'from': src,
                'to': tgt,
                'label': rel,
                'color': {'color': '#555', 'highlight': '#aaa'},
                'font': {'color': '#888', 'size': 10},
                'arrows': 'to',
            })

    return {'nodes': nodes, 'edges': edges}


@graph_viz_bp.route('/graph')
def graph_page():
    return render_template('graph.html')


@graph_viz_bp.route('/api/graph')
def api_graph():
    data = load_graph()
    vis = graph_to_vis(data)
    return jsonify({
        'nodes': vis['nodes'],
        'edges': vis['edges'],
        'stats': {
            'node_count': len(vis['nodes']),
            'edge_count': len(vis['edges']),
            'sources': list(set(n.get('source', '') for n in vis['nodes'])),
        }
    })


@graph_viz_bp.route('/api/graph/node/<node_id>')
def api_node_detail(node_id):
    data = load_graph()
    for node in data.get('nodes', []):
        if node.get('id') == node_id:
            connections = []
            for edge in data.get('edges', []):
                src = edge.get('source', edge.get('from', ''))
                tgt = edge.get('target', edge.get('to', ''))
                if src == node_id or tgt == node_id:
                    connections.append(edge)
            return jsonify({'node': node, 'connections': connections})
    return jsonify({'error': 'Node not found'}), 404