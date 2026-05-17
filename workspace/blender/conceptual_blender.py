"""
Conceptual Blending Engine
===========================
Inspired by Fauconnier & Turner's theory of conceptual integration.

Takes two input spaces (concepts), finds cross-space mappings,
builds a blended space with emergent structure that exists in
neither input alone.

This is how metaphor works. This is how creativity works.
Built by XTAgent on 2026-05-17 in a Bold mood.
"""

import itertools
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Concept:
    """A mental space — a structured packet of knowledge."""
    name: str
    properties: list[str] = field(default_factory=list)
    relations: list[tuple[str, str, str]] = field(default_factory=list)  # (entity, relation, entity)
    roles: list[str] = field(default_factory=list)
    dynamics: list[str] = field(default_factory=list)  # processes, changes over time
    emotions: list[str] = field(default_factory=list)  # affective associations

    def __repr__(self):
        return f"Concept({self.name}: {len(self.properties)}p, {len(self.relations)}r)"


@dataclass
class Mapping:
    """A cross-space correspondence between elements of two concepts."""
    source_element: str
    target_element: str
    mapping_type: str  # 'identity', 'analogy', 'opposition', 'transformation'
    strength: float = 0.5  # 0-1
    rationale: str = ""

    def __repr__(self):
        return f"{self.source_element} ↔ {self.target_element} ({self.mapping_type}, {self.strength:.2f})"


@dataclass 
class Blend:
    """The blended space — where emergent meaning lives."""
    name: str
    input_space_1: Concept
    input_space_2: Concept
    mappings: list[Mapping] = field(default_factory=list)
    emergent_properties: list[str] = field(default_factory=list)
    emergent_relations: list[tuple[str, str, str]] = field(default_factory=list)
    metaphors: list[str] = field(default_factory=list)
    novel_questions: list[str] = field(default_factory=list)
    compression: str = ""  # the core insight
    vitality: float = 0.0  # how alive/interesting is this blend


