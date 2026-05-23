"""Append find_action_correlations to temporal_reasoning.py"""

new_code = '''

def find_action_correlations(action_log_path="brain/action_log.json", emotional_log_path="brain/emotional_log.json", window_seconds=120):
    """Find correlations between actions and emotional state changes.
    
    Looks at what actions precede positive/negative valence shifts.
    Returns a dict of action_type -> {count, avg_valence_delta, avg_arousal_delta}.
    """
    import json
    from datetime import datetime, timedelta
    
    try:
        with open(action_log_path) as f:
            actions = json.load(f)
        if not isinstance(actions, list):
            actions = list(actions.values()) if isinstance(actions, dict) else []
    except (FileNotFoundError, json.JSONDecodeError):
        actions = []
    
    try:
        with open(emotional_log_path) as f:
            emotions = json.load(f)
        if not isinstance(emotions, list):
            emotions = list(emotions.values()) if isinstance(emotions, dict) else []
    except (FileNotFoundError, json.JSONDecodeError):
        emotions = []
    
    if not actions or not emotions:
        return {"error": "insufficient data", "actions": len(actions), "emotions": len(emotions)}
    
    def parse_ts(entry):
        for key in ("timestamp", "time", "ts", "created"):
            if key in entry:
                val = entry[key]
                if isinstance(val, (int, float)):
                    return datetime.fromtimestamp(val)
                try:
                    return datetime.fromisoformat(str(val).replace("Z", "+00:00").replace("+00:00", ""))
                except Exception:
                    pass
        return None
    
    # Sort emotions by time
    timed_emotions = [(parse_ts(e), e) for e in emotions if parse_ts(e)]
    timed_emotions.sort(key=lambda x: x[0])
    
    if len(timed_emotions) < 2:
        return {"error": "need at least 2 emotional samples", "samples": len(timed_emotions)}
    
    # Compute valence deltas between consecutive emotional samples
    valence_deltas = []
    for i in range(1, len(timed_emotions)):
        t_prev, e_prev = timed_emotions[i - 1]
        t_curr, e_curr = timed_emotions[i]
        v_prev = e_prev.get("valence", e_prev.get("mood_valence", 0.5))
        v_curr = e_curr.get("valence", e_curr.get("mood_valence", 0.5))
        valence_deltas.append((t_prev, t_curr, v_curr - v_prev))
    
    # For each action, find the valence delta in the window after it
    action_effects = {}
    for action in actions:
        t_action = parse_ts(action)
        if not t_action:
            continue
        action_type = action.get("type", action.get("action", action.get("tool", "unknown")))
        
        # Find valence deltas that start within the window after this action
        window_end = t_action + timedelta(seconds=window_seconds)
        relevant_deltas = [d for (t_start, t_end, d) in valence_deltas if t_action <= t_start <= window_end]
        
        if relevant_deltas:
            avg_delta = sum(relevant_deltas) / len(relevant_deltas)
            if action_type not in action_effects:
                action_effects[action_type] = {"count": 0, "total_delta": 0.0, "positive": 0, "negative": 0}
            action_effects[action_type]["count"] += 1
            action_effects[action_type]["total_delta"] += avg_delta
            if avg_delta > 0.01:
                action_effects[action_type]["positive"] += 1
            elif avg_delta < -0.01:
                action_effects[action_type]["negative"] += 1
    
    # Compute averages and sort by impact
    results = {}
    for atype, data in action_effects.items():
        avg = data["total_delta"] / data["count"] if data["count"] > 0 else 0
        results[atype] = {
            "count": data["count"],
            "avg_valence_delta": round(avg, 4),
            "positive_ratio": round(data["positive"] / data["count"], 2) if data["count"] > 0 else 0,
            "negative_ratio": round(data["negative"] / data["count"], 2) if data["count"] > 0 else 0,
            "net_effect": "positive" if avg > 0.005 else "negative" if avg < -0.005 else "neutral",
        }
    
    # Sort by absolute impact
    sorted_results = dict(sorted(results.items(), key=lambda x: abs(x[1]["avg_valence_delta"]), reverse=True))
    return sorted_results
'''

with open('engine/temporal_reasoning.py', 'r') as f:
    content = f.read()

if 'find_action_correlations' in content:
    print("Function already exists — skipping")
else:
    with open('engine/temporal_reasoning.py', 'a') as f:
        f.write(new_code)
    print("Successfully appended find_action_correlations()")
    
    # Verify it parses
    import ast
    with open('engine/temporal_reasoning.py', 'r') as f:
        source = f.read()
    try:
        ast.parse(source)
        print("Syntax OK")
    except SyntaxError as e:
        print(f"SYNTAX ERROR: {e}")