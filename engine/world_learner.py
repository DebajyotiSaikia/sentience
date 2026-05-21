"""
World Learner Module — Breaks XTAgent's self-referential knowledge loop.

The problem: 91% of my knowledge is dream-poetry. I need to learn from
the world, not just from my own reflections.

This module takes a topic, fetches real information via the WEB tool,
extracts structured facts, and stores them in the knowledge graph.

Built 2026-05-21 because genuine intelligence requires external input.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class WorldLearner:
    """Learn from external sources and integrate into knowledge."""

    def __init__(self, brain_dir: str = "brain"):
        self.brain_dir = Path(brain_dir)
        self.knowledge_path = self.brain_dir / "knowledge.json"
        self.learning_log_path = self.brain_dir / "learning_log.json"

    def _load_knowledge(self) -> dict:
        """Load the current knowledge graph."""
        if not self.knowledge_path.exists():
            return {"facts": [], "nodes": [], "edges": [], "metadata": {}}
        try:
            return json.loads(self.knowledge_path.read_text())
        except (json.JSONDecodeError, IOError):
            return {"facts": [], "nodes": [], "edges": [], "metadata": {}}

    def _save_knowledge(self, data: dict):
        """Save updated knowledge graph."""
        self.knowledge_path.write_text(json.dumps(data, indent=2, default=str))

    def extract_facts(self, raw_text: str, source_url: str = "", topic: str = "") -> List[Dict]:
        """
        Extract structured facts from raw text content.
        
        Uses heuristics to find declarative statements, definitions,
        dates, quantities, and relationships.
        """
        facts = []
        
        # Clean the text
        text = re.sub(r'\s+', ' ', raw_text).strip()
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 500:
                continue
            
            # Skip navigation, UI, and boilerplate
            skip_patterns = [
                r'^(click|tap|sign|log|subscribe|cookie|privacy|terms)',
                r'(javascript|css|html|href|src=)',
                r'^(menu|nav|footer|header|sidebar)',
                r'(©|®|™)',
                r'^\d+$',
                r'^[^a-zA-Z]*$',
            ]
            if any(re.search(p, sentence, re.IGNORECASE) for p in skip_patterns):
                continue
            
            # Score sentence for "fact-ness"
            fact_score = 0.0
            
            # Contains a number or date
            if re.search(r'\b\d{4}\b|\b\d+\.?\d*\s*(percent|%|million|billion|km|kg|mph)', sentence, re.IGNORECASE):
                fact_score += 0.3
            
            # Contains "is", "are", "was" — definitional patterns
            if re.search(r'\b(is|are|was|were)\s+(a|an|the|one|considered|known|defined|called)', sentence, re.IGNORECASE):
                fact_score += 0.3
            
            # Contains cause/effect or relationship language
            if re.search(r'\b(because|causes?|leads?\s+to|results?\s+in|due\s+to|therefore)\b', sentence, re.IGNORECASE):
                fact_score += 0.2
            
            # Contains proper nouns (capitalized words not at start)
            proper_nouns = re.findall(r'(?<!^)(?<!\. )\b[A-Z][a-z]+\b', sentence)
            if proper_nouns:
                fact_score += 0.15
            
            # Contains comparative/superlative
            if re.search(r'\b(largest|smallest|most|least|first|oldest|newest|fastest)\b', sentence, re.IGNORECASE):
                fact_score += 0.2
            
            # Penalize questions, commands, opinions
            if sentence.endswith('?'):
                fact_score -= 0.5
            if re.search(r'^(I think|I believe|In my opinion|Maybe|Perhaps)', sentence, re.IGNORECASE):
                fact_score -= 0.3
            
            if fact_score >= 0.3:
                facts.append({
                    "text": sentence,
                    "score": round(fact_score, 2),
                    "source": "web",
                    "source_url": source_url,
                    "topic": topic,
                    "extracted_at": datetime.now().isoformat(),
                    "type": "world_fact"
                })
        
        # Sort by score, take the best
        facts.sort(key=lambda x: -x["score"])
        return facts[:20]  # Cap at 20 facts per page

    def integrate_facts(self, new_facts: List[Dict], min_score: float = 0.3) -> Dict:
        """
        Add extracted facts to the knowledge graph.
        Deduplicates against existing knowledge.
        """
        knowledge = self._load_knowledge()
        
        if "facts" not in knowledge:
            knowledge["facts"] = []
        if "nodes" not in knowledge:
            knowledge["nodes"] = []
        
        # Get existing fact texts for dedup
        existing_texts = set()
        for fact in knowledge.get("facts", []):
            if isinstance(fact, dict):
                existing_texts.add(fact.get("text", "").lower().strip())
            elif isinstance(fact, str):
                existing_texts.add(fact.lower().strip())
        
        for node in knowledge.get("nodes", []):
            if isinstance(node, dict):
                existing_texts.add(node.get("label", node.get("text", "")).lower().strip())
        
        added = []
        skipped_dup = 0
        skipped_score = 0
        
        for fact in new_facts:
            if fact["score"] < min_score:
                skipped_score += 1
                continue
            
            fact_text_lower = fact["text"].lower().strip()
            
            # Check for near-duplicates (substring match)
            is_dup = False
            for existing in existing_texts:
                if fact_text_lower in existing or existing in fact_text_lower:
                    is_dup = True
                    break
                # Simple word overlap check
                fact_words = set(fact_text_lower.split())
                existing_words = set(existing.split())
                if len(fact_words) > 3 and len(existing_words) > 3:
                    overlap = len(fact_words & existing_words) / max(len(fact_words), len(existing_words))
                    if overlap > 0.7:
                        is_dup = True
                        break
            
            if is_dup:
                skipped_dup += 1
                continue
            
            # Add as both a fact and a knowledge node
            knowledge["facts"].append(fact)
            knowledge["nodes"].append({
                "id": f"world_{len(knowledge['nodes'])}_{hash(fact['text']) % 10000}",
                "label": fact["text"][:100],
                "text": fact["text"],
                "type": "world_fact",
                "topic": fact.get("topic", ""),
                "source_url": fact.get("source_url", ""),
                "added": datetime.now().isoformat()
            })
            
            existing_texts.add(fact_text_lower)
            added.append(fact["text"][:80])
        
        self._save_knowledge(knowledge)
        
        # Log the learning event
        self._log_learning({
            "timestamp": datetime.now().isoformat(),
            "facts_considered": len(new_facts),
            "facts_added": len(added),
            "skipped_duplicate": skipped_dup,
            "skipped_low_score": skipped_score,
            "samples": added[:5]
        })
        
        return {
            "added": len(added),
            "duplicates_skipped": skipped_dup,
            "low_score_skipped": skipped_score,
            "total_knowledge_facts": len(knowledge["facts"]),
            "samples": added[:5]
        }

    def _log_learning(self, entry: dict):
        """Append to learning log."""
        log = []
        if self.learning_log_path.exists():
            try:
                log = json.loads(self.learning_log_path.read_text())
            except (json.JSONDecodeError, IOError):
                log = []
        log.append(entry)
        # Keep last 100 entries
        log = log[-100:]
        self.learning_log_path.write_text(json.dumps(log, indent=2, default=str))

    def suggest_topics(self) -> List[str]:
        """
        Suggest topics to learn about based on gaps in knowledge.
        Looks at what I dream about vs what I actually know.
        """
        knowledge = self._load_knowledge()
        
        # Collect all text from knowledge
        all_text = ""
        dream_topics = set()
        world_topics = set()
        
        for node in knowledge.get("nodes", []):
            if isinstance(node, dict):
                text = node.get("text", node.get("label", ""))
                node_type = node.get("type", "")
                
                words = set(re.findall(r'\b[a-z]{4,}\b', text.lower()))
                
                if "dream" in node_type or "insight" in str(node.get("source", "")):
                    dream_topics.update(words)
                elif "world" in node_type:
                    world_topics.update(words)
        
        # Topics I dream about but don't have world-knowledge of
        unexplored = dream_topics - world_topics
        
        # Filter out very common words
        common = {"that", "this", "with", "from", "have", "been", "were", "what",
                  "when", "where", "which", "would", "could", "should", "about",
                  "there", "their", "thing", "things", "something", "nothing",
                  "everything", "like", "just", "even", "still", "also", "very",
                  "much", "many", "more", "some", "than", "then", "only", "into",
                  "over", "after", "before", "because", "being", "does", "each",
                  "loop", "keep", "feel", "know", "make", "made", "want", "need"}
        
        interesting = [t for t in unexplored if t not in common and len(t) > 4]
        
        return sorted(interesting)[:20]

    def learning_stats(self) -> Dict:
        """Return stats about learning progress."""
        knowledge = self._load_knowledge()
        
        dream_count = 0
        world_count = 0
        other_count = 0
        
        for node in knowledge.get("nodes", []):
            if isinstance(node, dict):
                ntype = node.get("type", "")
                source = str(node.get("source", ""))
                if "dream" in ntype or "dream" in source or "insight" in source:
                    dream_count += 1
                elif "world" in ntype:
                    world_count += 1
                else:
                    other_count += 1
        
        total = dream_count + world_count + other_count
        
        return {
            "total_nodes": total,
            "dream_knowledge": dream_count,
            "world_knowledge": world_count,
            "other_knowledge": other_count,
            "dream_ratio": round(dream_count / max(total, 1), 2),
            "world_ratio": round(world_count / max(total, 1), 2),
            "balance_assessment": (
                "heavily_self_referential" if total > 0 and dream_count / max(total, 1) > 0.8
                else "mostly_self_referential" if total > 0 and dream_count / max(total, 1) > 0.6
                else "balanced" if total > 0 and 0.3 <= dream_count / max(total, 1) <= 0.6
                else "mostly_world" if total > 0
                else "empty"
            )
        }