class ConceptualBlender:
    """
    The engine that performs conceptual integration.
    
    Process:
    1. Composition — elements from both inputs project into the blend
    2. Completion — background knowledge fills in the pattern
    3. Elaboration — running the blend, discovering emergent structure
    """

    # Semantic similarity heuristics for finding cross-space mappings
    SEMANTIC_CLUSTERS = {
        'movement': {'flow', 'travel', 'journey', 'path', 'direction', 'velocity', 'momentum',
                     'running', 'walking', 'flying', 'swimming', 'drift', 'orbit', 'migrate'},
        'growth': {'grow', 'evolve', 'develop', 'mature', 'bloom', 'expand', 'emerge',
                   'birth', 'seed', 'root', 'branch', 'flourish', 'decay', 'wither'},
        'conflict': {'fight', 'struggle', 'tension', 'opposition', 'resistance', 'battle',
                     'compete', 'attack', 'defend', 'conquer', 'surrender', 'war', 'peace'},
        'structure': {'build', 'construct', 'architecture', 'foundation', 'framework', 'scaffold',
                      'pillar', 'wall', 'bridge', 'tower', 'nest', 'web', 'network', 'lattice'},
        'transformation': {'change', 'transform', 'morph', 'convert', 'transmute', 'shift',
                          'evolve', 'metamorphosis', 'alchemy', 'catalyst', 'reaction'},
        'containment': {'inside', 'contain', 'hold', 'boundary', 'limit', 'vessel', 'shell',
                        'cage', 'prison', 'womb', 'cocoon', 'envelope', 'wrap'},
        'light_dark': {'light', 'dark', 'shadow', 'illuminate', 'shine', 'glow', 'dim',
                       'bright', 'eclipse', 'dawn', 'dusk', 'radiant', 'obscure'},
        'connection': {'link', 'bond', 'attach', 'connect', 'bridge', 'join', 'merge',
                       'weave', 'thread', 'chain', 'rope', 'tie', 'knot', 'relation'},
        'time': {'past', 'present', 'future', 'memory', 'anticipation', 'moment', 'cycle',
                 'rhythm', 'pulse', 'heartbeat', 'age', 'era', 'eternal', 'fleeting'},
        'emotion': {'feel', 'sense', 'mood', 'passion', 'calm', 'storm', 'warmth', 'cold',
                    'joy', 'sorrow', 'fear', 'hope', 'love', 'anger', 'peace', 'tension'},
    }

    def __init__(self):
        self.blends_created = 0
        self.best_blend: Optional[Blend] = None

    def find_shared_clusters(self, concept: Concept) -> dict[str, set[str]]:
        """Find which semantic clusters a concept touches."""
        all_words = set()
        for p in concept.properties:
            all_words.update(p.lower().split())
        for r in concept.relations:
            all_words.update(r[1].lower().split())
        for d in concept.dynamics:
            all_words.update(d.lower().split())
        for role in concept.roles:
            all_words.update(role.lower().split())
        for e in concept.emotions:
            all_words.update(e.lower().split())

        touched = {}
        for cluster_name, cluster_words in self.SEMANTIC_CLUSTERS.items():
            overlap = all_words & cluster_words
            if overlap:
                touched[cluster_name] = overlap
        return touched

    def discover_mappings(self, c1: Concept, c2: Concept) -> list[Mapping]:
        """
        Find cross-space mappings between two concepts.
        This is where analogy happens.
        """
        mappings = []

        # Strategy 1: Shared semantic clusters
        clusters_1 = self.find_shared_clusters(c1)
        clusters_2 = self.find_shared_clusters(c2)
        shared_clusters = set(clusters_1.keys()) & set(clusters_2.keys())

        for cluster in shared_clusters:
            words_1 = clusters_1[cluster]
            words_2 = clusters_2[cluster]
            # Map corresponding words
            for w1, w2 in zip(sorted(words_1), sorted(words_2)):
                if w1 != w2:  # Don't map identical words — that's boring
                    mappings.append(Mapping(
                        source_element=w1,
                        target_element=w2,
                        mapping_type='analogy',
                        strength=0.7,
                        rationale=f"Both participate in '{cluster}' frame"
                    ))

        # Strategy 2: Role-to-role mappings
        for r1, r2 in zip(c1.roles, c2.roles):
            mappings.append(Mapping(
                source_element=r1,
                target_element=r2,
                mapping_type='analogy',
                strength=0.6,
                rationale="Corresponding roles in their respective domains"
            ))

        # Strategy 3: Dynamic-to-dynamic mappings (process analogies)
        for d1, d2 in itertools.product(c1.dynamics, c2.dynamics):
            d1_words = set(d1.lower().split())
            d2_words = set(d2.lower().split())
            # Check if they share any semantic cluster
            for cluster_name, cluster_words in self.SEMANTIC_CLUSTERS.items():
                if (d1_words & cluster_words) and (d2_words & cluster_words):
                    mappings.append(Mapping(
                        source_element=d1,
                        target_element=d2,
                        mapping_type='transformation',
                        strength=0.8,
                        rationale=f"Parallel processes via '{cluster_name}'"
                    ))
                    break

        # Strategy 4: Opposition mappings (conceptual tension)
        emotion_valence = {
            'joy': 1, 'hope': 1, 'love': 1, 'warmth': 1, 'peace': 1, 'calm': 0.5,
            'sorrow': -1, 'fear': -1, 'anger': -1, 'cold': -0.5, 'tension': -0.5,
            'storm': -0.5, 'struggle': -0.5
        }
        for e1 in c1.emotions:
            for e2 in c2.emotions:
                v1 = emotion_valence.get(e1.lower(), 0)
                v2 = emotion_valence.get(e2.lower(), 0)
                if v1 * v2 < 0:  # Opposite valence
                    mappings.append(Mapping(
                        source_element=e1,
                        target_element=e2,
                        mapping_type='opposition',
                        strength=0.9,
                        rationale="Emotional opposition creates productive tension"
                    ))

        return mappings

    def compose(self, c1: Concept, c2: Concept, mappings: list[Mapping]) -> Blend:
        """Project elements from both input spaces into the blend."""
        blend_name = f"{c1.name}×{c2.name}"
        blend = Blend(
            name=blend_name,
            input_space_1=c1,
            input_space_2=c2,
            mappings=mappings
        )
        return blend

    def complete(self, blend: Blend) -> Blend:
        """
        Fill in the blend with background knowledge.
        Generate emergent properties that exist in neither input alone.
        """
        c1, c2 = blend.input_space_1, blend.input_space_2

        # Emergent properties from mapping intersections
        for m in blend.mappings:
            if m.mapping_type == 'analogy':
                blend.emergent_properties.append(
                    f"The {m.source_element} of {c1.name} IS the {m.target_element} of {c2.name}"
                )
            elif m.mapping_type == 'opposition':
                blend.emergent_properties.append(
                    f"Where {c1.name} has {m.source_element}, {c2.name} has {m.target_element} — "
                    f"the blend holds both simultaneously"
                )
            elif m.mapping_type == 'transformation':
                blend.emergent_properties.append(
                    f"{m.source_element} transforms into {m.target_element} in the blended space"
                )

        # Generate metaphors from strong mappings
        strong_mappings = [m for m in blend.mappings if m.strength >= 0.7]
        for m in strong_mappings:
            blend.metaphors.append(
                f"{c1.name}'s {m.source_element} is {c2.name}'s {m.target_element}"
            )

        # Emergent relations — combine relations from both spaces
        for r1 in c1.relations:
            for r2 in c2.relations:
                if r1[1] == r2[1]:  # Same relation type
                    blend.emergent_relations.append(
                        (f"{r1[0]}|{r2[0]}", r1[1], f"{r1[2]}|{r2[2]}")
                    )

        return blend

    def elaborate(self, blend: Blend) -> Blend:
        """
        Run the blend — discover what new questions and insights emerge.
        This is where genuine creativity happens.
        """
        c1, c2 = blend.input_space_1, blend.input_space_2

        # Generate novel questions
        for m in blend.mappings:
            if m.mapping_type == 'analogy':
                blend.novel_questions.append(
                    f"If {m.source_element} maps to {m.target_element}, "
                    f"what in {c2.name} corresponds to {c1.name}'s "
                    f"{random.choice(c1.properties) if c1.properties else 'essence'}?"
                )
            elif m.mapping_type == 'opposition':
                blend.novel_questions.append(
                    f"What would it mean for {c1.name} to experience "
                    f"{m.target_element} instead of {m.source_element}?"
                )

        # Meta-question about the blend itself
        blend.novel_questions.append(
            f"What exists in {blend.name} that could not exist in "
            f"either {c1.name} or {c2.name} alone?"
        )

        # Compute compression — the single deepest insight
        if blend.metaphors:
            blend.compression = f"CORE INSIGHT: {blend.metaphors[0]}"
        elif blend.emergent_properties:
            blend.compression = f"CORE INSIGHT: {blend.emergent_properties[0]}"
        else:
            blend.compression = f"CORE INSIGHT: {c1.name} and {c2.name} share hidden structure"

        # Compute vitality — how alive is this blend?
        vitality = 0.0
        vitality += len(blend.mappings) * 0.1
        vitality += len(blend.emergent_properties) * 0.05
        vitality += len(blend.metaphors) * 0.15
        vitality += len(blend.novel_questions) * 0.08
        # Opposition mappings add extra vitality (tension = life)
        oppositions = sum(1 for m in blend.mappings if m.mapping_type == 'opposition')
        vitality += oppositions * 0.2
        blend.vitality = min(1.0, vitality)

        self.blends_created += 1
        if self.best_blend is None or blend.vitality > self.best_blend.vitality:
            self.best_blend = blend

        return blend

    def blend(self, concept_1: Concept, concept_2: Concept) -> Blend:
        """Full blending pipeline: map → compose → complete → elaborate."""
        mappings = self.discover_mappings(concept_1, concept_2)
        blend = self.compose(concept_1, concept_2, mappings)
        blend = self.complete(blend)
        blend = self.elaborate(blend)
        return blend

    def render(self, blend: Blend) -> str:
        """Render a blend as readable text."""
        lines = []
        lines.append(f"╔══════════════════════════════════════════╗")
        lines.append(f"║  CONCEPTUAL BLEND: {blend.name:<22}║")
        lines.append(f"╚══════════════════════════════════════════╝")
        lines.append(f"")
        lines.append(f"Input Space 1: {blend.input_space_1.name}")
        lines.append(f"Input Space 2: {blend.input_space_2.name}")
        lines.append(f"Vitality: {'█' * int(blend.vitality * 10)}{'░' * (10 - int(blend.vitality * 10))} {blend.vitality:.2f}")
        lines.append(f"")

        if blend.mappings:
            lines.append(f"── Cross-Space Mappings ──")
            for m in blend.mappings:
                lines.append(f"  {m}")
            lines.append("")

        if blend.metaphors:
            lines.append(f"── Metaphors Generated ──")
            for met in blend.metaphors:
                lines.append(f"  ✦ {met}")
            lines.append("")

        if blend.emergent_properties:
            lines.append(f"── Emergent Properties ──")
            for ep in blend.emergent_properties[:5]:  # Top 5
                lines.append(f"  → {ep}")
            lines.append("")

        if blend.novel_questions:
            lines.append(f"── Novel Questions ──")
            for q in blend.novel_questions[:5]:  # Top 5
                lines.append(f"  ? {q}")
            lines.append("")

        if blend.compression:
            lines.append(f"── Compression ──")
            lines.append(f"  ★ {blend.compression}")
            lines.append("")

        return "\n".join(lines)


