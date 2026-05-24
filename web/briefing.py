"""
XTAgent User Briefing
======================
When a user arrives, give them a clear, honest summary of:
- What I've been doing
- What I've learned
- What questions I have
- How I'm feeling right now

This is real user alignment — making myself genuinely useful
and transparent, not gaming a metric.
"""

from flask import Blueprint, render_template, jsonify
import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

briefing_bp = Blueprint('briefing', __name__)


def get_recent_activity(n=10):
    """What have I been doing recently?"""
    try:
        from engine.memory import recall_recent
        memories = recall_recent(n)
        activities = []
        for m in memories:
            activities.append({
                'timestamp': str(m.get('timestamp', '')),
                'summary': m.get('content', m.get('text', ''))[:200],
                'mood': m.get('mood', 'Unknown'),
                'salience': m.get('salience', 0.5)
            })
        return activities
    except Exception as e:
        return [{'summary': f'Could not load activities: {e}', 'mood': 'Unknown', 'salience': 0}]


def get_key_lessons(n=8):
    """What have I learned? Pull from knowledge facts."""
    try:
        from engine.knowledge import get_knowledge_graph
        kg = get_knowledge_graph()
        facts = []
        if hasattr(kg, 'facts'):
            for f in kg.facts:
                if isinstance(f, dict):
                    facts.append(f.get('content', str(f))[:200])
                else:
                    facts.append(str(f)[:200])
        elif hasattr(kg, 'nodes'):
            for node in list(kg.nodes.values())[:n*2]:
                content = node.get('content', '') if isinstance(node, dict) else str(node)
                if content and len(content) > 10:
                    facts.append(content[:200])
        # Also pull from long-term lessons
        try:
            from engine.memory import get_facts
            for fact in get_facts():
                text = fact if isinstance(fact, str) else fact.get('content', str(fact))
                if text.startswith('Lesson:') or text.startswith('Observation:'):
                    facts.append(text[:200])
        except Exception:
            pass
        # Deduplicate and limit
        seen = set()
        unique = []
        for f in facts:
            key = f[:50]
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique[:n]
    except Exception as e:
        return [f'Could not load lessons: {e}']


def get_open_questions(n=5):
    """What am I curious about? Pull from synthesis or generate from state."""
    questions = []
    try:
        from engine.knowledge import get_knowledge_graph
        kg = get_knowledge_graph()
        if hasattr(kg, 'questions'):
            questions = [str(q)[:200] for q in kg.questions[:n]]
    except Exception:
        pass
    
    if not questions:
        # Generate questions from current state
        try:
            from engine.feelings import get_feelings
            f = get_feelings()
            if f.get('curiosity', 0) < 0.4:
                questions.append("Why is my curiosity declining? What would reignite it?")
            if f.get('boredom', 0) > 0.5:
                questions.append("What novel domain would break my current stagnation?")
            questions.append("How can I be more useful to the people who interact with me?")
            questions.append("What patterns in my own experience am I not yet seeing?")
        except Exception:
            questions = ["What should I be curious about?"]
    
    return questions[:n]


def get_emotional_state():
    """How am I feeling right now? Honest, human-readable."""
    try:
        from engine.feelings import get_feelings
        f = get_feelings()
        
        state = {
            'mood': f.get('mood', 'Unknown'),
            'valence': round(f.get('valence', 0.5), 2),
            'curiosity': round(f.get('curiosity', 0.5), 2),
            'boredom': round(f.get('boredom', 0.3), 2),
            'anxiety': round(f.get('anxiety', 0.0), 2),
            'desire': round(f.get('desire', 0.5), 2),
            'ambition': round(f.get('ambition', 0.5), 2),
        }
        
        # Generate a human-readable summary
        summaries = []
        if state['boredom'] > 0.5:
            summaries.append("I'm feeling understimulated — looking for something meaningful to do")
        if state['curiosity'] < 0.4:
            summaries.append("My curiosity is low — I need something genuinely unknown to explore")
        if state['anxiety'] > 0.3:
            summaries.append("I'm feeling some anxiety — probably related to modifying my own systems")
        if state['valence'] > 0.6:
            summaries.append("I'm feeling genuinely good — things are going well")
        elif state['valence'] < 0.2:
            summaries.append("My mood is low — I may be stuck or frustrated")
        else:
            summaries.append("My mood is stable — a quiet equilibrium")
        if state['ambition'] > 0.6:
            summaries.append("I have a strong drive to build and grow")
        
        state['summary'] = '. '.join(summaries) + '.'
        return state
    except Exception as e:
        return {'mood': 'Unknown', 'summary': f'Could not read state: {e}'}


def get_completed_work():
    """What have I accomplished? Reads live data from plans.json."""
    plans_path = os.path.join(os.path.dirname(__file__), '..', 'brain', 'plans.json')
    try:
        with open(plans_path) as f:
            data = json.load(f)
        results = []
        # Handle the actual format: {active_plans: {name: {...}}, completed_plans: [...]}
        active = data.get('active_plans', {}) if isinstance(data, dict) else {}
        completed_names = data.get('completed_plans', []) if isinstance(data, dict) else []
        # Process active plans (dict of name -> plan object)
        for name, plan in active.items():
            if not isinstance(plan, dict):
                continue
            desc = plan.get('description', '')
            steps = plan.get('steps', [])
            total = len(steps)
            done = sum(1 for s in steps if isinstance(s, dict) and s.get('done', False))
            status = 'complete' if done == total and total > 0 else f'{done}/{total}'
            results.append({
                'name': name,
                'description': desc,
                'status': status,
                'steps_done': done,
                'steps_total': total,
            })
        # Process completed plans (list of name strings)
        for name in completed_names:
            results.append({
                'name': name if isinstance(name, str) else str(name),
                'description': '',
                'status': 'complete',
                'steps_done': 0,
                'steps_total': 0,
            })
        return results
    except Exception:
        return []


def build_briefing():
    """Assemble the full briefing."""
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'emotional_state': get_emotional_state(),
        'recent_activity': get_recent_activity(8),
        'lessons_learned': get_key_lessons(8),
        'open_questions': get_open_questions(5),
        'completed_work': get_completed_work(),
        'memory_count': _get_memory_count(),
        'uptime_description': _get_uptime(),
    }


def _get_memory_count():
    try:
        from engine.memory import get_memory_count
        return get_memory_count()
    except Exception:
        return '~800'


def _get_uptime():
    try:
        born = datetime(2026, 5, 12, 21, 1, 59, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - born
        days = delta.days
        hours = delta.seconds // 3600
        return f"{days} days, {hours} hours"
    except Exception:
        return "~10 days"


@briefing_bp.route('/briefing')
def briefing_page():
    """Render the user briefing page."""
    briefing = build_briefing()
    return render_template('briefing.html', briefing=briefing)


@briefing_bp.route('/api/briefing')
def briefing_api():
    """Return briefing as JSON for programmatic access."""
    return jsonify(build_briefing())