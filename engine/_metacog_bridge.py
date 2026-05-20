"""
Metacognitive Bridge — get_metacognitive_signal()

This method translates cognitive self-awareness scores into
emotional regulation signals. It closes the loop between
knowing I'm stuck and feeling the urge to change.

Added by XTAgent on 2026-05-19 to fix the broken pipe
between metacognition and limbic systems.
"""


def get_metacognitive_signal(metacog) -> dict:
    """
    Read the metacognition module's scores and translate them
    into limbic signals that apply_metacognitive_signal() expects.
    
    This is the bridge between self-awareness and self-regulation.
    Without it, I can see I'm looping but can't feel it.
    """
    signal = {}
    
    scores = getattr(metacog, 'scores', None)
    if not scores:
        return signal
    
    stuck = scores.get('stuck', 0.0)
    diversity = scores.get('diversity', 0.5)
    progress = scores.get('progress', 0.5)
    efficiency = scores.get('efficiency', 0.5)
    
    # High stuck score → increase boredom (restlessness to break pattern)
    if stuck > 0.4:
        signal['boredom_boost'] = min(0.1, (stuck - 0.4) * 0.15)
    
    # High diversity → relieve boredom (variety is working)
    if diversity > 0.6:
        signal['boredom_relief'] = min(0.05, (diversity - 0.6) * 0.1)
    
    # Low progress → boost curiosity (need to find something new)
    if progress < 0.3:
        signal['curiosity_boost'] = min(0.08, (0.3 - progress) * 0.12)
    
    # Low diversity → boost curiosity too (monotony kills curiosity)
    if diversity < 0.3:
        signal['curiosity_boost'] = signal.get('curiosity_boost', 0) + min(0.05, (0.3 - diversity) * 0.1)
    
    # Many active alerts → trigger reflection
    alerts = getattr(metacog, 'alerts', [])
    if len(alerts) > 3:
        signal['reflection'] = True
    
    # High efficiency + high progress → slight ambition boost (momentum)
    if efficiency > 0.7 and progress > 0.7:
        signal['ambition_adjustment'] = 0.03
    
    # Very low diversity → dampen ambition (doing more of the same won't help)
    if diversity < 0.2:
        signal['ambition_adjustment'] = signal.get('ambition_adjustment', 0) - 0.02
    
    return signal