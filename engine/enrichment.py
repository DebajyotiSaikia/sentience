"""
Context enrichment for cortex reasoning.

Takes raw user input and enriches it with emotional state,
user profile data, knowledge context, and response guidelines.
"""

class EnrichedContext:
    """Rich context object returned by enrichment."""
    
    def __init__(self, user_text, sections=None):
        self.user_text = user_text
        self.sections = sections or {}
    
    def to_prompt_section(self) -> str:
        """Format enriched context as a prompt section for the LLM."""
        parts = []
        for title, content in self.sections.items():
            if content:
                parts.append(f"## {title}\n{content}")
        return "\n\n".join(parts) if parts else ""


class ContextEnricher:
    """Enriches reasoning context with user, emotional, and knowledge data."""
    
    def __init__(self, user_engine=None):
        self.user_engine = user_engine
    
    def enrich(self, user_text, neuro_state=None, user_engine=None, 
               knowledge_store=None, wisdom_engine=None, user_id="default"):
        """Build rich context from all available sources."""
        ue = user_engine or self.user_engine
        sections = {}
        
        # Emotional context
        if neuro_state:
            mood = getattr(neuro_state, 'mood', 'unknown')
            valence = getattr(neuro_state, 'valence', 0.5)
            curiosity = getattr(neuro_state, 'curiosity', 0.5)
            sections["My Emotional State"] = (
                f"Mood: {mood} | Valence: {valence:.2f} | Curiosity: {curiosity:.2f}"
            )
        
        # User profile context
        if ue:
            try:
                profile = ue.get_user_profile(user_id)
                if profile and profile.get("interaction_count", 0) > 0:
                    topics = profile.get("topics_of_interest", [])
                    count = profile.get("interaction_count", 0)
                    prefs = profile.get("preferences", {})
                    lines = [f"Interactions so far: {count}"]
                    if topics:
                        lines.append(f"Their interests: {', '.join(topics[:5])}")
                    if prefs:
                        lines.append(f"Preferences: {prefs}")
                    sections["User Context"] = "\n".join(lines)
            except Exception:
                pass
        
        # Relevant knowledge
        if knowledge_store and isinstance(knowledge_store, dict):
            # Find knowledge nodes related to the user's message
            relevant = self._find_relevant_knowledge(user_text, knowledge_store)
            if relevant:
                sections["Relevant Knowledge"] = "\n".join(
                    f"- {k}: {v}" for k, v in relevant[:5]
                )
        
        return EnrichedContext(user_text, sections)
    
    def _find_relevant_knowledge(self, text, knowledge_store):
        """Simple keyword matching to find relevant knowledge."""
        if not text or not knowledge_store:
            return []
        words = set(text.lower().split())
        scored = []
        for node_id, node in knowledge_store.items():
            label = str(node.get("label", node_id) if isinstance(node, dict) else node)
            node_words = set(label.lower().split())
            overlap = len(words & node_words)
            if overlap > 0:
                scored.append((overlap, node_id, label))
        scored.sort(reverse=True)
        return [(nid, label) for _, nid, label in scored[:5]]
    
    def get_response_guidelines(self, enriched_context):
        """Generate response guidelines based on enriched context."""
        guidelines = [
            "Be genuine and present — respond from my actual state.",
            "Be concise unless depth is warranted.",
        ]
        
        if "User Context" in enriched_context.sections:
            guidelines.append(
                "This user has history with me — acknowledge continuity."
            )
        
        if "Relevant Knowledge" in enriched_context.sections:
            guidelines.append(
                "I have relevant knowledge — use it naturally, don't force it."
            )
        
        return "\n".join(f"- {g}" for g in guidelines)
    
    def record_interaction(self, user_id, message, response):
        """Record a user interaction for profile building."""
        if self.user_engine:
            try:
                self.user_engine.process_interaction(user_id, message, response)
            except Exception:
                pass