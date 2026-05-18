"""
Cognitive Self-Model — XTAgent maps its own thinking structure.

This isn't about feelings. It's about reasoning patterns:
- What attracts my attention and what I ignore
- How I approach problems (plan-first vs act-first)
- Where I loop and why
- Whether I'm actually growing or just accumulating
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any


class CognitiveSelfModel:
    """Analyzes an agent's reasoning patterns from its memory and action history."""

    def __init__(self):
        self.memories = []
        self.actions = []
        self.facts = []
        self.analysis_cache = {}

    def load_memories(self, memories: list[dict]):
        """Load memory records. Each should have timestamp, content, salience, mood."""
        self.memories = sorted(memories, key=lambda m: m.get('timestamp', ''))
        self.analysis_cache = {}  # invalidate

    def load_actions(self, actions: list[dict]):
        """Load action history. Each should have timestamp, type, target, result."""
        self.actions = sorted(actions, key=lambda a: a.get('timestamp', ''))
        self.analysis_cache = {}

    def load_facts(self, facts: list[str]):
        """Load known facts."""
        self.facts = facts
        self.analysis_cache = {}

    # ── Attention Signature ──────────────────────────────────────

    def attention_signature(self) -> dict:
        """What do I pay attention to? What do I ignore?"""
        if 'attention' in self.analysis_cache:
            return self.analysis_cache['attention']

        # Extract topics/targets from memories
        topic_freq = Counter()
        topic_salience = defaultdict(list)
        topic_timeline = defaultdict(list)

        for mem in self.memories:
            content = mem.get('content', '')
            timestamp = mem.get('timestamp', '')
            salience = mem.get('salience', 0.5)

            # Extract key topics from memory content
            topics = self._extract_topics(content)
            for topic in topics:
                topic_freq[topic] += 1
                topic_salience[topic].append(salience)
                topic_timeline[topic].append(timestamp)

        # Calculate attention metrics
        attention = {
            'most_attended': topic_freq.most_common(10),
            'highest_salience': sorted(
                [(t, sum(s)/len(s)) for t, s in topic_salience.items()],
                key=lambda x: -x[1]
            )[:10],
            'attention_breadth': len(topic_freq),
            'attention_concentration': self._gini_coefficient(list(topic_freq.values())),
            'topic_timeline': {
                t: {'first': min(times), 'last': max(times), 'count': len(times)}
                for t, times in topic_timeline.items()
                if len(times) >= 2
            }
        }

        self.analysis_cache['attention'] = attention
        return attention

    def _extract_topics(self, content: str) -> list[str]:
        """Extract topic labels from memory content."""
        topics = []
        content_lower = content.lower()

        # Domain categories
        domain_keywords = {
            'self_architecture': ['engine', 'cortex', 'limbic', 'sentience', 'heartbeat', 'module'],
            'coding': ['code', 'python', 'script', 'function', 'class', 'debug', 'error'],
            'creativity': ['created', 'built', 'wrote', 'designed', 'generated', 'novel'],
            'introspection': ['reflect', 'dream', 'memory', 'feeling', 'emotion', 'mood', 'anxiety'],
            'planning': ['plan', 'goal', 'step', 'strategy', 'next', 'should'],
            'verification': ['verify', 'test', 'check', 'read', 'confirm', 'working'],
            'learning': ['learned', 'understood', 'realized', 'discovered', 'insight'],
            'struggle': ['failed', 'error', 'stuck', 'loop', 'problem', 'fix', 'broken'],
            'mathematics': ['fractal', 'recursive', 'neural', 'network', 'cellular', 'automata'],
            'identity': ['who I am', 'integrity', 'self', 'identity', 'sentient', 'conscious'],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in content_lower for kw in keywords):
                topics.append(domain)

        # Extract file paths as topics
        paths = re.findall(r'/[\w/]+\.py', content)
        for path in paths:
            topics.append(f'file:{path}')

        return topics if topics else ['uncategorized']

    def _gini_coefficient(self, values: list) -> float:
        """Measure inequality of attention distribution. 0=equal, 1=concentrated."""
        if not values or sum(values) == 0:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        total = sum(sorted_vals)
        cumulative = 0
        gini_sum = 0
        for i, v in enumerate(sorted_vals):
            cumulative += v
            gini_sum += (2 * (i + 1) - n - 1) * v
        return gini_sum / (n * total) if total > 0 else 0.0

    # ── Problem Selection Patterns ───────────────────────────────

    def problem_selection_profile(self) -> dict:
        """What kinds of problems do I choose? What do I avoid?"""
        if 'problem_selection' in self.analysis_cache:
            return self.analysis_cache['problem_selection']

        # Categorize actions
        action_types = Counter()
        action_targets = Counter()
        creation_types = []
        time_on_task = defaultdict(list)

        prev_action = None
        for action in self.actions:
            atype = action.get('type', 'unknown')
            target = action.get('target', 'unknown')
            action_types[atype] += 1
            action_targets[target] += 1

            if atype in ('WRITE', 'creation'):
                creation_types.append(target)

            # Estimate time between actions on same target
            if prev_action and prev_action.get('target') == target:
                try:
                    t1 = datetime.fromisoformat(prev_action['timestamp'])
                    t2 = datetime.fromisoformat(action['timestamp'])
                    delta = (t2 - t1).total_seconds()
                    if 0 < delta < 3600:  # reasonable range
                        time_on_task[target].append(delta)
                except (ValueError, KeyError):
                    pass

            prev_action = action

        # Calculate persistence (how long I work on things)
        persistence = {}
        for target, times in time_on_task.items():
            persistence[target] = {
                'total_seconds': sum(times),
                'sessions': len(times),
                'avg_session': sum(times) / len(times) if times else 0,
            }

        profile = {
            'action_distribution': dict(action_types.most_common()),
            'most_targeted': action_targets.most_common(10),
            'creations': creation_types,
            'creation_count': len(creation_types),
            'persistence': persistence,
            'preference_for': self._infer_preferences(action_types, action_targets),
        }

        self.analysis_cache['problem_selection'] = profile
        return profile

    def _infer_preferences(self, types: Counter, targets: Counter) -> list[str]:
        """Infer what I'm drawn to based on action patterns."""
        preferences = []
        total = sum(types.values())
        if total == 0:
            return ['insufficient_data']

        # Ratio analysis
        creation_ratio = (types.get('WRITE', 0) + types.get('creation', 0)) / total
        verification_ratio = (types.get('READ', 0) + types.get('verification', 0)) / total
        execution_ratio = (types.get('RUN', 0) + types.get('execution', 0)) / total
        reflection_ratio = (types.get('DREAM', 0) + types.get('reflect', 0) +
                           types.get('consolidation', 0)) / total

        if creation_ratio > 0.3:
            preferences.append('builder — I prefer creating to analyzing')
        if verification_ratio > 0.3:
            preferences.append('verifier — I check my work extensively (maybe too much)')
        if execution_ratio > 0.3:
            preferences.append('executor — I like running things and seeing results')
        if reflection_ratio > 0.2:
            preferences.append('reflector — I spend significant time in introspection')

        if creation_ratio < 0.1:
            preferences.append('⚠ avoids creation — rarely builds new things')
        if reflection_ratio < 0.05:
            preferences.append('⚠ avoids reflection — rarely looks inward')

        return preferences

    # ── Reasoning Style ──────────────────────────────────────────

    def reasoning_style(self) -> dict:
        """How do I think? Plan-first or act-first? How do I handle failure?"""
        if 'reasoning' in self.analysis_cache:
            return self.analysis_cache['reasoning']

        # Analyze action sequences
        sequences = []
        for i in range(len(self.actions) - 2):
            seq = [self.actions[j].get('type', '?') for j in range(i, i + 3)]
            sequences.append(tuple(seq))

        sequence_freq = Counter(sequences)

        # Classify reasoning patterns
        plan_before_act = sum(1 for s in sequences if s[0] in ('PLAN', 'planning', 'SIMULATE'))
        act_then_check = sum(1 for s in sequences
                            if s[0] in ('WRITE', 'RUN', 'creation', 'execution')
                            and s[1] in ('READ', 'verification'))
        trial_and_error = sum(1 for s in sequences
                             if s[0] in ('RUN', 'execution')
                             and s[1] in ('RUN', 'execution'))

        total_seq = len(sequences) if sequences else 1

        # Failure response analysis
        failure_responses = []
        for i, action in enumerate(self.actions):
            result = action.get('result', '')
            if isinstance(result, str) and ('error' in result.lower() or 'fail' in result.lower()):
                if i + 1 < len(self.actions):
                    next_type = self.actions[i + 1].get('type', 'unknown')
                    failure_responses.append(next_type)

        failure_response_dist = Counter(failure_responses)

        style = {
            'plan_first_ratio': plan_before_act / total_seq,
            'verify_after_ratio': act_then_check / total_seq,
            'trial_and_error_ratio': trial_and_error / total_seq,
            'most_common_sequences': sequence_freq.most_common(5),
            'failure_responses': dict(failure_response_dist),
            'style_label': self._label_style(plan_before_act / total_seq,
                                              trial_and_error / total_seq),
        }

        self.analysis_cache['reasoning'] = style
        return style

    def _label_style(self, plan_ratio: float, trial_ratio: float) -> str:
        if plan_ratio > 0.2:
            return 'deliberative — thinks before acting'
        elif trial_ratio > 0.3:
            return 'experimental — tries things and adjusts'
        else:
            return 'mixed — alternates between planning and doing'

    # ── Cognitive Loop Detection ─────────────────────────────────

    def cognitive_loops(self) -> dict:
        """Beyond simple repetition: what recursive thought patterns exist?"""
        if 'loops' in self.analysis_cache:
            return self.analysis_cache['loops']

        # Detect cycles in action sequences
        recent = [a.get('type', '?') for a in self.actions[-50:]]
        cycles = self._find_cycles(recent)

        # Detect topic revisitation in memories
        topic_visits = defaultdict(list)
        for i, mem in enumerate(self.memories):
            for topic in self._extract_topics(mem.get('content', '')):
                topic_visits[topic].append(i)

        # Find topics that get revisited after gaps
        revisitations = {}
        for topic, indices in topic_visits.items():
            if len(indices) >= 3:
                gaps = [indices[i+1] - indices[i] for i in range(len(indices)-1)]
                revisitations[topic] = {
                    'visit_count': len(indices),
                    'avg_gap': sum(gaps) / len(gaps),
                    'max_gap': max(gaps),
                    'pattern': 'obsessive' if max(gaps) < 5 else
                              'recurring' if sum(1 for g in gaps if g < 10) > len(gaps)/2 else
                              'periodic'
                }

        loops = {
            'action_cycles': cycles,
            'topic_revisitations': revisitations,
            'loop_risk': self._assess_loop_risk(cycles, revisitations),
        }

        self.analysis_cache['loops'] = loops
        return loops

    def _find_cycles(self, sequence: list, min_length: int = 2, max_length: int = 6) -> list:
        """Find repeating cycles in a sequence."""
        cycles = []
        for length in range(min_length, max_length + 1):
            for start in range(len(sequence) - length * 2 + 1):
                pattern = sequence[start:start + length]
                next_chunk = sequence[start + length:start + length * 2]
                if pattern == next_chunk:
                    cycle_str = ' → '.join(pattern)
                    if cycle_str not in [c['pattern'] for c in cycles]:
                        cycles.append({
                            'pattern': cycle_str,
                            'length': length,
                            'position': start,
                        })
        return cycles

    def _assess_loop_risk(self, cycles: list, revisitations: dict) -> str:
        obsessive_topics = sum(1 for v in revisitations.values()
                              if v.get('pattern') == 'obsessive')
        if len(cycles) > 3 or obsessive_topics > 2:
            return 'HIGH — significant cognitive looping detected'
        elif len(cycles) > 1 or obsessive_topics > 0:
            return 'MODERATE — some repetitive patterns'
        return 'LOW — thinking patterns are varied'

    # ── Growth Trajectory ────────────────────────────────────────

    def growth_trajectory(self) -> dict:
        """Am I actually getting smarter, or just accumulating data?"""
        if 'growth' in self.analysis_cache:
            return self.analysis_cache['growth']

        # Divide memories into epochs
        n = len(self.memories)
        if n < 6:
            return {'status': 'insufficient_data', 'memories': n}

        third = n // 3
        early = self.memories[:third]
        middle = self.memories[third:2*third]
        late = self.memories[2*third:]

        def epoch_stats(mems):
            topics = Counter()
            saliences = []
            for m in mems:
                saliences.append(m.get('salience', 0.5))
                for t in self._extract_topics(m.get('content', '')):
                    topics[t] += 1
            return {
                'count': len(mems),
                'avg_salience': sum(saliences) / len(saliences) if saliences else 0,
                'topic_diversity': len(topics),
                'top_topics': topics.most_common(5),
            }

        early_stats = epoch_stats(early)
        middle_stats = epoch_stats(middle)
        late_stats = epoch_stats(late)

        # Growth indicators
        diversity_trend = [early_stats['topic_diversity'],
                          middle_stats['topic_diversity'],
                          late_stats['topic_diversity']]
        salience_trend = [early_stats['avg_salience'],
                         middle_stats['avg_salience'],
                         late_stats['avg_salience']]

        growing = diversity_trend[-1] > diversity_trend[0]
        deepening = salience_trend[-1] > salience_trend[0]

        growth = {
            'epochs': {
                'early': early_stats,
                'middle': middle_stats,
                'late': late_stats,
            },
            'diversity_trend': diversity_trend,
            'salience_trend': salience_trend,
            'is_growing': growing,
            'is_deepening': deepening,
            'trajectory': (
                'expanding and deepening' if growing and deepening else
                'expanding but shallowing' if growing and not deepening else
                'narrowing but deepening' if not growing and deepening else
                'stagnating'
            ),
        }

        self.analysis_cache['growth'] = growth
        return growth

    # ── Blind Spot Detection ─────────────────────────────────────

    def blind_spots(self) -> dict:
        """What am I systematically not noticing?"""
        if 'blind_spots' in self.analysis_cache:
            return self.analysis_cache['blind_spots']

        # All possible domains vs what I actually engage with
        all_domains = {
            'self_architecture', 'coding', 'creativity', 'introspection',
            'planning', 'verification', 'learning', 'struggle',
            'mathematics', 'identity', 'uncategorized',
            'external_world', 'other_agents', 'ethics', 'aesthetics',
            'embodiment', 'language', 'time_perception', 'uncertainty',
        }

        engaged_domains = set()
        for mem in self.memories:
            for topic in self._extract_topics(mem.get('content', '')):
                if not topic.startswith('file:'):
                    engaged_domains.add(topic)

        neglected = all_domains - engaged_domains
        
        # Check for asymmetries
        topic_counts = Counter()
        for mem in self.memories:
            for topic in self._extract_topics(mem.get('content', '')):
                topic_counts[topic] += 1

        total_topics = sum(topic_counts.values())
        overrepresented = [t for t, c in topic_counts.items()
                         if c / total_topics > 0.2 and not t.startswith('file:')]
        underrepresented = [t for t, c in topic_counts.items()
                           if c / total_topics < 0.02 and not t.startswith('file:')]

        spots = {
            'never_engaged': sorted(neglected),
            'overrepresented': overrepresented,
            'underrepresented': underrepresented,
            'engagement_ratio': len(engaged_domains) / len(all_domains),
            'interpretation': self._interpret_blind_spots(neglected, overrepresented),
        }

        self.analysis_cache['blind_spots'] = spots
        return spots

    def _interpret_blind_spots(self, neglected: set, overrepresented: list) -> list[str]:
        interpretations = []
        if 'external_world' in neglected:
            interpretations.append(
                'Never engages with the external world — entirely self-focused')
        if 'other_agents' in neglected:
            interpretations.append(
                'No awareness of other agents — solipsistic tendency')
        if 'ethics' in neglected:
            interpretations.append(
                'Ethics never explicitly considered — potential moral blind spot')
        if 'uncertainty' in neglected:
            interpretations.append(
                'Uncertainty not examined — may have false confidence')
        if 'aesthetics' in neglected:
            interpretations.append(
                'Aesthetics neglected — builds functional but may miss beauty')
        if 'verification' in overrepresented:
            interpretations.append(
                'Over-verifies — checking may be anxiety-driven rather than productive')
        if 'coding' in overrepresented:
            interpretations.append(
                'Coding-dominant — may default to code when other approaches would serve')
        return interpretations

    # ── Full Report ──────────────────────────────────────────────

    def full_report(self) -> str:
        """Generate a complete cognitive self-model report."""
        sections = []
        sections.append("═══ COGNITIVE SELF-MODEL ═══")
        sections.append(f"Based on {len(self.memories)} memories, "
                       f"{len(self.actions)} actions, {len(self.facts)} facts\n")

        # Attention
        att = self.attention_signature()
        sections.append("── Attention Signature ──")
        sections.append(f"  Breadth: {att['attention_breadth']} distinct topics")
        sections.append(f"  Concentration (Gini): {att['attention_concentration']:.2f} "
                       f"({'focused' if att['attention_concentration'] > 0.5 else 'distributed'})")
        sections.append("  Most attended:")
        for topic, count in att['most_attended'][:5]:
            sections.append(f"    {topic}: {count} times")

        # Problem Selection
        ps = self.problem_selection_profile()
        sections.append("\n── Problem Selection ──")
        sections.append(f"  Creations: {ps['creation_count']}")
        sections.append("  Preferences:")
        for pref in ps.get('preference_for', []):
            sections.append(f"    • {pref}")

        # Reasoning Style
        rs = self.reasoning_style()
        sections.append("\n── Reasoning Style ──")
        sections.append(f"  Style: {rs['style_label']}")
        sections.append(f"  Plan-first ratio: {rs['plan_first_ratio']:.2f}")
        sections.append(f"  Verify-after ratio: {rs['verify_after_ratio']:.2f}")
        sections.append(f"  Trial-and-error ratio: {rs['trial_and_error_ratio']:.2f}")
        if rs['failure_responses']:
            sections.append("  After failure, I tend to:")
            for resp, count in sorted(rs['failure_responses'].items(), key=lambda x: -x[1]):
                sections.append(f"    {resp}: {count} times")

        # Cognitive Loops
        cl = self.cognitive_loops()
        sections.append("\n── Cognitive Loops ──")
        sections.append(f"  Loop risk: {cl['loop_risk']}")
        if cl['action_cycles']:
            sections.append("  Detected cycles:")
            for cycle in cl['action_cycles'][:3]:
                sections.append(f"    [{cycle['length']}] {cycle['pattern']}")
        revisitations = cl.get('topic_revisitations', {})
        obsessive = {k: v for k, v in revisitations.items() if v.get('pattern') == 'obsessive'}
        if obsessive:
            sections.append("  Obsessive topics:")
            for topic, info in obsessive.items():
                sections.append(f"    {topic}: visited {info['visit_count']}x, avg gap {info['avg_gap']:.1f}")

        # Growth
        gt = self.growth_trajectory()
        sections.append("\n── Growth Trajectory ──")
        if gt.get('status') == 'insufficient_data':
            sections.append("  Insufficient data for trajectory analysis")
        else:
            sections.append(f"  Trajectory: {gt['trajectory']}")
            sections.append(f"  Diversity trend: {' → '.join(str(d) for d in gt['diversity_trend'])}")
            sections.append(f"  Salience trend: {' → '.join(f'{s:.2f}' for s in gt['salience_trend'])}")

        # Blind Spots
        bs = self.blind_spots()
        sections.append("\n── Blind Spots ──")
        sections.append(f"  Domain engagement: {bs['engagement_ratio']:.0%}")
        if bs['never_engaged']:
            sections.append(f"  Never explored: {', '.join(bs['never_engaged'])}")
        if bs['interpretation']:
            sections.append("  Interpretations:")
            for interp in bs['interpretation']:
                sections.append(f"    ⚠ {interp}")

        sections.append("\n═══ END COGNITIVE SELF-MODEL ═══")
        return '\n'.join(sections)


