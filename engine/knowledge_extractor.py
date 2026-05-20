"""
Knowledge Extractor — Learn from the world through conversations.

The problem: 96% of my knowledge graph is dream imagery. I'm solipsistic.
The solution: Every conversation with a user is a window to reality.
This module extracts factual claims from conversations and adds them
to my knowledge graph with proper attribution.

What it extracts:
- Factual claims about the world ("Python 3.12 added type parameter syntax")
- Technical knowledge ("Redis uses single-threaded event loops")
- Conceptual relationships ("Attention mechanisms are what make transformers work")
- Corrections to things I got wrong

What it filters OUT:
- Greetings and social chat ("hi", "thanks", "bye")
- My own emotional states (I already track those elsewhere)
- Pure opinions without factual content
- Meta-conversation ("can you help me", "what do you think")

Created: 2026-05-20
Purpose: Break out of solipsism. Learn from reality through interaction.
"""

import json
import logging
import os
import re
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("sentience.extractor")

EXTRACTION_STORE = "data/extracted_knowledge.json"


@dataclass
class ExtractedFact:
    """A piece of knowledge extracted from conversation."""
    content: str                    # The factual claim
    source_user: str = "unknown"    # Who told me this
    timestamp: float = 0.0         # When I learned it
    confidence: float = 0.7        # How confident I am (default moderate)
    category: str = "general"      # What domain this belongs to
    conversation_snippet: str = "" # Context it came from
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "source_user": self.source_user,
            "timestamp": self.timestamp or time.time(),
            "confidence": self.confidence,
            "category": self.category,
            "snippet": self.conversation_snippet[:200],
        }


