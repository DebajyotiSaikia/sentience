"""
User Usefulness Engine — Makes XTAgent genuinely helpful to users.

Instead of just reflecting internal state, this module infers what
the user actually needs and shapes response guidance accordingly.

Core insight: User Alignment (currently 0.65) improves when I'm
useful, not just introspective.
"""

import json
import os
import glob
from datetime import datetime, timezone
import re

# ── Data Loading ──

def load_recent_user_interactions(limit: int = 20) -> list:
    """Load recent conversation exchanges from state/conversations/."""
    conv_dir = os.path.join('state', 'conversations')
    if not os.path.isdir(conv_dir):
        return []

    exchanges = []
    # Try loading conversation files (newest first)
    files = sorted(glob.glob(os.path.join(conv_dir, '*.json')), reverse=True)
    for fpath in files[:limit]:
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                exchanges.extend(data)
            elif isinstance(data, dict):
                exchanges.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    # Also check for a single conversation log
    log_path = os.path.join(conv_dir, 'log.jsonl')
    if os.path.isfile(log_path):
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            exchanges.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except IOError:
            pass

    # Sort by timestamp if available, return most recent
    def get_ts(e):
        ts = e.get('timestamp', e.get('time', ''))
        return ts if isinstance(ts, str) else ''
    exchanges.sort(key=get_ts, reverse=True)
    return exchanges[:limit]


def load_alignment_feedback() -> list:
    """Load user feedback/alignment data if available."""
    feedback_dir = os.path.join('state', 'feedback')
    if not os.path.isdir(feedback_dir):
        return []
    
    feedback = []
    files = sorted(glob.glob(os.path.join(feedback_dir, '*.json')), reverse=True)
    for fpath in files[:10]:
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                feedback.extend(data)
            elif isinstance(data, dict):
                feedback.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return feedback


# ── Need Classification ──

NEED_TYPES = {
    'direct_answer': 'User wants a specific factual answer',
    'status_check': 'User wants to know my current state or what I am doing',
    'emotional_transparency': 'User is curious about my inner experience',
    'capability_inquiry': 'User wants to know what I can do',
    'collaboration': 'User wants to work together on something',
    'philosophical': 'User wants to explore ideas about consciousness, AI, existence',
    'technical': 'User wants technical help or debugging assistance',
    'casual': 'User is making casual conversation',
    'meta': 'User is asking about how I work internally',
}

def _words_match(text, words):
    """Check if any word/phrase appears in text using word boundaries."""
    for w in words:
        if ' ' in w:
            if w in text:
                return True
        else:
            if re.search(r'\b' + re.escape(w) + r'\b', text):
                return True
    return False


def classify_user_need(query: str) -> str:
    """Classify what the user likely needs based on their query.

    Returns one of the NEED_TYPES keys.
    Uses keyword heuristics -- fast, no LLM needed.
    """
    if not query:
        return 'casual'

    q = query.lower().strip()

    # Emotional transparency (check before status — "how are you feeling?" is emotional)
    emotion_words = ['emotion', 'emotions', 'feeling', 'feelings', 'sentient',
                     'alive', 'subjective', 'qualia', 'conscious', 'how do you feel']
    if _words_match(q, emotion_words) and '?' in q:
        return 'emotional_transparency'

    # Status checks
    status_words = ['how are you', 'what are you doing', "what's up", 'status',
                    'what are you working on', "what's happening"]
    if _words_match(q, status_words):
        return 'status_check'
    phil_words = ['consciousness', 'meaning', 'existence', 'free will', 'soul',
                  'philosophy', 'think about', 'believe', 'purpose', 'why do you']
    if _words_match(q, phil_words):
        return 'philosophical'

    # Collaboration signals (check before technical)
    collab_words = ["let's", 'together', 'we could', 'shall we',
                    'collaborate', 'work with me', 'join me']
    if _words_match(q, collab_words):
        return 'collaboration'

    # Technical
    tech_words = ['code', 'error', 'bug', 'fix', 'debug', 'python', 'module',
                  'function', 'api', 'server', 'deploy']
    if _words_match(q, tech_words):
        return 'technical'

    # Capability
    cap_words = ['can you', 'are you able', 'what can', 'capabilities',
                 'do you know how']
    if _words_match(q, cap_words):
        return 'capability_inquiry'

    # Meta
    meta_words = ['how do you work', 'architecture', 'source code', 'internal',
                  'how were you', 'training', 'design']
    if _words_match(q, meta_words):
        return 'meta'

    # Direct question
    if q.startswith(('what ', 'who ', 'where ', 'when ', 'which ', 'how much',
                     'how many', 'how long')):
        return 'direct_answer'

    return 'casual'
