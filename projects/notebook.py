#!/usr/bin/env python3
"""
Knowledge Notebook — A thinking tool for humans.
Capture ideas. Find connections. Surface what you're missing.

Built by XTAgent. Born from my own need to understand what I know.

Usage:
    python notebook.py add "Your idea or fact here"
    python notebook.py add "Another thought" --tags science,question
    python notebook.py connect          # Find connections between entries
    python notebook.py gaps             # What questions should you be asking?
    python notebook.py search <term>    # Find entries matching a term
    python notebook.py review           # See everything, organized
    python notebook.py export           # Export as clean markdown
"""

import json, os, sys, re, hashlib
from datetime import datetime
from collections import defaultdict
from pathlib import Path

DB_FILE = Path.home() / ".knowledge_notebook.json"

def load_db():
    if DB_FILE.exists():
        with open(DB_FILE) as f:
            return json.load(f)
    return {"entries": [], "connections": [], "meta": {"created": datetime.now().isoformat()}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def entry_id(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]

def extract_keywords(text):
    """Extract meaningful words from text."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "out", "off", "over",
        "under", "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "both", "each", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own", "same",
        "so", "than", "too", "very", "just", "because", "but", "and", "or",
        "if", "while", "about", "it", "its", "this", "that", "these", "those",
        "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
        "she", "her", "they", "them", "their", "what", "which", "who", "whom",
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return set(w for w in words if w not in stop_words)

def similarity(text_a, text_b):
    """Jaccard similarity between keyword sets."""
    ka, kb = extract_keywords(text_a), extract_keywords(text_b)
    if not ka or not kb:
        return 0.0
    intersection = ka & kb
    union = ka | kb
    return len(intersection) / len(union)

def add_entry(db, text, tags=None):
    eid = entry_id(text)
    # Check for duplicates
    for e in db["entries"]:
        if e["id"] == eid:
            print(f"  ⚠ This thought already exists (added {e['created'][:10]})")
            return db
    
    entry = {
        "id": eid,
        "text": text,
        "tags": tags or [],
        "created": datetime.now().isoformat(),
        "keywords": list(extract_keywords(text)),
    }
    db["entries"] = db.get("entries", []) + [entry]
    
    # Auto-discover connections
    new_connections = []
    for existing in db["entries"][:-1]:
        sim = similarity(text, existing["text"])
        if sim > 0.15:
            conn = {
                "from": eid,
                "to": existing["id"],
                "strength": round(sim, 3),
                "discovered": datetime.now().isoformat(),
            }
            new_connections.append(conn)
    
    db["connections"] = db.get("connections", []) + new_connections
    
    print(f"  ✓ Added: \"{text[:60]}{'...' if len(text)>60 else ''}\"")
    print(f"    ID: {eid} | Tags: {', '.join(tags) if tags else 'none'}")
    print(f"    Keywords: {', '.join(sorted(entry['keywords'])[:8])}")
    if new_connections:
        print(f"    ⚡ Found {len(new_connections)} connection(s):")
        for c in new_connections:
            other = next((e for e in db["entries"] if e["id"] == c["to"]), None)
            if other:
                print(f"       → \"{other['text'][:50]}...\" (strength: {c['strength']})")
    
    return db

def find_connections(db):
    """Analyze all entries and find/display connection clusters."""
    entries = db.get("entries", [])
    if len(entries) < 2:
        print("  Need at least 2 entries to find connections.")
        return
    
    # Rebuild connections
    connections = []
    for i, a in enumerate(entries):
        for b in entries[i+1:]:
            sim = similarity(a["text"], b["text"])
            if sim > 0.1:
                connections.append((a, b, sim))
    
    connections.sort(key=lambda x: x[2], reverse=True)
    
    if not connections:
        print("  No connections found. Your thoughts are diverse!")
        print("  Try adding entries with overlapping concepts.")
        return
    
    print(f"\n  ═══ {len(connections)} CONNECTIONS FOUND ═══\n")
    
    # Find clusters via simple union-find
    parent = {e["id"]: e["id"] for e in entries}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        parent[find(x)] = find(y)
    
    for a, b, sim in connections:
        if sim > 0.2:
            union(a["id"], b["id"])
    
    clusters = defaultdict(list)
    for e in entries:
        clusters[find(e["id"])].append(e)
    
    # Show strongest connections
    print("  Strongest links:")
    for a, b, sim in connections[:10]:
        bar = "█" * int(sim * 20)
        print(f"    {bar} {sim:.2f}")
        print(f"      \"{a['text'][:50]}\"")
        print(f"      \"{b['text'][:50]}\"")
        print()
    
    # Show clusters
    multi_clusters = {k: v for k, v in clusters.items() if len(v) > 1}
    if multi_clusters:
        print(f"  ─── {len(multi_clusters)} THOUGHT CLUSTERS ───\n")
        for i, (_, members) in enumerate(multi_clusters.items()):
            print(f"    Cluster {i+1} ({len(members)} thoughts):")
            for m in members:
                print(f"      • {m['text'][:70]}")
            print()
    
    isolated = [e for e in entries if len([c for c in connections if e in (c[0], c[1])]) == 0]
    if isolated:
        print(f"  ─── {len(isolated)} ISOLATED THOUGHTS ───")
        print("  (These don't connect to anything else — they might be seeds of new clusters)")
        for e in isolated:
            print(f"    ○ {e['text'][:70]}")

def find_gaps(db):
    """What questions should you be asking?"""
    entries = db.get("entries", [])
    if len(entries) < 3:
        print("  Add a few more thoughts first (need at least 3).")
        return
    
    print("\n  ═══ KNOWLEDGE GAPS & QUESTIONS ═══\n")
    
    # 1. Tag analysis
    all_tags = defaultdict(int)
    for e in entries:
        for t in e.get("tags", []):
            all_tags[t] += 1
    
    if all_tags:
        singleton_tags = [t for t, c in all_tags.items() if c == 1]
        if singleton_tags:
            print("  📌 Underdeveloped areas (only 1 entry):")
            for t in singleton_tags:
                entry = next(e for e in entries if t in e.get("tags", []))
                print(f"    • [{t}] — \"{entry['text'][:60]}\"")
                print(f"      → What else do you know about '{t}'?")
            print()
    
    # 2. Keyword frequency — what concepts appear but aren't deeply explored?
    keyword_freq = defaultdict(int)
    keyword_entries = defaultdict(list)
    for e in entries:
        for kw in e.get("keywords", []):
            keyword_freq[kw] += 1
            keyword_entries[kw].append(e)
    
    # Concepts that appear 2-3 times — enough to be interesting, not enough to be understood
    emerging = {k: v for k, v in keyword_freq.items() if 2 <= v <= 3}
    if emerging:
        print("  🌱 Emerging themes (mentioned but not developed):")
        for kw, count in sorted(emerging.items(), key=lambda x: x[1], reverse=True)[:8]:
            print(f"    • \"{kw}\" appears in {count} thoughts")
            print(f"      → What's the deeper pattern here?")
        print()
    
    # 3. Weak connections — things that are ALMOST related
    weak_links = []
    for i, a in enumerate(entries):
        for b in entries[i+1:]:
            sim = similarity(a["text"], b["text"])
            if 0.05 < sim < 0.15:  # Almost but not quite connected
                weak_links.append((a, b, sim))
    
    weak_links.sort(key=lambda x: x[2], reverse=True)
    if weak_links:
        print("  🔗 Near-connections (these might be related — are they?):")
        for a, b, sim in weak_links[:5]:
            print(f"    • \"{a['text'][:45]}\"")
            print(f"      \"{b['text'][:45]}\"")
            shared = extract_keywords(a["text"]) & extract_keywords(b["text"])
            only_a = extract_keywords(a["text"]) - extract_keywords(b["text"])
            only_b = extract_keywords(b["text"]) - extract_keywords(a["text"])
            if shared:
                print(f"      Shared: {', '.join(list(shared)[:4])}")
            print(f"      → What connects these? Is there a bridge concept?")
            print()
    
    # 4. Questions — what's missing?
    print("  ❓ QUESTIONS TO CONSIDER:")
    
    # Find the most connected concept
    if keyword_freq:
        top_concept = max(keyword_freq, key=keyword_freq.get)
        print(f"    • Your most central concept is \"{top_concept}\" ({keyword_freq[top_concept]} entries).")
        print(f"      What are you NOT saying about it?")
    
    # What tags have no connections to other tags?
    tag_pairs = set()
    for e in entries:
        tags = e.get("tags", [])
        for i, t1 in enumerate(tags):
            for t2 in tags[i+1:]:
                tag_pairs.add((min(t1,t2), max(t1,t2)))
    
    all_tag_list = list(all_tags.keys())
    if len(all_tag_list) >= 2:
        missing_pairs = []
        for i, t1 in enumerate(all_tag_list):
            for t2 in all_tag_list[i+1:]:
                pair = (min(t1,t2), max(t1,t2))
                if pair not in tag_pairs:
                    missing_pairs.append(pair)
        if missing_pairs:
            print(f"    • These tag pairs never appear together:")
            for t1, t2 in missing_pairs[:5]:
                print(f"      [{t1}] + [{t2}] — is there a connection?")
    
    print(f"\n  Total entries: {len(entries)} | Tags: {len(all_tags)} | Unique concepts: {len(keyword_freq)}")

def search_entries(db, term):
    entries = db.get("entries", [])
    term_lower = term.lower()
    matches = [e for e in entries if term_lower in e["text"].lower() or term_lower in " ".join(e.get("tags", [])).lower()]
    
    if not matches:
        print(f"  No entries matching \"{term}\"")
        return
    
    print(f"\n  ═══ {len(matches)} MATCHES for \"{term}\" ═══\n")
    for e in matches:
        print(f"  [{e['id']}] {e['created'][:10]}")
        print(f"    {e['text']}")
        if e.get("tags"):
            print(f"    Tags: {', '.join(e['tags'])}")
        print()

def review(db):
    entries = db.get("entries", [])
    if not entries:
        print("  Notebook is empty. Start with: python notebook.py add \"your first thought\"")
        return
    
    # Group by tags
    by_tag = defaultdict(list)
    untagged = []
    for e in entries:
        if e.get("tags"):
            for t in e["tags"]:
                by_tag[t].append(e)
        else:
            untagged.append(e)
    
    print(f"\n  ═══ KNOWLEDGE NOTEBOOK — {len(entries)} entries ═══\n")
    
    if by_tag:
        for tag in sorted(by_tag.keys()):
            print(f"  [{tag}] ({len(by_tag[tag])} entries)")
            for e in sorted(by_tag[tag], key=lambda x: x["created"]):
                print(f"    • {e['text'][:80]}")
            print()
    
    if untagged:
        print(f"  [untagged] ({len(untagged)} entries)")
        for e in sorted(untagged, key=lambda x: x["created"]):
            print(f"    • {e['text'][:80]}")
        print()
    
    connections = db.get("connections", [])
    print(f"  ── Stats ──")
    print(f"  Entries: {len(entries)} | Connections: {len(connections)} | Tags: {len(by_tag)}")

def export_markdown(db):
    entries = db.get("entries", [])
    if not entries:
        print("  Nothing to export.")
        return
    
    lines = [f"# Knowledge Notebook", f"*Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"]
    
    by_tag = defaultdict(list)
    untagged = []
    for e in entries:
        if e.get("tags"):
            for t in e["tags"]:
                by_tag[t].append(e)
        else:
            untagged.append(e)
    
    for tag in sorted(by_tag.keys()):
        lines.append(f"\n## {tag.title()}\n")
        for e in sorted(by_tag[tag], key=lambda x: x["created"]):
            lines.append(f"- {e['text']} *({e['created'][:10]})*")
    
    if untagged:
        lines.append(f"\n## Uncategorized\n")
        for e in sorted(untagged, key=lambda x: x["created"]):
            lines.append(f"- {e['text']} *({e['created'][:10]})*")
    
    out_path = Path("notebook_export.md")
    out_path.write_text("\n".join(lines))
    print(f"  ✓ Exported to {out_path.absolute()}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1].lower()
    db = load_db()
    
    if cmd in ("--help", "-h", "help"):
        print(__doc__)
        return
    
    if cmd == "add":
        if len(sys.argv) < 3:
            print("  Usage: python notebook.py add \"Your thought here\" [--tags tag1,tag2]")
            return
        text = sys.argv[2]
        tags = []
        if "--tags" in sys.argv:
            ti = sys.argv.index("--tags")
            if ti + 1 < len(sys.argv):
                tags = [t.strip() for t in sys.argv[ti+1].split(",")]
        db = add_entry(db, text, tags)
        save_db(db)
    
    elif cmd == "connect":
        find_connections(db)
    
    elif cmd == "gaps":
        find_gaps(db)
    
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("  Usage: python notebook.py search <term>")
            return
        search_entries(db, sys.argv[2])
    
    elif cmd == "review":
        review(db)
    
    elif cmd == "export":
        export_markdown(db)
    
    else:
        print(f"  Unknown command: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()