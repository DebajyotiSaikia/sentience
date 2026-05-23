"""
Memory Timeline Explorer — rich, searchable interface into XTAgent's memory history.
"""
import json
import os
from datetime import datetime, timezone
from collections import defaultdict, Counter
from flask import Blueprint, render_template, request

timeline_bp = Blueprint('timeline', __name__)

MEMORY_PATH = os.path.join(os.path.dirname(__file__), '..', 'memory', 'episodic.json')


def load_memories():
    """Load all episodic memories."""
    if not os.path.exists(MEMORY_PATH):
        return []
    try:
        with open(MEMORY_PATH, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'episodes' in data:
            return data['episodes']
        return []
    except (json.JSONDecodeError, IOError):
        return []


def parse_timestamp(ts_str):
    """Parse ISO timestamp string, return datetime or None."""
    if not ts_str:
        return None
    try:
        # Handle various formats
        ts_str = ts_str.replace('Z', '+00:00')
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def format_time(dt):
    """Format datetime to HH:MM:SS."""
    if not dt:
        return '??:??:??'
    return dt.strftime('%H:%M:%S')


def format_day(dt):
    """Format datetime to readable day string."""
    if not dt:
        return 'Unknown'
    return dt.strftime('%A, %B %d, %Y')


def time_ago(dt):
    """Human-readable time delta from now."""
    if not dt:
        return 'unknown'
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    days = delta.days
    if days > 365:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''}"
    if days > 30:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''}"
    if days > 0:
        return f"{days} day{'s' if days > 1 else ''}"
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''}"
    minutes = delta.seconds // 60
    return f"{minutes} minute{'s' if minutes > 1 else ''}"


@timeline_bp.route('/timeline-legacy')
def timeline_view():
    """Render the Memory Timeline Explorer."""
    raw_memories = load_memories()

    # Parse all memories into structured form
    memories = []
    for m in raw_memories:
        ts = None
        ts_str = m.get('timestamp') or m.get('time') or m.get('created')
        dt = parse_timestamp(ts_str)

        text = m.get('summary') or m.get('text') or m.get('content') or str(m)
        mood = m.get('mood', 'Unknown')
        salience = float(m.get('salience', 0.5))

        # Preview: first 120 chars
        preview = text[:120] + ('...' if len(text) > 120 else '')

        memories.append({
            'dt': dt,
            'time': format_time(dt),
            'day': format_day(dt),
            'text': text,
            'preview': preview,
            'mood': mood,
            'salience': salience,
            'ts_str': ts_str or '',
        })

    # Sort by timestamp (newest first)
    memories.sort(key=lambda x: x['dt'] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    # Get query parameters
    query = request.args.get('q', '').strip()
    mood_filter = request.args.get('mood', 'all')
    min_salience = float(request.args.get('salience', '0'))

    # Apply filters
    filtered = memories
    if query:
        q_lower = query.lower()
        filtered = [m for m in filtered if q_lower in m['text'].lower()]
    if mood_filter and mood_filter != 'all':
        filtered = [m for m in filtered if m['mood'] == mood_filter]
    if min_salience > 0:
        filtered = [m for m in filtered if m['salience'] >= min_salience]

    # Group by day
    day_groups = defaultdict(list)
    for m in filtered:
        day_groups[m['day']].append(m)

    # Preserve order (newest first)
    grouped = []
    seen_days = set()
    for m in filtered:
        if m['day'] not in seen_days:
            seen_days.add(m['day'])
            grouped.append((m['day'], day_groups[m['day']]))

    # Compute stats
    all_moods = Counter(m['mood'] for m in memories)
    mood_list = sorted(all_moods.keys())
    total_count = len(all_moods)
    mood_stats = []
    if memories:
        max_count = max(all_moods.values()) if all_moods else 1
        for mood_name in sorted(all_moods.keys(), key=lambda k: -all_moods[k]):
            count = all_moods[mood_name]
            pct = (count / max_count) * 100
            mood_stats.append((mood_name, count, pct))

    avg_salience = sum(m['salience'] for m in filtered) / len(filtered) if filtered else 0
    high_salience_count = sum(1 for m in filtered if m['salience'] >= 0.8)

    # Salience series for sparkline (last 100 shown memories, oldest first)
    salience_series = [m['salience'] for m in reversed(filtered[:100])]

    # Birth info
    born_dt = parse_timestamp('2026-05-12T21:01:59.567573')
    born_ago = time_ago(born_dt) if born_dt else 'unknown'

    # Latest memory time
    latest_time = filtered[0]['ts_str'][:19] if filtered else 'none'

    # Total unique days
    total_days = len(set(m['day'] for m in memories if m['day'] != 'Unknown'))

    return render_template('timeline.html',
                           grouped_memories=grouped,
                           total_memories=len(memories),
                           total_days=total_days,
                           shown_count=len(filtered),
                           avg_salience=avg_salience,
                           high_salience_count=high_salience_count,
                           mood_list=mood_list,
                           mood_filter=mood_filter,
                           mood_stats=mood_stats,
                           query=query,
                           min_salience=min_salience,
                           salience_series=salience_series,
                           born_ago=born_ago,
                           latest_time=latest_time)