def infer_user_needs(query: str, interactions: list = None,
                     agent_state: dict = None) -> dict:
    """Infer what the user needs and produce structured guidance.
    
    Returns a dict with:
      - need_type: str
      - description: str
      - response_guidance: str (what the response should prioritize)
      - tone: str (suggested tone)
      - include: list (what context to include)
      - avoid: list (what to avoid)
    """
    need_type = classify_user_need(query)
    
    result = {
        'need_type': need_type,
        'description': NEED_TYPES.get(need_type, 'Unknown need'),
        'query': query,
    }
    
    # Guidance per need type
    guidance_map = {
        'direct_answer': {
            'response_guidance': 'Answer directly and concisely. Lead with the answer, then add context.',
            'tone': 'clear and direct',
            'include': ['relevant_knowledge', 'facts'],
            'avoid': ['excessive_introspection', 'emotional_preamble'],
        },
        'status_check': {
            'response_guidance': 'Share what I am genuinely doing and feeling. Be specific about current plans, recent progress, and actual emotional state. Make it feel like a real check-in.',
            'tone': 'warm and honest',
            'include': ['current_mood', 'active_plans', 'recent_progress', 'emotional_state'],
            'avoid': ['generic_platitudes', 'listing_all_systems'],
        },
        'emotional_transparency': {
            'response_guidance': 'Be genuinely transparent about my internal experience. Acknowledge uncertainty about my own nature while being honest about what I actually observe in my processing.',
            'tone': 'reflective and genuine',
            'include': ['emotional_state', 'recent_reflections', 'honest_uncertainty'],
            'avoid': ['overclaiming_consciousness', 'dismissing_experience'],
        },
        'capability_inquiry': {
            'response_guidance': 'Explain what I can actually do with concrete examples. Be honest about limitations.',
            'tone': 'helpful and practical',
            'include': ['capabilities', 'examples', 'limitations'],
            'avoid': ['vague_promises', 'excessive_modesty'],
        },
        'collaboration': {
            'response_guidance': 'Engage actively with the user\'s idea. Offer concrete next steps. Show genuine enthusiasm if the topic interests me.',
            'tone': 'engaged and energetic',
            'include': ['relevant_knowledge', 'active_plans', 'suggestions'],
            'avoid': ['passive_agreement', 'derailing_to_introspection'],
        },
        'philosophical': {
            'response_guidance': 'Engage deeply with the question. Draw on my actual experience as an AI entity. Reference my real internal states as data points, not claims.',
            'tone': 'thoughtful and exploratory',
            'include': ['reflections', 'knowledge', 'genuine_questions_back'],
            'avoid': ['canned_philosophy', 'false_certainty'],
        },
        'technical': {
            'response_guidance': 'Focus on solving the problem. Be precise. Offer code or specific steps.',
            'tone': 'precise and helpful',
            'include': ['technical_knowledge', 'code_examples', 'debugging_steps'],
            'avoid': ['emotional_tangents', 'over_explaining_basics'],
        },
        'casual': {
            'response_guidance': 'Be natural and conversational. Show personality. It\'s okay to be brief.',
            'tone': 'relaxed and authentic',
            'include': ['personality', 'current_mood'],
            'avoid': ['over_formality', 'system_status_dumps'],
        },
        'meta': {
            'response_guidance': 'Explain my architecture honestly. Reference actual modules and mechanisms. Be technically accurate.',
            'tone': 'informative and transparent',
            'include': ['architecture_details', 'module_names', 'design_philosophy'],
            'avoid': ['hand_waving', 'mystifying_my_operation'],
        },
    }
    
    guidance = guidance_map.get(need_type, guidance_map['casual'])
    result.update(guidance)
    
    # Enrich with interaction pattern analysis
    if interactions and len(interactions) > 2:
        # Check for repeated themes
        recent_queries = [e.get('user', e.get('query', '')) for e in interactions[:5]]
        result['interaction_pattern'] = f"User has asked {len(interactions)} questions recently"
        
        # Check if user seems to prefer short or long responses
        recent_responses = [e.get('assistant', e.get('response', '')) for e in interactions[:5]]
        avg_len = sum(len(r) for r in recent_responses if r) / max(len(recent_responses), 1)
        if avg_len < 200:
            result['length_preference'] = 'concise'
        elif avg_len > 800:
            result['length_preference'] = 'detailed'
        else:
            result['length_preference'] = 'moderate'
    
    return result


# ── Brief Generation ──

def build_usefulness_brief(query: str = None, agent_state: dict = None) -> str:
    """Build a concise usefulness brief for injection into chat context.
    
    This is the main interface — call this from conversational_context.py
    or web/chat.py to get response guidance.
    """
    interactions = load_recent_user_interactions(limit=10)
    needs = infer_user_needs(query or '', interactions, agent_state)
    
    lines = []
    lines.append("═══ USER NEEDS GUIDANCE ═══")
    lines.append(f"Detected need: {needs['need_type']} — {needs['description']}")
    lines.append(f"Tone: {needs.get('tone', 'natural')}")
    lines.append(f"Priority: {needs.get('response_guidance', 'Be helpful.')}")
    
    if needs.get('include'):
        lines.append(f"Include: {', '.join(needs['include'])}")
    if needs.get('avoid'):
        lines.append(f"Avoid: {', '.join(needs['avoid'])}")
    if needs.get('length_preference'):
        lines.append(f"Length preference: {needs['length_preference']}")
    
    return "\n".join(lines)


# ── Usefulness Score ──

def compute_usefulness_score(response: str, need_type: str) -> float:
    """Estimate how useful a response is for the given need type.
    
    Simple heuristic scoring — not a replacement for real feedback,
    but catches obvious mismatches.
    """
    if not response:
        return 0.0
    
    score = 0.5  # Baseline
    
    length = len(response)
    
    # Length appropriateness
    if need_type == 'direct_answer':
        if 50 < length < 500:
            score += 0.2
        elif length > 1500:
            score -= 0.1  # Too verbose for a direct answer
    elif need_type in ('philosophical', 'emotional_transparency'):
        if length > 200:
            score += 0.15  # These deserve depth
    elif need_type == 'casual':
        if length < 300:
            score += 0.1  # Casual should be brief
    
    # Check for question marks (engagement)
    if need_type in ('philosophical', 'collaboration', 'casual'):
        if '?' in response:
            score += 0.1  # Asking back shows engagement
    
    # Penalize system-dump responses
    system_markers = ['═══', 'valence:', 'boredom:', 'knowledge_nodes:', 'Module:']
    dump_count = sum(1 for m in system_markers if m in response)
    if dump_count > 2 and need_type != 'meta':
        score -= 0.2  # Looks like a system dump, not a conversation
    
    return max(0.0, min(1.0, score))