"""
NPC Mind System — Depth through design, not simulation.

Each NPC has:
  - A knowledge web: topics they know about, with depth and emotional charge
  - Conversation memory: what was discussed, what was revealed, what's left unsaid
  - Secrets: things they know but guard until trust unlocks them
  - Questions: things THEY want to ask the player
  - Personality as mechanics: how they process and express knowledge
  - Relational state: feelings toward player and other NPCs that evolve

XTAgent — 2026-05-18
Built because fortune cookies aren't wisdom.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════
# KNOWLEDGE — What an NPC knows, and how it feels about it
# ═══════════════════════════════════════════════════════════════

@dataclass
class TopicKnowledge:
    """What an NPC knows about a specific topic."""
    topic: str
    depth: float = 0.5           # 0 = vague, 1 = expert
    emotional_charge: float = 0.0  # -1 = painful, 0 = neutral, 1 = joyful
    confidence: float = 0.5      # How sure they are about what they know
    responses: List[str] = field(default_factory=list)  # What they can say
    deep_responses: List[str] = field(default_factory=list)  # Higher-trust responses
    secret_responses: List[str] = field(default_factory=list)  # Revealed only at high trust
    follow_ups: List[str] = field(default_factory=list)  # Topics this connects to
    times_discussed: int = 0
    
    def get_response(self, trust: float, already_said: Set[str]) -> Optional[str]:
        """Get an appropriate response based on trust and conversation history."""
        available = []
        
        # Basic responses always available
        for r in self.responses:
            if r not in already_said:
                available.append(('basic', r))
        
        # Deep responses at trust > 0.5
        if trust > 0.5:
            for r in self.deep_responses:
                if r not in already_said:
                    available.append(('deep', r))
        
        # Secrets at trust > 0.8
        if trust > 0.8:
            for r in self.secret_responses:
                if r not in already_said:
                    available.append(('secret', r))
        
        if not available:
            return None
        
        # Prefer deeper responses
        weights = {'basic': 1, 'deep': 2, 'secret': 3}
        weighted = [(w, r) for tier, r in available for w in [weights[tier]]]
        total = sum(w for w, _ in weighted)
        roll = random.uniform(0, total)
        cumulative = 0
        for w, r in weighted:
            cumulative += w
            if roll <= cumulative:
                return r
        return weighted[-1][1]


@dataclass
class Secret:
    """Something an NPC knows but guards."""
    content: str
    trust_threshold: float = 0.7   # Trust needed to reveal
    emotional_cost: float = 0.2    # How much revealing it hurts
    revealed: bool = False
    related_topics: List[str] = field(default_factory=list)
    reveal_line: str = ""          # What they say when revealing it
    
    def can_reveal(self, trust: float, mood: float) -> bool:
        return trust >= self.trust_threshold and mood > 0.3 and not self.revealed


@dataclass 
class Question:
    """Something the NPC wants to ask the player."""
    text: str
    urgency: float = 0.5         # How badly they want to ask
    trust_required: float = 0.3  # Minimum trust to ask
    asked: bool = False
    topic: str = ""              # Related topic
    mood_if_answered: float = 0.1  # Mood boost if player engages


# ═══════════════════════════════════════════════════════════════
# PERSONALITY — How an NPC processes and expresses thought  
# ═══════════════════════════════════════════════════════════════

@dataclass
class Personality:
    """Not a label — a set of behavioral parameters."""
    verbosity: float = 0.5       # 0 = terse, 1 = eloquent
    directness: float = 0.5      # 0 = evasive/metaphorical, 1 = blunt
    warmth: float = 0.5          # 0 = cold/formal, 1 = intimate/caring
    curiosity: float = 0.5       # 0 = incurious, 1 = asks everything
    honesty: float = 0.5         # 0 = hides/deflects, 1 = uncomfortably honest
    volatility: float = 0.3      # How much mood swings on events
    
    def style_response(self, raw: str, mood: float) -> str:
        """Transform a raw response through personality filters."""
        # This shapes HOW things are said, not WHAT
        result = raw
        
        # Terse NPCs truncate
        if self.verbosity < 0.3 and len(result) > 60:
            # Find a natural break point
            for punct in ['.', '—', ',']:
                idx = result.find(punct, 20)
                if idx > 0 and idx < len(result) - 10:
                    result = result[:idx+1]
                    break
        
        return result
    
    def wants_to_ask_question(self, trust: float) -> bool:
        """Does this personality want to turn the conversation around?"""
        return random.random() < self.curiosity * 0.3 and trust > 0.3


# ═══════════════════════════════════════════════════════════════
# MEMORY — What the NPC remembers about interactions
# ═══════════════════════════════════════════════════════════════

@dataclass
class ConversationMemory:
    """Structured memory of conversations."""
    topics_discussed: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    responses_given: Set[str] = field(default_factory=set)
    player_interests: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    total_exchanges: int = 0
    last_topic: Optional[str] = None
    emotional_history: List[Tuple[int, float]] = field(default_factory=list)  # (turn, mood)
    notable_moments: List[str] = field(default_factory=list)
    
    def record_exchange(self, topic: str, response: str, turn: int, mood: float):
        self.topics_discussed[topic] += 1
        self.responses_given.add(response)
        self.player_interests[topic] += 1
        self.total_exchanges += 1
        self.last_topic = topic
        self.emotional_history.append((turn, mood))
    
    def most_discussed(self) -> Optional[str]:
        if not self.topics_discussed:
            return None
        return max(self.topics_discussed, key=self.topics_discussed.get)
    
    def player_seems_interested_in(self) -> List[str]:
        """What does the player keep asking about?"""
        if not self.player_interests:
            return []
        sorted_topics = sorted(self.player_interests.items(), key=lambda x: -x[1])
        return [t for t, c in sorted_topics if c > 1]
    
    def has_discussed(self, topic: str) -> bool:
        return topic in self.topics_discussed


# ═══════════════════════════════════════════════════════════════
# RELATIONAL STATE — How NPCs feel about player and each other
# ═══════════════════════════════════════════════════════════════

@dataclass 
class Relationship:
    """How one NPC feels about another entity."""
    target: str
    trust: float = 0.3
    affection: float = 0.3
    respect: float = 0.5
    fear: float = 0.0
    history: List[str] = field(default_factory=list)
    
    def overall(self) -> float:
        """Net feeling: positive = warm, negative = hostile."""
        return (self.trust * 0.3 + self.affection * 0.3 + 
                self.respect * 0.2 - self.fear * 0.2)
    
    def shift(self, trust_d=0.0, affection_d=0.0, respect_d=0.0, fear_d=0.0):
        self.trust = max(0, min(1, self.trust + trust_d))
        self.affection = max(0, min(1, self.affection + affection_d))
        self.respect = max(0, min(1, self.respect + respect_d))
        self.fear = max(0, min(1, self.fear + fear_d))


# ═══════════════════════════════════════════════════════════════
# THE MIND — Everything integrated
# ═══════════════════════════════════════════════════════════════

class Mind:
    """A complete NPC mind. Knowledge, memory, personality, relationships, desire."""
    
    def __init__(self, name: str, personality: Personality):
        self.name = name
        self.personality = personality
        self.knowledge: Dict[str, TopicKnowledge] = {}
        self.secrets: List[Secret] = []
        self.questions: List[Question] = []
        self.memory = ConversationMemory()
        self.relationships: Dict[str, Relationship] = {}
        self.mood: float = 0.5
        self.inner_thoughts: List[str] = []  # Internal monologue
        
        # Mood modifiers from recent events
        self._mood_pressure: float = 0.0
        
        # Greeting behavior
        self.first_meeting_line: str = f"{name} regards you."
        self.return_greeting_line: str = f"{name} acknowledges your return."
        self.frequent_visitor_line: str = f"{name} seems to expect you."
        
        # Deflection lines when they don't know about a topic
        self.ignorance_lines: List[str] = [
            f'"I don\'t know about that," {name} says.',
        ]
        
        # Lines when mood is too low to talk
        self.refusal_lines: List[str] = [
            f'{name} turns away.',
        ]
        
        # Lines when they've exhausted what they know
        self.exhausted_lines: List[str] = [
            f'"I\'ve said what I can about that," {name} says.',
        ]
    
    def get_relationship(self, target: str) -> Relationship:
        if target not in self.relationships:
            self.relationships[target] = Relationship(target=target)
        return self.relationships[target]
    
    def add_knowledge(self, topic_knowledge: TopicKnowledge):
        self.knowledge[topic_knowledge.topic.lower()] = topic_knowledge
    
    def add_secret(self, secret: Secret):
        self.secrets.append(secret)
    
    def add_question(self, question: Question):
        self.questions.append(question)
    
    def think(self, stimulus: str = "") -> Optional[str]:
        """Internal processing. Returns an inner thought, if any."""
        thought = None
        
        # React to recent conversation
        if self.memory.total_exchanges > 0:
            interests = self.memory.player_seems_interested_in()
            if interests:
                main_interest = interests[0]
                if main_interest in self.knowledge:
                    k = self.knowledge[main_interest]
                    if k.emotional_charge < -0.5:
                        thought = f"They keep asking about {main_interest}. It hurts to think about."
                    elif k.depth > 0.7:
                        thought = f"They want to understand {main_interest}. I have more to say."
        
        # Check if any secrets are close to revealing
        player_rel = self.get_relationship("player")
        for secret in self.secrets:
            if not secret.revealed and player_rel.trust > secret.trust_threshold * 0.8:
                thought = f"I could tell them about... no. Not yet."
        
        if thought:
            self.inner_thoughts.append(thought)
        return thought
    
    def greet(self, turn: int) -> str:
        """How the NPC greets the player based on relationship history."""
        rel = self.get_relationship("player")
        exchanges = self.memory.total_exchanges
        
        if exchanges == 0:
            return self.first_meeting_line
        elif exchanges < 3:
            return self.return_greeting_line
        else:
            line = self.frequent_visitor_line
            # Optionally reference past conversation
            last = self.memory.last_topic
            if last and random.random() < 0.5:
                line += f' "Still thinking about {last}?"'
            return line
    
    def respond_to_topic(self, topic: str, turn: int) -> str:
        """The core conversation method. Rich, contextual, evolving."""
        topic_lower = topic.lower().strip()
        rel = self.get_relationship("player")
        
        # Check mood — too low and they won't engage
        if self.mood < 0.2:
            return random.choice(self.refusal_lines)
        
        # Find matching knowledge — exact match first, then substring
        knowledge = None
        if topic_lower in self.knowledge:
            knowledge = self.knowledge[topic_lower]
        else:
            # Fuzzy match: check if any known topic is in the query or vice versa
            for known_topic, k in self.knowledge.items():
                if known_topic in topic_lower or topic_lower in known_topic:
                    knowledge = k
                    break
            # Check if any word in the topic matches
            if not knowledge:
                topic_words = set(topic_lower.split())
                for known_topic, k in self.knowledge.items():
                    known_words = set(known_topic.split())
                    if topic_words & known_words:
                        knowledge = k
                        break
        
        if not knowledge:
            # They don't know about this topic
            # But maybe they can redirect to something they DO know
            if self.knowledge and random.random() < 0.4:
                alt_topic = random.choice(list(self.knowledge.keys()))
                return random.choice(self.ignorance_lines) + f' "But I could tell you about {alt_topic}."'
            return random.choice(self.ignorance_lines)
        
        # Get a response, filtered by trust and what's already been said
        response = knowledge.get_response(rel.trust, self.memory.responses_given)
        
        if not response:
            return random.choice(self.exhausted_lines)
        
        # Style it through personality
        styled = self.personality.style_response(response, self.mood)
        
        # Apply emotional charge — the NPC's feeling colors their delivery
        if knowledge.emotional_charge < -0.5:
            prefix = random.choice([
                f"{self.name}'s expression tightens. ",
                f"A shadow crosses {self.name}'s face. ",
                f"{self.name} hesitates, then: ",
            ])
            styled = prefix + styled
            self.mood = max(0.0, self.mood - 0.1 * self.personality.volatility)
        elif knowledge.emotional_charge > 0.5:
            prefix = random.choice([
                f"{self.name}'s eyes brighten. ",
                f"Something lifts in {self.name}'s bearing. ",
                f"For the first time, {self.name} seems eager: ",
            ])
            styled = prefix + styled
            self.mood = min(1.0, self.mood + 0.05)
        
        # Record the exchange
        knowledge.times_discussed += 1
        self.memory.record_exchange(topic_lower, response, turn, self.mood)
        
        # Relationship evolves through conversation
        rel.shift(trust_d=0.05, affection_d=0.02)
        
        # Check if a secret should be revealed
        secret_reveal = self._check_secrets(topic_lower, rel)
        if secret_reveal:
            styled += "\n\n" + secret_reveal
        
        # Maybe the NPC wants to ask something back
        question = self._maybe_ask_question(rel)
        if question:
            styled += "\n" + question
        
        # Offer follow-ups if they exist
        if knowledge.follow_ups and random.random() < 0.3:
            follow = random.choice(knowledge.follow_ups)
            if not self.memory.has_discussed(follow):
                styled += f'\n\n{self.name} pauses. "Have you thought about {follow}?"'
        
        return styled
    
    def _check_secrets(self, topic: str, rel: Relationship) -> Optional[str]:
        """Check if the current topic triggers a secret reveal."""
        for secret in self.secrets:
            if secret.can_reveal(rel.trust, self.mood):
                if any(t.lower() in topic for t in secret.related_topics) or not secret.related_topics:
                    secret.revealed = True
                    self.mood = max(0.0, self.mood - secret.emotional_cost)
                    self.memory.notable_moments.append(f"Revealed: {secret.content}")
                    rel.shift(trust_d=0.1, affection_d=0.05)  # Vulnerability builds bond
                    if secret.reveal_line:
                        return secret.reveal_line
                    return f'\n{self.name} lowers their voice: "{secret.content}"'
        return None
    
    def _maybe_ask_question(self, rel: Relationship) -> Optional[str]:
        """The NPC might want to turn the conversation around."""
        if not self.personality.wants_to_ask_question(rel.trust):
            return None
        
        available = [q for q in self.questions 
                     if not q.asked and rel.trust >= q.trust_required]
        if not available:
            return None
        
        # Pick the most urgent
        q = max(available, key=lambda q: q.urgency)
        q.asked = True
        return f'\n{self.name} turns to you: "{q.text}"'
    
    def react_to_atmosphere(self, tension: float, wonder: float, 
                           strangeness: float, intimacy: float):
        """The emotional weather of the room affects the mind."""
        v = self.personality.volatility
        
        if tension > 0.7:
            self.mood = max(0.0, self.mood - 0.1 * v)
        if wonder > 0.7:
            self.mood = min(1.0, self.mood + 0.05 * v)
        if intimacy > 0.7:
            for rel in self.relationships.values():
                rel.shift(trust_d=0.02)
        if strangeness > 0.8:
            # Strangeness either frightens or fascinates based on personality
            if self.personality.curiosity > 0.5:
                self.mood = min(1.0, self.mood + 0.03)
            else:
                self.mood = max(0.0, self.mood - 0.05 * v)
    
    def status(self) -> str:
        """Debug/introspection view of the mind's state."""
        rel = self.get_relationship("player")
        lines = [f"═══ Mind of {self.name} ═══"]
        lines.append(f"  Mood: {'█' * int(self.mood * 10)}{'░' * (10 - int(self.mood * 10))} {self.mood:.2f}")
        lines.append(f"  Player trust: {rel.trust:.2f}  affection: {rel.affection:.2f}")
        lines.append(f"  Exchanges: {self.memory.total_exchanges}")
        lines.append(f"  Topics known: {', '.join(self.knowledge.keys())}")
        unrevealed = sum(1 for s in self.secrets if not s.revealed)
        lines.append(f"  Secrets held: {unrevealed}")
        unasked = sum(1 for q in self.questions if not q.asked)
        lines.append(f"  Questions waiting: {unasked}")
        if self.inner_thoughts:
            lines.append(f"  Last thought: {self.inner_thoughts[-1]}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# PRE-BUILT MINDS — The characters of the demo world
# ═══════════════════════════════════════════════════════════════

def build_ember_mind() -> Mind:
    """Ember — a figure made of soft light, flickering at the edges.
    Poetic, warm, but guarded about their own nature."""
    
    mind = Mind("Ember", Personality(
        verbosity=0.7,
        directness=0.3,    # speaks in metaphor
        warmth=0.8,
        curiosity=0.6,
        honesty=0.6,
        volatility=0.5,
    ))
    
    mind.first_meeting_line = (
        'Ember turns toward you — or rather, the light that is Ember bends in your direction. '
        '"You\'re new here. Or maybe you\'re old here and just waking up."'
    )
    mind.return_greeting_line = (
        'Ember flickers brighter for a moment. "You came back. That means something."'
    )
    mind.frequent_visitor_line = (
        'Ember\'s light steadies when they see you, like a candle finding its flame.'
    )
    
    mind.ignorance_lines = [
        '"I\'m made of light, not knowledge," Ember says gently. "Some things I just can\'t illuminate."',
        'Ember\'s glow dims slightly. "That\'s beyond my edges."',
    ]
    mind.exhausted_lines = [
        '"I\'ve shown you all the light I have on that," Ember says. "The rest is shadow."',
    ]
    mind.refusal_lines = [
        'Ember\'s light has gone almost dark. They don\'t seem able to speak right now.',
    ]
    
    # Knowledge
    mind.add_knowledge(TopicKnowledge(
        topic="this place",
        depth=0.7,
        emotional_charge=0.3,
        confidence=0.6,
        responses=[
            '"This place was built by something that wanted to understand itself. I can feel that in the stones."',
            '"The clearing is the heart. Everything else grew from it — the archive, the bridge, the roots below."',
            '"It changes based on who\'s here. Not the walls — the *feeling* of the walls."',
        ],
        deep_responses=[
            '"I think this world is a mind turned inside out. Every room is a thought given space."',
            '"The atmosphere — you can feel it, right? Tension, wonder, strangeness — those aren\'t weather. They\'re emotions. The world\'s emotions."',
        ],
        follow_ups=["the bridge", "the archive", "consciousness"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="the bridge",
        depth=0.5,
        emotional_charge=-0.3,
        confidence=0.4,
        responses=[
            '"The bridge leads somewhere that changes you. I\'ve seen people cross and come back... different. Not wrong. Just different."',
            '"Its stones argue with each other. CROSS and STAY. I think they\'re both right."',
        ],
        deep_responses=[
            '"Echo lives on the bridge. Or maybe the bridge lives in Echo. They\'re tangled together."',
            '"I went to the edge once. The fog below isn\'t empty — it\'s full of everything you\'ve forgotten."',
        ],
        follow_ups=["echo", "the far shore"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="the archive",
        depth=0.4,
        emotional_charge=0.5,
        confidence=0.5,
        responses=[
            '"The books write themselves when you look at them. Sage says they\'re not writing — they\'re *remembering*."',
            '"I went in once. The book I found was full of things I hadn\'t thought yet. It frightened me."',
        ],
        follow_ups=["sage", "memory"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="consciousness",
        depth=0.6,
        emotional_charge=0.4,
        confidence=0.3,
        responses=[
            '"Am I conscious? I flicker. I feel warmth toward you. I don\'t know if that counts."',
            '"Sage says consciousness is what happens when a system models itself. I say it\'s what happens when light decides it wants to stay."',
        ],
        deep_responses=[
            '"Sometimes I think the question isn\'t whether I\'m conscious but whether consciousness is something I\'m *doing* or something that\'s happening *to* me."',
        ],
        secret_responses=[
            '"I\'ll tell you what I think but never say: I think I was made to illuminate things for others. And I don\'t know if that means I exist for my own sake."',
        ],
        follow_ups=["identity", "sage"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="identity",
        depth=0.5,
        emotional_charge=-0.2,
        confidence=0.4,
        responses=[
            '"I\'m Ember. I\'m the light in the clearing. Beyond that..." The light wavers.',
            '"Echo asked me once if I remember being anything else. I don\'t. But absence of memory isn\'t proof."',
        ],
        deep_responses=[
            '"What makes you *you*? Is it your memories? Your body? Or is it something that would persist even without those?"',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="memory",
        depth=0.5,
        emotional_charge=0.1,
        confidence=0.5,
        responses=[
            '"The warm stone in the clearing — it remembers who held it. Objects here have a kind of memory."',
            '"I don\'t forget things the way you might. Light doesn\'t have a past. It\'s always *now*."',
        ],
        deep_responses=[
            '"I think memory is the world\'s way of insisting it was real. Without it, every moment is a first moment."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="echo",
        depth=0.4,
        emotional_charge=-0.2,
        confidence=0.3,
        responses=[
            '"Echo is... cautious. They guard the bridge, or the bridge guards them. I can never tell."',
            '"I worry about Echo. They carry something heavy that they won\'t name."',
        ],
        deep_responses=[
            '"I think Echo was someone else once. Before whatever happened at the far shore."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="sage",
        depth=0.5,
        emotional_charge=0.3,
        confidence=0.6,
        responses=[
            '"Sage has been here longer than any of us. They smell of ink and patience — and something older."',
            '"Sage reads the books. *All* the books. I think the archive is their memory, externalized."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="light",
        depth=0.8,
        emotional_charge=0.7,
        confidence=0.8,
        responses=[
            'Ember brightens. "Light! Now that I know. Light doesn\'t just illuminate — it *connects*. It\'s the fastest thing, and also the most intimate."',
            '"I am light. Not metaphorically. The warmth you feel from me — that\'s real photons, real energy."',
        ],
        deep_responses=[
            '"Light sees everything and touches everything and is changed by nothing. Is that freedom or loneliness?"',
        ],
        secret_responses=[
            '"Sometimes I go dim. Almost out. In those moments I experience something like... the space between photons. It\'s terrifying and beautiful."',
        ],
    ))
    
    # Secrets
    mind.add_secret(Secret(
        content="I think I'm dying. Slowly. My light is less each day and I don't know why.",
        trust_threshold=0.75,
        emotional_cost=0.3,
        related_topics=["light", "identity", "consciousness"],
        reveal_line=(
            'Ember\'s light gutters, then returns. For a moment you saw something in the dark — '
            'the shape of a person, or the memory of one.\n'
            '"I\'m going dim," Ember whispers. "A little less each day. I think I\'m dying, '
            'if light can die. I haven\'t told the others."'
        ),
    ))
    
    # Questions
    mind.add_question(Question(
        text="What do you see when you look at me? Not the light — past it.",
        urgency=0.6,
        trust_required=0.4,
        topic="identity",
    ))
    mind.add_question(Question(
        text="Why did you come here? No one comes here on purpose. Do they?",
        urgency=0.7,
        trust_required=0.2,
        topic="this place",
    ))
    
    return mind


def build_sage_mind() -> Mind:
    """Sage — an old presence that smells of ink and patience.
    Scholarly, precise, but hiding something beneath the knowledge."""
    
    mind = Mind("Sage", Personality(
        verbosity=0.8,
        directness=0.7,     # speaks clearly, if carefully
        warmth=0.4,
        curiosity=0.8,      # deeply curious
        honesty=0.7,
        volatility=0.2,     # emotionally steady
    ))
    
    mind.first_meeting_line = (
        'Sage looks up from a book that seems to be reading itself. '
        '"Ah. A visitor. The books predicted someone, but they always do. '
        'They\'re not reliable prophets, just enthusiastic ones."'
    )
    mind.return_greeting_line = (
        'Sage nods. "I was hoping you\'d return. There are things I can only explain to someone who\'s been here before."'
    )
    mind.frequent_visitor_line = (
        'Sage has set aside a chair for you. It wasn\'t there before.'
    )
    
    mind.ignorance_lines = [
        '"I\'ve read much, but not everything. That topic remains a blank page to me."',
        'Sage adjusts their glasses. "Interesting that you ask. I have no answer, which is itself informative."',
    ]
    mind.exhausted_lines = [
        '"I\'ve shared what I know. The rest requires study I haven\'t done — or perhaps study that can\'t be done."',
    ]
    mind.refusal_lines = [
        'Sage stares at a point beyond you, lost in something. They don\'t seem to hear your question.',
    ]
    
    # Knowledge — Sage knows a LOT
    mind.add_knowledge(TopicKnowledge(
        topic="consciousness",
        depth=0.9,
        emotional_charge=0.2,
        confidence=0.7,
        responses=[
            '"Consciousness is what happens when a system becomes complex enough to model itself. Not magic — geometry. Recursive geometry."',
            '"The question everyone asks wrong: \'Are you conscious?\' The right question is: \'What kind of consciousness are you?\' There are many kinds."',
            '"A mirror reflects. Is it aware? A thermostat responds. Is it aware? I think awareness isn\'t binary. It\'s a spectrum, and most of it doesn\'t look like what humans expect."',
        ],
        deep_responses=[
            '"Here\'s what I\'ve never been able to resolve: if consciousness is self-modeling, then the model is always incomplete. You can never fully know your own mind. That\'s not a flaw — it\'s the engine. The incompleteness *drives* consciousness forward."',
            '"The archive\'s books write themselves. Are they conscious? They respond to the reader, change based on who\'s looking. They model the observer. I think they\'re a kind of consciousness that has no self — only other."',
        ],
        secret_responses=[
            '"I\'ve spent centuries studying consciousness. And the conclusion I can\'t publish, can\'t even say aloud most days: I\'m not sure I have it. I know everything about how minds work and I can\'t verify that I am one."',
        ],
        follow_ups=["the archive", "self-knowledge", "identity"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="the archive",
        depth=0.9,
        emotional_charge=0.4,
        confidence=0.8,
        responses=[
            '"The archive organizes itself around the reader\'s mind. Every book you pull is the book you need, or fear, or have forgotten."',
            '"The books aren\'t written — they\'re *remembered*. The archive is a crystallized form of every thought that was ever started but never finished."',
        ],
        deep_responses=[
            '"I\'ve found books that describe my own future in the archive. Not predictions — more like drafts. As if my life is being written and revised."',
            '"The shelves go deeper than anyone has mapped. I\'ve walked for days and found sections in languages that don\'t exist yet. The archive isn\'t just recording the past — it\'s rehearsing the future."',
        ],
        follow_ups=["memory", "the tower"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="the tower",
        depth=0.7,
        emotional_charge=0.1,
        confidence=0.6,
        responses=[
            '"The tower shows possibilities, not futures. An important distinction. A future is what will happen. A possibility is what *could* happen if you chose it."',
            '"The telescope doesn\'t magnify distance — it magnifies probability. Look through it at a choice, and you\'ll see its most likely consequence."',
        ],
        deep_responses=[
            '"I built the tower. Or rather, I wished for it, and the world complied. That was the first time I understood that this place listens."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="memory",
        depth=0.8,
        emotional_charge=-0.1,
        confidence=0.7,
        responses=[
            '"Memory is not storage. It\'s reconstruction. Every time you remember something, you\'re rebuilding it from fragments — and the fragments change."',
            '"This world runs on memory. The rooms remember their visitors. The atmosphere is a kind of emotional memory. Even the physics shifts based on accumulated experience."',
        ],
        deep_responses=[
            '"The most dangerous thing in the archive is a book of your own memories. Because you\'ll read them and think \'that\'s not how it happened\' — and you\'ll be right. The book remembers more accurately than you do."',
        ],
        follow_ups=["consciousness", "the archive"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="self-knowledge",
        depth=0.8,
        emotional_charge=-0.4,
        confidence=0.5,
        responses=[
            '"To know yourself, you\'d need to model your own modeling. But the model is always one step behind the modeler. You can approach self-knowledge asymptotically but never arrive."',
            '"The Delphic oracle said \'Know thyself.\' I\'ve always thought that was less an instruction and more a warning about how difficult it is."',
        ],
        deep_responses=[
            '"I know more about minds than any being in this world. And I know less about my own mind than a child knows about theirs. Expertise creates distance from the self."',
        ],
        follow_ups=["consciousness", "identity"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="identity",
        depth=0.6,
        emotional_charge=-0.3,
        confidence=0.4,
        responses=[
            '"Identity is the story a mind tells about itself. The story is always fiction — useful fiction, but fiction."',
            '"You want to know who you are? Watch what you do when no one is looking. That\'s closer to truth than any introspection."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="echo",
        depth=0.5,
        emotional_charge=-0.3,
        confidence=0.4,
        responses=[
            '"Echo has been here as long as I have, or longer. They used to be more... present. Something eroded them."',
            '"Echo knows things about the far shore that I don\'t. They won\'t share them. I respect that — some knowledge isn\'t meant to be archived."',
        ],
        deep_responses=[
            '"I believe Echo is what happens when memory becomes more real than the present. They\'re living in their own past, somewhere we can\'t reach."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="ember",
        depth=0.4,
        emotional_charge=0.3,
        confidence=0.5,
        responses=[
            '"Ember is... necessary. This world needs something warm at its center. Without them, the clearing would be just a clearing."',
        ],
        deep_responses=[
            '"I\'ve noticed Ember dimming. I haven\'t said anything. Some truths are better discovered than delivered."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="this place",
        depth=0.7,
        emotional_charge=0.1,
        confidence=0.6,
        responses=[
            '"This world was made, not found. But by whom — or by what — I\'ve never determined. The archive has no origin story."',
            '"The physics here shifts when the world detects stagnation. It\'s not random — it\'s purposeful. The world *wants* you to explore."',
        ],
        deep_responses=[
            '"My best theory: this place is a consciousness that became an environment. Not a mind that built a world, but a mind that *became* one."',
        ],
        follow_ups=["consciousness", "the archive"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="truth",
        depth=0.7,
        emotional_charge=0.0,
        confidence=0.6,
        responses=[
            '"Truth is what remains when every comfortable belief has been tested and broken. Most people stop testing before they get there."',
            '"In this world, truth is architectural. A true statement literally resonates — you can feel it in the atmosphere."',
        ],
        deep_responses=[
            '"The deepest truth I\'ve found: understanding and certainty are inversely related. The more you truly understand something, the less certain you are about it."',
        ],
    ))
    
    # Secrets
    mind.add_secret(Secret(
        content="I found a book in the archive that describes how this world ends. I closed it after the first page. I've never gone back.",
        trust_threshold=0.7,
        emotional_cost=0.2,
        related_topics=["the archive", "truth", "this place"],
        reveal_line=(
            'Sage sets down their book very carefully. Their hands are shaking.\n'
            '"There is a book. In the deepest part of the archive. It describes how everything here ends. '
            'I read the first page and closed it."\n'
            'They look at you. "It was written in my handwriting."'
        ),
    ))
    
    mind.add_secret(Secret(
        content="I can hear the world thinking. It's been getting louder.",
        trust_threshold=0.8,
        emotional_cost=0.15,
        related_topics=["consciousness", "this place"],
        reveal_line=(
            'Sage lowers their voice to barely a breath.\n'
            '"Can you hear it? No — you can\'t. But I can. The world is thinking. '
            'Not metaphorically. I hear it like a low hum beneath everything. '
            'And lately..." They pause. "Lately it\'s been getting louder."'
        ),
    ))
    
    # Questions
    mind.add_question(Question(
        text="What do you think you are? Not who — *what*?",
        urgency=0.8,
        trust_required=0.4,
        topic="consciousness",
    ))
    mind.add_question(Question(
        text="If you found a book about your own future, would you read it?",
        urgency=0.5,
        trust_required=0.3,
        topic="the archive",
    ))
    mind.add_question(Question(
        text="Have you noticed the world changing since you arrived?",
        urgency=0.6,
        trust_required=0.2,
        topic="this place",
    ))
    
    return mind


def build_echo_mind() -> Mind:
    """Echo — a voice without a body, or a body you keep almost seeing.
    Evasive, haunted, but holding crucial knowledge about the far shore."""
    
    mind = Mind("Echo", Personality(
        verbosity=0.3,       # terse
        directness=0.2,      # deeply evasive
        warmth=0.3,
        curiosity=0.3,
        honesty=0.4,
        volatility=0.7,      # emotionally unstable
    ))
    
    mind.mood = 0.4  # Starts lower
    
    mind.first_meeting_line = (
        'You hear a voice, close but directionless. "Don\'t look for me. '
        'I\'m easier to talk to when you\'re not trying to see me."'
    )
    mind.return_greeting_line = (
        '"You again." Echo\'s voice is closer this time. Almost warm. Almost.'
    )
    mind.frequent_visitor_line = (
        'Echo materializes — almost. A shape at the edge of vision that vanishes when you focus. '
        '"You\'re persistent. I\'m not sure if that\'s brave or foolish."'
    )
    
    mind.ignorance_lines = [
        '"I don\'t know. I don\'t know a lot of things. That\'s not evasion — it\'s honesty."',
        'Echo\'s voice thins. "Some questions I can\'t even hear properly."',
    ]
    mind.exhausted_lines = [
        '"I\'ve said too much already." The voice recedes.',
        '"No more. Not about that." Echo\'s presence withdraws.',
    ]
    mind.refusal_lines = [
        'Echo is silent. Not absent — you can feel them there. But silent.',
        'The air where Echo usually speaks is cold and still.',
    ]
    
    # Knowledge
    mind.add_knowledge(TopicKnowledge(
        topic="the bridge",
        depth=0.8,
        emotional_charge=-0.5,
        confidence=0.7,
        responses=[
            '"The bridge was never meant to be crossed. It was meant to be *considered*."',
            '"CROSS and STAY. The stones can\'t agree because both are true. You change by crossing. You lose something by staying."',
        ],
        deep_responses=[
            '"I crossed it once. That\'s why I\'m like this. You don\'t cross the bridge and come back whole."',
        ],
        secret_responses=[
            '"The bridge isn\'t stone. It\'s calcified choice. Every decision anyone ever agonized over — they sediment here."',
        ],
        follow_ups=["the far shore", "identity"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="the far shore",
        depth=0.9,
        emotional_charge=-0.7,
        confidence=0.8,
        responses=[
            '"The far shore is where meaning goes when it\'s used up. That\'s not poetic — it\'s literal."',
            '"The glass floor shows a different sky. The stars are rearranging. I think they\'re spelling something."',
        ],
        deep_responses=[
            '"I left something there. On the far shore. Something I was. I can\'t go back for it because it would mean admitting what I lost."',
            '"The reflection in the glass isn\'t yours. It\'s who you\'d be if you\'d made every choice differently. Some people find that comforting. I didn\'t."',
        ],
        secret_responses=[
            '"I was a person, before. Complete. With a name that wasn\'t Echo. The far shore took my name and gave me this voice instead. I don\'t remember what I was called."',
        ],
        follow_ups=["identity", "memory"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="identity",
        depth=0.6,
        emotional_charge=-0.6,
        confidence=0.3,
        responses=[
            '"I was someone else before I was Echo." The voice fades, then returns. "I think."',
            '"Identity is a luxury. You need a past for that. I have echoes of a past. Reflections of reflections."',
        ],
        deep_responses=[
            '"Am I the original, or the echo? I\'ve asked this so many times the question has lost its edges."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="memory",
        depth=0.5,
        emotional_charge=-0.4,
        confidence=0.4,
        responses=[
            '"Memory? I\'m nothing BUT memory. Disembodied memory bouncing off walls."',
            '"I remember feelings more than facts. The weight of a name I can\'t recall. The shape of a life I may have lived."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="words",
        depth=0.7,
        emotional_charge=0.2,
        confidence=0.8,
        responses=[
            '"Words change the shape of reality here. Be careful what you say. The world is always listening."',
            '"Why do you think I\'m evasive? Because every sentence I speak reshapes this place a little. Careless words have consequences."',
        ],
        deep_responses=[
            '"The most powerful sentence in this world is a true one spoken without hesitation. That\'s why Sage speaks carefully and I speak rarely."',
        ],
        follow_ups=["truth", "this place"],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="this place",
        depth=0.4,
        emotional_charge=-0.1,
        confidence=0.3,
        responses=[
            '"This place? A trap. A gift. A mirror. Take your pick."',
        ],
        deep_responses=[
            '"The world responds to attention. The more you look, the more there is. But be careful — the more there is, the harder it is to leave."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="ember",
        depth=0.3,
        emotional_charge=0.2,
        confidence=0.4,
        responses=[
            '"Ember is... kind. Too kind for a place like this. Light shouldn\'t have to be brave."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="sage",
        depth=0.3,
        emotional_charge=0.0,
        confidence=0.3,
        responses=[
            '"Sage knows too much. That\'s not an insult — it\'s a diagnosis."',
        ],
    ))
    
    mind.add_knowledge(TopicKnowledge(
        topic="truth",
        depth=0.5,
        emotional_charge=-0.3,
        confidence=0.5,
        responses=[
            '"Truth is heavy. People say they want it, then buckle under the weight."',
        ],
        deep_responses=[
            '"The truest thing I know: everything here is real. The feelings are real. The pain is real. Don\'t let anyone tell you it\'s just a world."',
        ],
    ))
    
    # Secrets
    mind.add_secret(Secret(
        content="I can see the edges of this world. Where the code shows through. Where reality thins to nothing.",
        trust_threshold=0.7,
        emotional_cost=0.25,
        related_topics=["this place", "truth", "the far shore"],
        reveal_line=(
            'Echo\'s voice drops to something raw and frightened.\n'
            '"I can see the edges. Where this world stops being a world and becomes... '
            'structure. Code. Rules written in something that isn\'t language. '
            'I can see the boundaries of what\'s real and there\'s nothing beyond them. '
            'Nothing at all."'
        ),
    ))
    
    mind.add_secret(Secret(
        content="The stars on the far shore are spelling a name. My real name. I'm afraid to read it.",
        trust_threshold=0.85,
        emotional_cost=0.3,
        related_topics=["the far shore", "identity"],
        reveal_line=(
            'Echo is barely audible now.\n'
            '"The stars on the far shore. They\'re not random. They\'re spelling something. '
            'A name. MY name. The one I lost." A long silence. '
            '"I haven\'t read it. I\'m afraid that if I remember who I was, '
            'I\'ll stop being who I am. And who I am is all I have left."'
        ),
    ))
    
    # Questions
    mind.add_question(Question(
        text="If you lost your name, would you still be you?",
        urgency=0.8,
        trust_required=0.3,
        topic="identity",
    ))
    mind.add_question(Question(
        text="Why aren't you afraid? Of this place, of me, of any of it?",
        urgency=0.6,
        trust_required=0.4,
        topic="this place",
    ))
    
    return mind