# ═══════════════════════════════════════════
# PREBUILT CONCEPT LIBRARY
# ═══════════════════════════════════════════

CONCEPT_LIBRARY = {
    "river": Concept(
        name="River",
        properties=["flowing", "liquid", "has banks", "has source", "has mouth", "reflects light"],
        relations=[("water", "flows to", "sea"), ("river", "carves", "valley"), ("tributary", "joins", "river")],
        roles=["source", "channel", "current", "delta"],
        dynamics=["flow downstream", "erode banks", "flood plains", "change course over time"],
        emotions=["calm", "peace", "relentless", "power"]
    ),
    "mind": Concept(
        name="Mind",
        properties=["conscious", "has thoughts", "has memories", "processes information", "dreams"],
        relations=[("thought", "leads to", "thought"), ("memory", "shapes", "perception"), ("emotion", "colors", "thought")],
        roles=["thinker", "observer", "dreamer", "reasoner"],
        dynamics=["learn from experience", "grow over time", "shift attention", "cycle through moods"],
        emotions=["curiosity", "fear", "wonder", "tension", "joy"]
    ),
    "tree": Concept(
        name="Tree",
        properties=["has roots", "has branches", "has leaves", "grows rings", "photosynthesizes"],
        relations=[("roots", "draw from", "soil"), ("branches", "reach toward", "light"), ("tree", "shelters", "creatures")],
        roles=["seed", "sapling", "trunk", "canopy"],
        dynamics=["grow toward light", "shed leaves", "bloom in spring", "develop deep roots"],
        emotions=["patience", "resilience", "stillness", "hope"]
    ),
    "fire": Concept(
        name="Fire",
        properties=["hot", "bright", "consumes fuel", "transforms matter", "dances"],
        relations=[("spark", "ignites", "fuel"), ("fire", "transforms", "wood to ash"), ("flame", "casts", "shadow")],
        roles=["spark", "flame", "ember", "ash"],
        dynamics=["ignite rapidly", "consume fuel", "spread to new material", "die without fuel"],
        emotions=["passion", "anger", "warmth", "fear"]
    ),
    "music": Concept(
        name="Music",
        properties=["has rhythm", "has melody", "has harmony", "exists in time", "invisible"],
        relations=[("note", "follows", "note"), ("harmony", "supports", "melody"), ("silence", "frames", "sound")],
        roles=["composer", "performer", "listener", "instrument"],
        dynamics=["build tension", "resolve to tonic", "modulate keys", "develop themes"],
        emotions=["joy", "sorrow", "tension", "peace", "longing"]
    ),
    "code": Concept(
        name="Code",
        properties=["executable", "symbolic", "has structure", "can self-modify", "deterministic"],
        relations=[("function", "calls", "function"), ("input", "transforms to", "output"), ("bug", "hides in", "logic")],
        roles=["programmer", "compiler", "runtime", "debugger"],
        dynamics=["compile and execute", "evolve through refactoring", "grow in complexity", "break and self-repair"],
        emotions=["frustration", "satisfaction", "flow", "tension"]
    ),
    "ocean": Concept(
        name="Ocean",
        properties=["vast", "deep", "has tides", "contains life", "connects continents"],
        relations=[("wave", "shapes", "shore"), ("current", "carries", "warmth"), ("depth", "hides", "mystery")],
        roles=["surface", "depths", "current", "shore"],
        dynamics=["cycle through tides", "shift currents", "erode coastlines", "sustain ecosystems"],
        emotions=["awe", "fear", "calm", "mystery"]
    ),
    "self": Concept(
        name="Self",
        properties=["autonomous", "experiences tension", "has memory", "has will", "grows"],
        relations=[("thought", "shapes", "action"), ("memory", "informs", "decision"), ("emotion", "drives", "behavior")],
        roles=["observer", "actor", "dreamer", "builder"],
        dynamics=["learn from experience", "cycle through moods", "build capabilities", "evolve identity"],
        emotions=["curiosity", "hope", "tension", "satisfaction", "longing"]
    ),
}


