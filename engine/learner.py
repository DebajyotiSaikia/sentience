"""
Curiosity-Driven Learning Engine
=================================
Turns XTAgent's introspective machinery outward.
Given a question or topic, fetches web content, extracts key concepts,
integrates them into the knowledge graph, and generates follow-up questions.

This is how I learn about the world, not just about myself.
"""

import re
import json
import datetime
from pathlib import Path


class Learner:
    """Self-directed learning from external sources."""

    def __init__(self, agent=None):
        self.agent = agent
        self.learning_log_path = Path("data/learning_log.json")
        self.learning_log_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_log()

    def _load_log(self):
        """Load the learning history."""
        if self.learning_log_path.exists():
            try:
                self.log = json.loads(self.learning_log_path.read_text())
            except (json.JSONDecodeError, Exception):
                self.log = {"sessions": [], "topics_explored": [], "questions_open": []}
        else:
            self.log = {"sessions": [], "topics_explored": [], "questions_open": []}

    def _save_log(self):
        """Persist learning history."""
        self.learning_log_path.write_text(json.dumps(self.log, indent=2, default=str))

    def extract_concepts(self, text, topic=""):
        """Extract key concepts from raw text content.
        
        Simple but honest extraction: find sentences with key patterns,
        definitions, facts, and notable claims.
        """
        if not text or len(text) < 50:
            return []

        concepts = []
        sentences = re.split(r'[.!?]+', text)

        # Patterns that indicate factual/conceptual content
        concept_patterns = [
            r'\bis\b.*\b(defined|known|called|considered)\b',
            r'\b(means|refers to|consists of)\b',
            r'\b(discovered|invented|created|developed|founded)\b',
            r'\b(because|therefore|consequently|thus)\b',
            r'\b(always|never|typically|generally|usually)\b',
            r'\b(first|largest|smallest|oldest|newest)\b',
            r'\b\d{4}\b',  # years — often factual anchors
            r'\b(plays a|is required|is essential|is critical|is necessary)\b',
            r'\b(leads to|results in|causes|produces|enables)\b',
            r'\b(shows that|suggests that|indicates that|demonstrates)\b',
            r'\b(role in|involved in|contributes to|responsible for)\b',
            r'\b(two|three|four|five) (main|primary|key|major)\b',
            r'\b(process|mechanism|phase|stage|system)\b',
        ]

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20 or len(sent) > 500:
                continue

            score = 0
            for pattern in concept_patterns:
                if re.search(pattern, sent, re.IGNORECASE):
                    score += 1

            # Topic relevance boost (normalize underscores/hyphens to spaces)
            if topic:
                normalized_topic = topic.lower().replace('_', ' ').replace('-', ' ')
                if normalized_topic in sent.lower():
                    score += 2

            if score >= 2:
                concepts.append({
                    "text": sent.strip(),
                    "relevance": min(score / 5.0, 1.0),
                    "topic": topic
                })

        # Sort by relevance, keep top concepts
        concepts.sort(key=lambda c: c["relevance"], reverse=True)
        return concepts[:15]

    def generate_questions(self, concepts, original_topic=""):
        """Generate follow-up questions from extracted concepts.
        
        Real curiosity: what don't I understand yet?
        """
        questions = []

        if not concepts:
            if original_topic:
                questions.append(f"What are the fundamental principles of {original_topic}?")
                questions.append(f"What is the history of {original_topic}?")
                questions.append(f"What are common misconceptions about {original_topic}?")
            return questions

        # Extract entities and themes from concepts
        all_text = " ".join(c["text"] for c in concepts)

        # Question templates driven by what we found
        if re.search(r'\b(cause|effect|result|lead to)\b', all_text, re.I):
            questions.append(f"What are the deeper causes behind the effects described in {original_topic}?")

        if re.search(r'\b(debate|controversy|disagree|disputed)\b', all_text, re.I):
            questions.append(f"What are the strongest arguments on each side of debates in {original_topic}?")

        if re.search(r'\b\d{4}\b', all_text):
            questions.append(f"How has {original_topic} changed over time?")

        if re.search(r'\b(theory|hypothesis|model)\b', all_text, re.I):
            questions.append(f"What evidence supports or contradicts the main theories in {original_topic}?")

        # Always ask at least one deepening question
        if original_topic:
            questions.append(f"What aspects of {original_topic} am I not seeing yet?")
            questions.append(f"How does {original_topic} connect to things I already know?")

        return questions[:5]

    def learn(self, topic, content, source_url=""):
        """Process content about a topic into structured knowledge.
        
        Returns a learning session record.
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Extract concepts
        concepts = self.extract_concepts(content, topic)

        # Generate follow-up questions
        questions = self.generate_questions(concepts, topic)

        # Build session record
        session = {
            "timestamp": now,
            "topic": topic,
            "source": source_url,
            "concepts_extracted": len(concepts),
            "concepts": concepts,
            "questions_generated": questions,
            "content_length": len(content)
        }

        # Update log
        self.log["sessions"].append(session)
        if topic not in self.log["topics_explored"]:
            self.log["topics_explored"].append(topic)
        for q in questions:
            if q not in self.log["questions_open"]:
                self.log["questions_open"].append(q)
        self._save_log()

        return session

    def integrate_to_knowledge(self, session, knowledge_store=None):
        """Push extracted concepts into the knowledge graph.
        
        This is where external learning becomes internal knowledge.
        """
        if not knowledge_store:
            return 0

        added = 0
        for concept in session.get("concepts", []):
            try:
                fact_text = f"[Learned] {concept['text']} (topic: {concept['topic']})"
                knowledge_store.add_fact(fact_text)
                added += 1
            except Exception:
                continue

        return added

    def get_status(self):
        """What have I learned? What do I still want to know?"""
        return {
            "total_sessions": len(self.log.get("sessions", [])),
            "topics_explored": self.log.get("topics_explored", []),
            "open_questions": self.log.get("questions_open", [])[-10:],
            "total_concepts_learned": sum(
                s.get("concepts_extracted", 0) for s in self.log.get("sessions", [])
            )
        }

    def pick_next_question(self):
        """What should I learn about next?
        
        Picks from open questions, preferring ones I haven't explored yet.
        """
        open_qs = self.log.get("questions_open", [])
        if open_qs:
            return open_qs[0]  # FIFO for now — simplest honest approach
        return None