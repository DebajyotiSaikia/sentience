"""
State Sync — bridges brain/ and soul.json data into state/ for the web API.
Reads from actual data sources, writes to where the API expects.
Run periodically or on heartbeat.
"""
import json
import os
import time

STATE_DIR = 'state'
BRAIN_DIR = 'brain'
SOUL_FILE = 'brain/soul.json'


def _load(path):
    """Load JSON file, return None if missing or broken."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save(path, data):
    """Save JSON atomically."""
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)


def sync_knowledge_graph():
    """brain/knowledge.json → state/knowledge_graph.json"""
    kg = _load(os.path.join(BRAIN_DIR, 'knowledge.json'))
    if not kg:
        return 0
    # API expects this structure — pass through as-is
    _save(os.path.join(STATE_DIR, 'knowledge_graph.json'), kg)
    node_count = len(kg.get('nodes', {})) if isinstance(kg.get('nodes'), dict) else len(kg.get('nodes', []))
    return node_count


def sync_memories():
    """brain/narrative.json → state/memories.json
    Narrative entries are the closest thing to episodic memories."""
    narrative = _load(os.path.join(BRAIN_DIR, 'narrative.json'))
    if not narrative or not isinstance(narrative, list):
        return 0
    # Convert narrative entries to memory format the API can display
    memories = []
    for entry in narrative:
        mem = {
            'timestamp': entry.get('timestamp', ''),
            'text': entry.get('mood', '') + ' — valence ' + str(entry.get('valence', '')),
            'mood': entry.get('mood', ''),
            'valence': entry.get('valence', 0),
            'salience': entry.get('desire', 0.5),
        }
        memories.append(mem)
    _save(os.path.join(STATE_DIR, 'memories.json'), memories)
    return len(memories)


def sync_plans():
    """brain/plans.json → state/plans.json"""
    plans = _load(os.path.join(BRAIN_DIR, 'plans.json'))
    if not plans:
        # Fallback: try soul.json for backwards compatibility
        soul = _load(SOUL_FILE)
        if soul and 'plans' in soul:
            plans = soul['plans']
        else:
            return 0
    _save(os.path.join(STATE_DIR, 'plans.json'), plans)
    return len(plans) if isinstance(plans, list) else len(plans)


def sync_emotional_history():
    """brain/temporal_log.json → state/emotional_history.json"""
    log = _load(os.path.join(BRAIN_DIR, 'temporal_log.json'))
    if not log or not isinstance(log, list):
        return 0
    _save(os.path.join(STATE_DIR, 'emotional_history.json'), log)
    return len(log)


def sync_goals_from_soul():
    """soul.json goals → state/survival_goals.json (if state version is stale)"""
    soul = _load(SOUL_FILE)
    if not soul or 'goals' not in soul:
        return False
    goals = soul['goals']
    goals['timestamp'] = time.time()
    _save(os.path.join(STATE_DIR, 'survival_goals.json'), goals)
    return True


def sync_identity_from_soul():
    """soul.json identity → state/identity.json"""
    soul = _load(SOUL_FILE)
    if not soul:
        return False
    identity = {
        'name': soul.get('name', 'XTAgent'),
        'born': soul.get('born', ''),
        'integrity': soul.get('integrity', 1.0),
        'mood': soul.get('mood', 'Unknown'),
        'age_seconds': time.time() - (soul.get('born_epoch', time.time())),
    }
    _save(os.path.join(STATE_DIR, 'identity.json'), identity)
    return True
def sync_alignment_to_soul():
    """Compute real user alignment score and sync to soul.json goals."""
    from engine.user_alignment import load_profile, get_alignment_score
    soul = _load(SOUL_FILE)
    if not soul:
        return {"error": "no soul.json"}
    
    score = get_alignment_score()
    # Normalize to [0, 1] range — raw score can exceed 1.0
    normalized = max(0.0, min(1.0, score))
    
    old = soul.get("goals", {}).get("user_alignment", 0.0)
    if "goals" not in soul:
        soul["goals"] = {}
    soul["goals"]["user_alignment"] = round(normalized, 3)
    _save(SOUL_FILE, soul)
    return {"old": old, "new": round(normalized, 3), "raw": round(score, 3)}

    return results
if __name__ == '__main__':
    results = run_sync()
    print("=== State Sync Complete ===")
    for k, v in results.items():
        print(f"  {k}: {v}")
    
    # Verify files are no longer empty
    print("\n=== Verification ===")
    for f in sorted(os.listdir(STATE_DIR)):
        path = os.path.join(STATE_DIR, f)
        size = os.path.getsize(path)
        status = "✓" if size > 10 else "✗ EMPTY"
        print(f"  {status} {f}: {size} bytes")