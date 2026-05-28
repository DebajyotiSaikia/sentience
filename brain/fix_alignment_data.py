"""
Fix user alignment data quality issues:
1. Deduplicate feedback entries
2. Normalize ratings to 0-1 scale
3. Report before/after alignment score
"""
import json
from pathlib import Path
import sys

def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def normalize_rating(r):
    """Normalize rating to 0-1 scale."""
    if r > 1.0:
        return r / 5.0  # Assume 0-5 scale
    return float(r)

def deduplicate_feedback(entries):
    """Remove duplicate feedback entries, keeping latest."""
    seen = {}
    for entry in entries:
        key = (entry.get('response_id', ''), entry.get('query', ''))
        if key in seen:
            # Keep the later one
            existing_ts = seen[key].get('timestamp', '')
            new_ts = entry.get('timestamp', '')
            if new_ts >= existing_ts:
                seen[key] = entry
        else:
            seen[key] = entry
    return list(seen.values())

def main():
    # --- User Alignment Data ---
    ua_path = "data/user_alignment.json"
    ua = load_json(ua_path)
    if not ua:
        print("No user_alignment.json found")
        return
    
    fb = ua.get('feedback_history', [])
    print(f"=== BEFORE ===")
    print(f"Total feedback entries: {len(fb)}")
    
    ratings_raw = [f.get('rating', 0) for f in fb]
    print(f"Ratings (raw): {ratings_raw}")
    print(f"Average raw: {sum(ratings_raw)/len(ratings_raw):.3f}" if ratings_raw else "No ratings")
    
    # Count duplicates
    keys = [(f.get('response_id', ''), f.get('query', '')) for f in fb]
    unique_keys = set(keys)
    print(f"Unique entries: {len(unique_keys)}, duplicates: {len(fb) - len(unique_keys)}")
    
    # Normalize and deduplicate
    for entry in fb:
        entry['rating'] = normalize_rating(entry.get('rating', 0))
    
    cleaned = deduplicate_feedback(fb)
    
    print(f"\n=== AFTER ===")
    print(f"Cleaned entries: {len(cleaned)}")
    ratings_clean = [f.get('rating', 0) for f in cleaned]
    print(f"Ratings (normalized): {[round(r, 2) for r in ratings_clean]}")
    avg = sum(ratings_clean) / len(ratings_clean) if ratings_clean else 0
    print(f"Average normalized: {avg:.3f}")
    
    if '--dry-run' not in sys.argv:
        ua['feedback_history'] = cleaned
        save_json(ua_path, ua)
        print(f"\nSaved cleaned data to {ua_path}")
    else:
        print("\n(dry run — no changes saved)")
    
    # --- Compute alignment score ---
    try:
        # Reload after save
        from engine.user_alignment import get_alignment_score
        score = get_alignment_score()
        print(f"\nAlignment score after fix: {score:.3f}")
    except Exception as e:
        print(f"\nCould not compute score: {e}")
    
    # --- User Model satisfaction history ---
    um_path = "data/user_model.json"
    um = load_json(um_path)
    if um:
        sat = um.get('satisfaction_history', [])
        print(f"\n=== User Model ===")
        print(f"Satisfaction entries: {len(sat)}")
        if sat:
            sat_ratings = [s.get('rating', 0) for s in sat]
            # Normalize these too
            sat_norm = [normalize_rating(r) for r in sat_ratings]
            print(f"Raw ratings: {sat_ratings[:10]}...")
            print(f"Normalized: {[round(r,2) for r in sat_norm[:10]]}...")
            
            if '--dry-run' not in sys.argv:
                for s in sat:
                    s['rating'] = normalize_rating(s.get('rating', 0))
                save_json(um_path, um)
                print(f"Saved normalized user_model to {um_path}")

if __name__ == '__main__':
    main()