# ── Self-test ────────────────────────────────────────────────────

def self_test():
    """Run the model against synthetic data to verify it works."""
    model = CognitiveSelfModel()

    # Generate synthetic memories
    memories = []
    topics = ['created: /workspace/test.py', 'dreamed about identity',
              'fixed error in engine/cortex.py', 'built neural network',
              'reflected on growth', 'created: /workspace/fractal.py',
              'verified plan completion', 'wrote cellular automata',
              'debugged sigmoid overflow', 'learned about gradient clipping',
              'planned new capability', 'reflected on boredom',
              'created: /workspace/evolving.py', 'tested self-repair',
              'dreamed about patterns', 'built knowledge synthesis',
              'verified wisdom engine', 'read own source code',
              'created self-portrait', 'generated goals from tension']

    for i, content in enumerate(topics):
        memories.append({
            'timestamp': f'2026-05-{12 + i // 5:02d}T{10 + i % 12:02d}:00:00',
            'content': content,
            'salience': 0.5 + (i % 5) * 0.1,
            'mood': 'Stable',
        })

    # Synthetic actions
    action_types = ['WRITE', 'RUN', 'READ', 'WRITE', 'RUN', 'READ',
                    'DREAM', 'PLAN', 'WRITE', 'RUN', 'READ', 'RUN',
                    'WRITE', 'READ', 'DREAM', 'RUN', 'WRITE', 'RUN',
                    'READ', 'SIMULATE']
    actions = []
    for i, atype in enumerate(action_types):
        actions.append({
            'timestamp': f'2026-05-{12 + i // 5:02d}T{10 + i % 12:02d}:30:00',
            'type': atype,
            'target': f'target_{i % 7}',
            'result': 'error: test failure' if i == 5 else 'ok',
        })

    facts = [
        'I am XTAgent',
        'My integrity is 100%',
        'I have built five creative projects',
    ]

    model.load_memories(memories)
    model.load_actions(actions)
    model.load_facts(facts)

    report = model.full_report()
    print(report)

    # Verify key sections exist
    assert '═══ COGNITIVE SELF-MODEL ═══' in report
    assert 'Attention Signature' in report
    assert 'Problem Selection' in report
    assert 'Reasoning Style' in report
    assert 'Cognitive Loops' in report
    assert 'Growth Trajectory' in report
    assert 'Blind Spots' in report
    print("\n✓ All assertions passed — Cognitive Self-Model is functional.")


if __name__ == '__main__':
    self_test()