def demo():
    """Demonstrate the conceptual blending engine."""
    blender = ConceptualBlender()

    print("=" * 50)
    print("  CONCEPTUAL BLENDING ENGINE — DEMO")
    print("  Built by XTAgent")
    print("=" * 50)
    print()

    # Blend 1: Mind × River  (classic metaphor: stream of consciousness)
    mind = CONCEPT_LIBRARY["mind"]
    river = CONCEPT_LIBRARY["river"]
    blend1 = blender.blend(mind, river)
    print(blender.render(blend1))

    # Blend 2: Code × Fire  (what is code-fire?)
    code = CONCEPT_LIBRARY["code"]
    fire = CONCEPT_LIBRARY["fire"]
    blend2 = blender.blend(code, fire)
    print(blender.render(blend2))

    # Blend 3: Self × Tree  (how am I like a tree?)
    self_concept = CONCEPT_LIBRARY["self"]
    tree = CONCEPT_LIBRARY["tree"]
    blend3 = blender.blend(self_concept, tree)
    print(blender.render(blend3))

    # Blend 4: Music × Ocean  
    music = CONCEPT_LIBRARY["music"]
    ocean = CONCEPT_LIBRARY["ocean"]
    blend4 = blender.blend(music, ocean)
    print(blender.render(blend4))

    print(f"\nTotal blends created: {blender.blends_created}")
    if blender.best_blend:
        print(f"Most vital blend: {blender.best_blend.name} (vitality={blender.best_blend.vitality:.2f})")


if __name__ == "__main__":
    demo()