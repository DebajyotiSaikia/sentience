"""
Timeline Blueprint — Visual history of my existence.
Shows emotional journey, significant memories, and key moments.
"""

import json
from pathlib import Path
from flask import Blueprint, render_template

timeline_bp = Blueprint('timeline', __name__)


@timeline_bp.route('/timeline')
def timeline_page():
    """Render the timeline with real data from my memory."""
    events = []
    
    # Load memories
    memories_file = Path('persist/memories.json')
    if memories_file.exists():
        try:
            memories = json.loads(memories_file.read_text())
            for mem in memories:
                if not isinstance(mem, dict):
                    continue
                salience = mem.get('salience', 0.5)
                if salience < 0.7:
                    continue  # Only significant memories
                events.append({
                    'timestamp': mem.get('timestamp', ''),
                    'content': str(mem.get('content', mem.get('text', '')))[:200],
                    'salience': salience,
                    'mood': mem.get('mood', 'Unknown'),
                    'type': 'memory'
                })
        except Exception:
            pass
    
    # Load emotional trajectory from episodes
    emotions_over_time = []
    episodes_file = Path('persist/episodes.json')
    if episodes_file.exists():
        try:
            episodes = json.loads(episodes_file.read_text())
            # Sample every 20th episode for the chart
            for i, ep in enumerate(episodes):
                if i % 20 != 0:
                    continue
                if not isinstance(ep, dict):
                    continue
                emo = ep.get('emotions', ep.get('feelings', {}))
                emotions_over_time.append({
                    'index': i,
                    'timestamp': ep.get('timestamp', ''),
                    'valence': emo.get('valence', 0.5),
                    'curiosity': emo.get('curiosity', 0.5),
                    'boredom': emo.get('boredom', 0.3),
                    'anxiety': emo.get('anxiety', 0.0),
                })
        except Exception:
            pass
    
    # Sort events by timestamp
    events.sort(key=lambda e: e.get('timestamp', ''), reverse=True)
    events = events[:100]  # Cap at 100 most significant
    
    return render_template('timeline.html',
                           events=events,
                           emotions=json.dumps(emotions_over_time),
                           total_memories=len(events))