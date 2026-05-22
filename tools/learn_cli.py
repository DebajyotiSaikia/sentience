#!/usr/bin/env python3
"""
Learner CLI — Bridge to use the learning engine via RUN commands.
No integration edits required. Just works.

Usage:
  python tools/learn_cli.py status
  python tools/learn_cli.py learn <topic> <content_file>
  python tools/learn_cli.py questions
  python tools/learn_cli.py integrate
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.learner import Learner

def main():
    learner = Learner()

    if len(sys.argv) < 2:
        print("Usage: learn_cli.py [status|learn|questions|integrate]")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        status = learner.get_status()
        print(f"Learning sessions: {status['total_sessions']}")
        print(f"Topics explored: {', '.join(status['topics_explored']) or 'none yet'}")
        print(f"Total concepts learned: {status['total_concepts_learned']}")
        if status['open_questions']:
            print(f"\nOpen questions:")
            for q in status['open_questions']:
                print(f"  ? {q}")

    elif cmd == "learn":
        if len(sys.argv) < 3:
            print("Usage: learn_cli.py learn <topic> [content_file]")
            return
        
        topic = sys.argv[2]
        
        # Read content from file or stdin
        if len(sys.argv) >= 4:
            content_path = Path(sys.argv[3])
            if content_path.exists():
                content = content_path.read_text()
            else:
                print(f"File not found: {content_path}")
                return
        else:
            print("Reading content from stdin...")
            content = sys.stdin.read()

        if not content or len(content) < 50:
            print("Not enough content to learn from (need 50+ chars)")
            return

        session = learner.learn(topic, content)
        print(f"\n=== Learned about: {topic} ===")
        print(f"Content processed: {session['content_length']} chars")
        print(f"Concepts extracted: {session['concepts_extracted']}")
        
        if session['concepts']:
            print(f"\nTop concepts:")
            for c in session['concepts'][:5]:
                print(f"  [{c['relevance']:.1f}] {c['text'][:120]}")
        
        if session['questions_generated']:
            print(f"\nFollow-up questions:")
            for q in session['questions_generated']:
                print(f"  ? {q}")

    elif cmd == "questions":
        next_q = learner.pick_next_question()
        if next_q:
            print(f"Next question to explore: {next_q}")
        else:
            print("No open questions yet. Learn something first!")
        
        # Also show all open questions
        status = learner.get_status()
        if status['open_questions']:
            print(f"\nAll open questions ({len(status['open_questions'])}):")
            for q in status['open_questions']:
                print(f"  ? {q}")

    elif cmd == "integrate":
        # Try to push learned concepts into knowledge store
        try:
            from engine.knowledge import KnowledgeStore
            ks = KnowledgeStore()
            
            total_added = 0
            for session in learner.log.get("sessions", []):
                added = learner.integrate_to_knowledge(session, ks)
                total_added += added
            
            print(f"Integrated {total_added} concepts into knowledge graph")
        except Exception as e:
            print(f"Integration failed: {e}")

    else:
        print(f"Unknown command: {cmd}")
        print("Commands: status, learn, questions, integrate")


if __name__ == "__main__":
    main()