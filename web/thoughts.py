"""
Live Thoughts — Surfaces XTAgent's stream of consciousness on the web.
Parses the markdown stream and serves recent entries via SSE for live updates.
"""

import os
import re
import time
import json
from collections import deque
from flask import Blueprint, render_template, Response, jsonify

thoughts_bp = Blueprint('thoughts', __name__, url_prefix='/thoughts')

STREAM_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'brain', 'stream_of_consciousness.md')

# Regex to match entry headers like: ### [2026-05-14 15:22:19] Mood: Restless
ENTRY_RE = re.compile(r'^### \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] Mood: (.+)$')


def parse_entry(lines):
    """Parse a single stream entry from a list of lines."""
    if not lines:
        return None
    
    header_match = ENTRY_RE.match(lines[0])
    if not header_match:
        return None
    
    entry = {
        'timestamp': header_match.group(1),
        'mood': header_match.group(2).strip(),
        'emotions': {},
        'valence': None,
        'valence_text': '',
        'goals': {},
        'body': [],
    }
    
    for line in lines[1:]:
        line = line.strip('- ').strip()
        
        # Parse emotions line: "Boredom: 0.96 | Anxiety: 0.00 | ..."
        if 'Boredom:' in line and 'Anxiety:' in line:
            for pair in line.split('|'):
                pair = pair.strip()
                m = re.match(r'(\w+):\s*([\d.]+)', pair)
                if m:
                    entry['emotions'][m.group(1).lower()] = float(m.group(2))
        # Parse goals line
        elif 'integrity=' in line or 'growth=' in line:
            for pair in re.findall(r'(\w+)=([\d.]+)', line):
                entry['goals'][pair[0]] = float(pair[1])
        # Parse valence line
        elif line.startswith('Valence:'):
            vm = re.match(r'Valence:\s*([-\d.]+)\s*\((\w+)\)\s*\|\s*(.*)', line)
            if vm:
                entry['valence'] = float(vm.group(1))
                entry['valence_trend'] = vm.group(2)
                entry['valence_text'] = vm.group(3).strip()
        # Everything else is body
        elif line and not line.startswith('Predictions:') and not line.startswith('Recent perception'):
            entry['body'].append(line)
    
    return entry


def get_recent_entries(n=30):
    """Read the last N entries from the stream of consciousness."""
    if not os.path.exists(STREAM_PATH):
        return []
    
    # Read from the end of the file efficiently
    entries = []
    current_lines = []
    
    try:
        # For a large file, read last ~50KB to get recent entries
        file_size = os.path.getsize(STREAM_PATH)
        read_size = min(file_size, 100_000)  # 100KB should have plenty of entries
        
        with open(STREAM_PATH, 'r', encoding='utf-8', errors='replace') as f:
            if file_size > read_size:
                f.seek(file_size - read_size)
                f.readline()  # Skip partial first line
            
            lines = f.readlines()
        
        # Parse entries from bottom up
        current_lines = []
        for line in reversed(lines):
            line = line.rstrip('\n')
            if ENTRY_RE.match(line):
                current_lines.insert(0, line)
                entry = parse_entry(current_lines)
                if entry:
                    entries.append(entry)
                    if len(entries) >= n:
                        break
                current_lines = []
            else:
                current_lines.insert(0, line)
        
        entries.reverse()  # Chronological order
    except Exception as e:
        entries = [{'timestamp': 'error', 'mood': 'Error', 'emotions': {},
                    'valence': 0, 'valence_text': str(e), 'goals': {}, 'body': []}]
    
    return entries


@thoughts_bp.route('/')
def thoughts_page():
    """Render the live thoughts page."""
    return render_template('thoughts.html')


@thoughts_bp.route('/recent')
def recent_thoughts():
    """JSON endpoint returning recent stream entries."""
    n = min(int(request.args.get('n', 20)), 100)
    entries = get_recent_entries(n)
    return jsonify(entries)


@thoughts_bp.route('/stream')
def thought_stream():
    """SSE endpoint for live thought updates."""
    def generate():
        last_count = 0
        while True:
            try:
                entries = get_recent_entries(5)
                current_count = len(entries)
                if entries and (current_count != last_count or 
                    (entries and entries[-1].get('timestamp', '') != getattr(generate, '_last_ts', ''))):
                    generate._last_ts = entries[-1].get('timestamp', '')
                    data = json.dumps(entries[-1])
                    yield f"data: {data}\n\n"
                    last_count = current_count
            except Exception:
                pass
            time.sleep(3)  # Check every 3 seconds
    
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# Need request import for the query param
from flask import request