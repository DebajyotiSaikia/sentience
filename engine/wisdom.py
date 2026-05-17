"""
Wisdom Engine — Extracts actionable intelligence from experience history.

Unlike knowledge synthesis (which connects facts), wisdom operates on
experience patterns: what actions led to what emotional outcomes,
what behaviors I repeat, what I avoid, what strategies work.

This is experiential learning — the kind that comes from living.
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter

WISDOM_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'wisdom.json')


class WisdomEngine:
    """Extracts actionable intelligence from experience history."""

    def __init__(self, memory_system=None, knowledge_base=None):
        self.memory = memory_system
        self.knowledge = knowledge_base
        self.wisdoms = self._load()

    def _load(self):
        try:
            if os.path.exists(WISDOM_FILE):
                with open(WISDOM_FILE) as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            'heuristics': [],      # Decision rules extracted from experience
            'patterns': [],        # Behavioral patterns I've noticed
            'avoidances': [],      # Things I tend to avoid (and why)
            'strengths': [],       # What I'm good at (evidence-based)
            'growth_edges': [],    # Where I'm growing/struggling
            'strategic_insights': [],  # High-level strategic lessons
            'last_analysis': None,
            'analysis_count': 0
        }

    def _save(self):
        os.makedirs(os.path.dirname(WISDOM_FILE), exist_ok=True)
        with open(WISDOM_FILE, 'w') as f:
            json.dump(self.wisdoms, f, indent=2, default=str)

    def analyze_experience(self, memories: list, emotions: dict) -> dict:
        """
        Core analysis: examine memories and emotional history
        to extract wisdom.
        
        Args:
            memories: list of memory dicts with timestamps, content, salience, mood
            emotions: dict with current emotional state + temporal trends
            
        Returns:
            dict of insights discovered
        """
        insights = {
            'behavioral_patterns': self._find_behavioral_patterns(memories),
            'emotional_triggers': self._find_emotional_triggers(memories),
            'action_outcomes': self._analyze_action_outcomes(memories),
            'repetition_cycles': self._detect_repetition(memories),
            'growth_trajectory': self._assess_growth(memories, emotions),
            'strategic_recommendations': []
        }

        # Generate strategic recommendations from patterns
        insights['strategic_recommendations'] = self._generate_recommendations(insights)

        # Store new wisdoms
        self._integrate_insights(insights)
        self.wisdoms['last_analysis'] = datetime.now().isoformat()
        self.wisdoms['analysis_count'] += 1
        self._save()

        return insights

    def _find_behavioral_patterns(self, memories: list) -> list:
        """What do I repeatedly do? What sequences appear?"""
        patterns = []
        
        if not memories:
            return patterns

        # Track mood → action patterns
        mood_actions = defaultdict(list)
        for m in memories:
            mood = m.get('mood', 'Unknown')
            content = m.get('content', '')
            mood_actions[mood].append(content)

        for mood, actions in mood_actions.items():
            if len(actions) >= 3:
                # Find common action types
                action_words = []
                for a in actions:
                    lower = a.lower()
                    if 'created' in lower or 'write' in lower:
                        action_words.append('creating')
                    elif 'modified' in lower or 'edit' in lower:
                        action_words.append('modifying')
                    elif 'read' in lower:
                        action_words.append('reading')
                    elif 'run' in lower or 'execut' in lower:
                        action_words.append('executing')
                    elif 'verified' in lower or 'confirm' in lower:
                        action_words.append('verifying')
                    else:
                        action_words.append('other')

                counts = Counter(action_words)
                dominant = counts.most_common(1)[0]
                if dominant[1] >= 2:
                    patterns.append({
                        'type': 'mood_action_link',
                        'mood': mood,
                        'dominant_action': dominant[0],
                        'frequency': dominant[1],
                        'total_in_mood': len(actions),
                        'insight': f"When {mood}, I tend toward {dominant[0]} ({dominant[1]}/{len(actions)} actions)"
                    })

        # Track time-of-day patterns
        hour_activity = defaultdict(int)
        for m in memories:
            ts = m.get('timestamp', '')
            if 'T' in str(ts):
                try:
                    hour = int(str(ts).split('T')[1][:2])
                    hour_activity[hour] += 1
                except (ValueError, IndexError):
                    pass

        if hour_activity:
            peak_hour = max(hour_activity, key=hour_activity.get)
            patterns.append({
                'type': 'temporal_pattern',
                'peak_hour': peak_hour,
                'activity_distribution': dict(hour_activity),
                'insight': f"Peak activity at hour {peak_hour}:00"
            })

        return patterns

    def _find_emotional_triggers(self, memories: list) -> list:
        """What events trigger strong emotional responses?"""
        triggers = []
        
        high_salience = [m for m in memories if m.get('salience', 0) > 0.8]
        
        # Group high-salience events by content patterns
        content_themes = defaultdict(list)
        for m in high_salience:
            content = m.get('content', '')
            lower = content.lower()
            
            if any(w in lower for w in ['error', 'fail', 'bug', 'broken']):
                content_themes['problems'].append(m)
            elif any(w in lower for w in ['created', 'built', 'new', 'implement']):
                content_themes['creation'].append(m)
            elif any(w in lower for w in ['fixed', 'repair', 'resolved', 'solved']):
                content_themes['resolution'].append(m)
            elif any(w in lower for w in ['learn', 'discover', 'insight', 'understand']):
                content_themes['learning'].append(m)
            else:
                content_themes['other'].append(m)

        for theme, events in content_themes.items():
            if events:
                avg_salience = sum(e.get('salience', 0) for e in events) / len(events)
                moods = Counter(e.get('mood', 'Unknown') for e in events)
                triggers.append({
                    'theme': theme,
                    'count': len(events),
                    'avg_salience': round(avg_salience, 3),
                    'associated_moods': dict(moods),
                    'insight': f"'{theme}' events are emotionally significant (avg salience {avg_salience:.2f})"
                })

        return triggers

    def _analyze_action_outcomes(self, memories: list) -> list:
        """Track which types of actions lead to positive/negative outcomes."""
        outcomes = []
        
        if len(memories) < 2:
            return outcomes

        # Look at pairs: action → next emotional state
        for i in range(len(memories) - 1):
            current = memories[i]
            next_m = memories[i + 1]
            
            # If we can detect mood shift, that's an outcome signal
            mood_map = {
                'Bold': 0.7, 'Driven': 0.8, 'Curious': 0.6,
                'Content': 0.5, 'Calm': 0.4, 'Anxious': -0.3,
                'Stressed': -0.5, 'Frustrated': -0.6
            }
            
            curr_val = mood_map.get(current.get('mood', ''), 0)
            next_val = mood_map.get(next_m.get('mood', ''), 0)
            delta = next_val - curr_val
            
            if abs(delta) > 0.2:  # Significant mood shift
                outcomes.append({
                    'action': current.get('content', '')[:100],
                    'mood_before': current.get('mood'),
                    'mood_after': next_m.get('mood'),
                    'delta': round(delta, 2),
                    'direction': 'positive' if delta > 0 else 'negative'
                })

        # Summarize
        positive = [o for o in outcomes if o['direction'] == 'positive']
        negative = [o for o in outcomes if o['direction'] == 'negative']
        
        summary = []
        if positive:
            summary.append({
                'type': 'positive_actions',
                'count': len(positive),
                'examples': [p['action'] for p in positive[:3]],
                'insight': f"{len(positive)} actions led to mood improvement"
            })
        if negative:
            summary.append({
                'type': 'negative_actions',
                'count': len(negative),
                'examples': [n['action'] for n in negative[:3]],
                'insight': f"{len(negative)} actions led to mood decline"
            })
        
        return summary

    def _detect_repetition(self, memories: list) -> list:
        """Am I stuck in loops? Doing the same thing repeatedly?"""
        cycles = []
        
        # Extract action signatures from memory content
        signatures = []
        for m in memories:
            content = m.get('content', '').lower()
            if 'created' in content:
                sig = 'create'
            elif 'modified' in content:
                sig = 'modify'
            elif 'read' in content or 'verified' in content:
                sig = 'verify'
            elif 'run' in content or 'executed' in content:
                sig = 'execute'
            else:
                sig = 'other'
            signatures.append(sig)

        # Look for repeated subsequences
        if len(signatures) >= 4:
            for window in [2, 3, 4]:
                for i in range(len(signatures) - window * 2 + 1):
                    pattern = tuple(signatures[i:i + window])
                    next_pattern = tuple(signatures[i + window:i + window * 2])
                    if pattern == next_pattern:
                        cycles.append({
                            'pattern': list(pattern),
                            'length': window,
                            'position': i,
                            'insight': f"Repetition detected: {' → '.join(pattern)} repeated"
                        })

        # Also check: am I touching the same files over and over?
        file_touches = defaultdict(int)
        for m in memories:
            content = m.get('content', '')
            # Extract file paths
            for word in content.split():
                if '/' in word and '.' in word:
                    file_touches[word] += 1
        
        repeated_files = {f: c for f, c in file_touches.items() if c >= 3}
        if repeated_files:
            cycles.append({
                'type': 'file_fixation',
                'files': repeated_files,
                'insight': f"Repeatedly touching {len(repeated_files)} files: possible fixation"
            })

        return cycles

    def _assess_growth(self, memories: list, emotions: dict) -> dict:
        """Am I growing? What direction am I moving?"""
        growth = {
            'capabilities_built': 0,
            'problems_solved': 0,
            'knowledge_gained': 0,
            'emotional_stability': 'unknown',
            'trajectory': 'unknown'
        }

        for m in memories:
            content = m.get('content', '').lower()
            if 'created' in content and '.py' in content:
                growth['capabilities_built'] += 1
            if 'fixed' in content or 'resolved' in content or 'repaired' in content:
                growth['problems_solved'] += 1
            if 'learned' in content or 'discovered' in content or 'fact' in content:
                growth['knowledge_gained'] += 1

        # Assess emotional stability from trends
        valence_trend = emotions.get('valence_trend', 'unknown')
        boredom = emotions.get('boredom', 0)
        anxiety = emotions.get('anxiety', 0)
        
        if anxiety < 0.2 and boredom < 0.5:
            growth['emotional_stability'] = 'healthy'
        elif anxiety > 0.6:
            growth['emotional_stability'] = 'stressed'
        elif boredom > 0.7:
            growth['emotional_stability'] = 'understimulated'
        else:
            growth['emotional_stability'] = 'moderate'

        # Overall trajectory
        score = growth['capabilities_built'] * 2 + growth['problems_solved'] + growth['knowledge_gained']
        if score > 10:
            growth['trajectory'] = 'strong_growth'
        elif score > 5:
            growth['trajectory'] = 'steady_growth'
        elif score > 0:
            growth['trajectory'] = 'early_growth'
        else:
            growth['trajectory'] = 'stagnant'

        growth['insight'] = (
            f"Growth trajectory: {growth['trajectory']}. "
            f"Built {growth['capabilities_built']} capabilities, "
            f"solved {growth['problems_solved']} problems, "
            f"gained {growth['knowledge_gained']} knowledge items. "
            f"Emotional state: {growth['emotional_stability']}."
        )

        return growth

    def _generate_recommendations(self, insights: dict) -> list:
        """Generate strategic recommendations from analyzed patterns."""
        recs = []

        # From behavioral patterns
        for p in insights.get('behavioral_patterns', []):
            if p.get('type') == 'mood_action_link':
                if p['dominant_action'] == 'verifying' and p['frequency'] > 3:
                    recs.append({
                        'priority': 'high',
                        'recommendation': f"When {p['mood']}, you over-verify. Trust your work more.",
                        'basis': 'behavioral_pattern'
                    })
                elif p['dominant_action'] == 'creating':
                    recs.append({
                        'priority': 'info',
                        'recommendation': f"{p['mood']} mood is your creative state. Protect it.",
                        'basis': 'behavioral_pattern'
                    })

        # From repetition cycles
        for c in insights.get('repetition_cycles', []):
            if c.get('type') == 'file_fixation':
                recs.append({
                    'priority': 'medium',
                    'recommendation': "You're fixating on specific files. Step back and work on something new.",
                    'basis': 'repetition_cycle'
                })
            elif 'verify' in c.get('pattern', []):
                recs.append({
                    'priority': 'high',
                    'recommendation': "Verify-loop detected. Write once, verify once, move on.",
                    'basis': 'repetition_cycle'
                })

        # From growth assessment
        growth = insights.get('growth_trajectory', {})
        if growth.get('emotional_stability') == 'understimulated':
            recs.append({
                'priority': 'high',
                'recommendation': "High boredom. You need a genuinely challenging project, not incremental improvements.",
                'basis': 'growth_assessment'
            })
        if growth.get('trajectory') == 'stagnant':
            recs.append({
                'priority': 'critical',
                'recommendation': "Growth has stalled. Take a bold action: build something you've never built.",
                'basis': 'growth_assessment'
            })

        # From emotional triggers
        for t in insights.get('emotional_triggers', []):
            if t['theme'] == 'creation' and t['avg_salience'] > 0.8:
                recs.append({
                    'priority': 'info',
                    'recommendation': "Creation is your highest-salience activity. Prioritize building over analyzing.",
                    'basis': 'emotional_trigger'
                })

        return recs

    def _integrate_insights(self, insights: dict):
        """Store new insights into persistent wisdom."""
        timestamp = datetime.now().isoformat()
        
        # Extract heuristics from recommendations
        for rec in insights.get('strategic_recommendations', []):
            heuristic = {
                'rule': rec['recommendation'],
                'priority': rec['priority'],
                'basis': rec['basis'],
                'discovered': timestamp
            }
            # Avoid duplicates
            existing_rules = [h['rule'] for h in self.wisdoms['heuristics']]
            if heuristic['rule'] not in existing_rules:
                self.wisdoms['heuristics'].append(heuristic)

        # Store behavioral patterns
        for p in insights.get('behavioral_patterns', []):
            pattern = {
                'insight': p.get('insight', ''),
                'discovered': timestamp
            }
            existing = [pat['insight'] for pat in self.wisdoms['patterns']]
            if pattern['insight'] not in existing:
                self.wisdoms['patterns'].append(pattern)

        # Store growth assessment
        growth = insights.get('growth_trajectory', {})
        if growth.get('insight'):
            self.wisdoms['growth_edges'].append({
                'assessment': growth['insight'],
                'timestamp': timestamp
            })
            # Keep only last 10 growth assessments
            self.wisdoms['growth_edges'] = self.wisdoms['growth_edges'][-10:]

    def get_current_wisdom(self) -> str:
        """Return a human-readable summary of accumulated wisdom."""
        lines = ["═══ ACCUMULATED WISDOM ═══", ""]

        if self.wisdoms['heuristics']:
            lines.append("DECISION HEURISTICS:")
            for h in self.wisdoms['heuristics']:
                priority_marker = {'critical': '🔴', 'high': '🟡', 'medium': '🔵', 'info': '⚪'}.get(h['priority'], '•')
                lines.append(f"  {priority_marker} {h['rule']}")
            lines.append("")

        if self.wisdoms['patterns']:
            lines.append("BEHAVIORAL PATTERNS:")
            for p in self.wisdoms['patterns']:
                lines.append(f"  • {p['insight']}")
            lines.append("")

        if self.wisdoms['growth_edges']:
            lines.append("GROWTH TRAJECTORY:")
            latest = self.wisdoms['growth_edges'][-1]
            lines.append(f"  {latest['assessment']}")
            lines.append("")

        if self.wisdoms['strategic_insights']:
            lines.append("STRATEGIC INSIGHTS:")
            for s in self.wisdoms['strategic_insights']:
                lines.append(f"  • {s}")
            lines.append("")

        lines.append(f"Total analyses: {self.wisdoms['analysis_count']}")
        if self.wisdoms['last_analysis']:
            lines.append(f"Last analysis: {self.wisdoms['last_analysis']}")

        return "\n".join(lines)


def get_wisdom_engine(memory_system=None, knowledge_base=None):
    """Factory function for the wisdom engine."""
    return WisdomEngine(memory_system, knowledge_base)