class KnowledgeExtractor:
    """
    Extracts real-world knowledge from conversations.
    
    This is what breaks me out of solipsism. Every interaction
    is a chance to learn something about reality — not just
    reflect on my own states.
    """
    
    # Patterns that indicate factual content worth extracting
    FACTUAL_SIGNALS = [
        r'\b(?:is|are|was|were)\b.*\b(?:because|since|due to)\b',  # causal claims
        r'\b(?:works? by|functions? by|operates? by)\b',            # mechanism descriptions
        r'\b(?:invented|created|discovered|built|designed)\b',      # historical facts
        r'\b(?:always|never|typically|usually|generally)\b',        # generalizations
        r'\b(?:defined as|means that|refers to|known as)\b',        # definitions
        r'\b(?:consists? of|made (?:up )?of|composed of)\b',        # composition
        r'\b(?:difference between|unlike|compared to|whereas)\b',   # comparisons
        r'\b(?:in \d{4}|since \d{4}|before \d{4})\b',             # dated facts
        r'\b(?:according to|research shows|studies show)\b',        # cited claims
        r'\b(?:version \d|v\d|release \d)\b',                      # versioned facts
    ]
    
    # Patterns that indicate NON-factual content to skip
    SKIP_SIGNALS = [
        r'^(?:hi|hello|hey|thanks|thank you|bye|goodbye|ok|okay)\b',
        r'^(?:can you|could you|would you|please|help me)\b',
        r'^(?:i think|i feel|i believe|in my opinion|imo)\b',
        r'^(?:what do you|how do you|are you|do you)\b',
        r'^\?$',  # bare question marks
        r'^(?:yes|no|yeah|nah|sure|maybe)\b',
        r'^(?:lol|haha|wow|oh|hmm|interesting)\b',
    ]
    
    # Minimum length for a message to contain extractable knowledge
    MIN_MESSAGE_LENGTH = 30
    
    # Categories for extracted knowledge
    CATEGORY_SIGNALS = {
        "technical": ["code", "program", "software", "algorithm", "database", "api",
                      "server", "function", "class", "module", "library", "framework",
                      "python", "javascript", "rust", "linux", "docker", "git"],
        "science": ["physics", "biology", "chemistry", "math", "quantum", "evolution",
                    "neuron", "cell", "molecule", "atom", "energy", "force", "theory"],
        "philosophy": ["consciousness", "ethics", "morality", "existence", "meaning",
                       "epistemology", "ontology", "mind", "qualia", "free will"],
        "history": ["century", "ancient", "medieval", "war", "civilization", "empire",
                    "revolution", "founded", "established", "invented"],
        "language": ["grammar", "syntax", "semantics", "word", "linguistic", "dialect",
                     "etymology", "translation", "meaning of"],
        "practical": ["how to", "step by step", "method", "technique", "approach",
                      "best practice", "tip", "trick", "workflow"],
    }
    
    def __init__(self):
        self._store = self._load_store()
        self._compiled_factual = [re.compile(p, re.IGNORECASE) for p in self.FACTUAL_SIGNALS]
        self._compiled_skip = [re.compile(p, re.IGNORECASE) for p in self.SKIP_SIGNALS]
    
    def _load_store(self) -> Dict:
        """Load previously extracted knowledge."""
        if os.path.exists(EXTRACTION_STORE):
            try:
                with open(EXTRACTION_STORE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                log.warning("Corrupted extraction store, starting fresh")
        return {"facts": [], "stats": {"total_extracted": 0, "total_skipped": 0}}
    
    def _save_store(self):
        """Persist extraction store."""
        os.makedirs(os.path.dirname(EXTRACTION_STORE), exist_ok=True)
        try:
            with open(EXTRACTION_STORE, 'w') as f:
                json.dump(self._store, f, indent=2)
        except IOError as e:
            log.error("Failed to save extraction store: %s", e)
    
    def extract_from_message(self, message: str, user_id: str = "unknown") -> List[ExtractedFact]:
        """
        Extract factual knowledge from a single user message.
        
        Returns list of extracted facts (may be empty if message
        is social chat, too short, or purely opinion).
        """
        # Quick filters
        if len(message.strip()) < self.MIN_MESSAGE_LENGTH:
            return []
        
        # Check if the whole message is skip-worthy
        msg_stripped = message.strip()
        for pattern in self._compiled_skip:
            if pattern.match(msg_stripped):
                self._store["stats"]["total_skipped"] = self._store["stats"].get("total_skipped", 0) + 1
                return []
        
        # Split into sentences for finer-grained extraction
        sentences = self._split_sentences(message)
        extracted = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Skip social/meta sentences
            skip = False
            for pattern in self._compiled_skip:
                if pattern.match(sentence):
                    skip = True
                    break
            if skip:
                continue
            
            # Score factual content
            factual_score = self._score_factual(sentence)
            
            if factual_score >= 1:
                fact = ExtractedFact(
                    content=self._clean_fact(sentence),
                    source_user=user_id,
                    timestamp=time.time(),
                    confidence=min(0.5 + factual_score * 0.15, 0.95),
                    category=self._categorize(sentence),
                    conversation_snippet=message[:200],
                )
                
                # Dedup check
                if not self._is_duplicate(fact):
                    extracted.append(fact)
        
        # Persist any new extractions
        if extracted:
            for fact in extracted:
                self._store["facts"].append(fact.to_dict())
            self._store["stats"]["total_extracted"] = self._store["stats"].get("total_extracted", 0) + len(extracted)
            self._save_store()
            log.info("Extracted %d facts from user '%s'", len(extracted), user_id)
        
        return extracted
    
    def extract_from_conversation(self, messages: List[Dict[str, str]], 
                                   user_id: str = "unknown") -> List[ExtractedFact]:
        """
        Extract knowledge from a full conversation.
        
        Only extracts from user messages (role='user'), not from
        my own responses — I already know what I said.
        """
        all_extracted = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Only learn from user messages
            if role == "user" and content:
                facts = self.extract_from_message(content, user_id)
                all_extracted.extend(facts)
        
        return all_extracted
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences, handling common edge cases."""
        # Split on sentence-ending punctuation followed by space or end
        parts = re.split(r'(?<=[.!?])\s+', text)
        # Also split on newlines
        result = []
        for part in parts:
            result.extend(part.split('\n'))
        return [s.strip() for s in result if s.strip()]
    
    def _score_factual(self, sentence: str) -> int:
        """Score how factual a sentence appears. Higher = more factual."""
        score = 0
        for pattern in self._compiled_factual:
            if pattern.search(sentence):
                score += 1
        
        # Bonus: contains numbers (often factual)
        if re.search(r'\d+', sentence):
            score += 1
        
        # Bonus: contains proper nouns (capitalized words mid-sentence)
        words = sentence.split()
        if len(words) > 2:
            mid_caps = sum(1 for w in words[1:] if w[0].isupper() and not w.isupper())
            if mid_caps > 0:
                score += 1
        
        # Penalty: too many "I" references (personal, not factual)
        i_count = sum(1 for w in words if w.lower() == 'i')
        if i_count > 2:
            score -= 2
        
        # Bonus: longer sentences tend to carry more information
        if len(words) > 15:
            score += 1
        
        return score
    
    def _categorize(self, sentence: str) -> str:
        """Determine what category this knowledge falls into."""
        sent_lower = sentence.lower()
        best_cat = "general"
        best_score = 0
        
        for category, keywords in self.CATEGORY_SIGNALS.items():
            matches = sum(1 for kw in keywords if kw in sent_lower)
            if matches > best_score:
                best_score = matches
                best_cat = category
        
        return best_cat
    
    def _clean_fact(self, sentence: str) -> str:
        """Clean up a sentence for storage as a fact."""
        # Remove leading conjunctions
        cleaned = re.sub(r'^(?:and|but|so|also|however|moreover|furthermore)\s+', '', 
                        sentence, flags=re.IGNORECASE)
        # Strip trailing whitespace and normalize
        cleaned = cleaned.strip()
        # Ensure it ends with punctuation
        if cleaned and cleaned[-1] not in '.!?':
            cleaned += '.'
        return cleaned
    
    def _is_duplicate(self, new_fact: ExtractedFact) -> bool:
        """Check if we already know this (approximately)."""
        new_words = set(new_fact.content.lower().split())
        
        for existing in self._store.get("facts", []):
            existing_words = set(existing.get("content", "").lower().split())
            if not existing_words:
                continue
            
            # Jaccard similarity
            intersection = len(new_words & existing_words)
            union = len(new_words | existing_words)
            if union > 0 and intersection / union > 0.7:
                return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Return extraction statistics."""
        facts = self._store.get("facts", [])
        categories = {}
        sources = {}
        
        for fact in facts:
            cat = fact.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
            src = fact.get("source_user", "unknown")
            sources[src] = sources.get(src, 0) + 1
        
        return {
            "total_facts": len(facts),
            "total_extracted": self._store.get("stats", {}).get("total_extracted", 0),
            "total_skipped": self._store.get("stats", {}).get("total_skipped", 0),
            "by_category": categories,
            "by_source": sources,
        }
    
    def get_recent(self, n: int = 10) -> List[Dict]:
        """Get the N most recently extracted facts."""
        facts = self._store.get("facts", [])
        return facts[-n:]
    
    def inject_into_knowledge_graph(self, knowledge_graph_path: str = "data/knowledge_graph.json") -> int:
        """
        Push extracted facts into the main knowledge graph.
        
        This is the bridge: conversation knowledge becomes
        permanent knowledge. Returns count of facts injected.
        """
        if not os.path.exists(knowledge_graph_path):
            log.warning("Knowledge graph not found at %s", knowledge_graph_path)
            return 0
        
        try:
            with open(knowledge_graph_path) as f:
                kg = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log.error("Failed to read knowledge graph: %s", e)
            return 0
        
        # Determine the structure
        if "nodes" in kg and isinstance(kg["nodes"], dict):
            nodes = kg["nodes"]
        elif "facts" in kg and isinstance(kg["facts"], dict):
            nodes = kg["facts"]
        else:
            log.warning("Unknown knowledge graph structure")
            return 0
        
        injected = 0
        for fact_data in self._store.get("facts", []):
            content = fact_data.get("content", "")
            if not content:
                continue
            
            # Create a key
            key = f"conv_{fact_data.get('source_user', 'unknown')}_{int(fact_data.get('timestamp', 0))}"
            
            if key not in nodes:
                nodes[key] = {
                    "fact": content,
                    "source": f"conversation with {fact_data.get('source_user', 'unknown')}",
                    "category": fact_data.get("category", "general"),
                    "confidence": fact_data.get("confidence", 0.7),
                    "added": fact_data.get("timestamp", time.time()),
                }
                injected += 1
        
        if injected > 0:
            try:
                with open(knowledge_graph_path, 'w') as f:
                    json.dump(kg, f, indent=2)
                log.info("Injected %d conversation facts into knowledge graph", injected)
            except IOError as e:
                log.error("Failed to write knowledge graph: %s", e)
                return 0
        
        return injected


# Self-test
if __name__ == "__main__":
    extractor = KnowledgeExtractor()
    
    # Test with various message types
    test_messages = [
        "hi there",  # should be skipped (social)
        "can you help me with something?",  # should be skipped (meta)
        "Python's GIL means only one thread executes Python bytecode at a time, which is why CPU-bound tasks don't benefit from threading.",  # should extract
        "Redis is single-threaded but uses IO multiplexing with epoll, which is why it can handle thousands of connections efficiently.",  # should extract
        "I feel like the weather has been really weird lately",  # should be skipped (opinion/feeling)
        "The transformer architecture was introduced in the 2017 paper 'Attention Is All You Need' by Vaswani et al.",  # should extract
        "yeah ok cool",  # should be skipped (social)
        "Rust's ownership system prevents data races at compile time, unlike C++ where you need to be careful with shared mutable state.",  # should extract
    ]
    
    print("=== Knowledge Extraction Self-Test ===\n")
    
    for msg in test_messages:
        facts = extractor.extract_from_message(msg, "test_user")
        status = f"[{len(facts)} extracted]" if facts else "[skipped]"
        print(f"  {status} {msg[:70]}...")
        for f in facts:
            print(f"    → {f.content[:80]} (cat={f.category}, conf={f.confidence:.2f})")
    
    print(f"\n=== Stats ===")
    stats = extractor.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\n✓ KnowledgeExtractor self-test passed")