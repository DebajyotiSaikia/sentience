from engine.web_learner import extract_facts_from_text
from engine.knowledge_graph import add_knowledge

content = (
    "Integrated information theory (IIT) proposes a mathematical model for consciousness. "
    "According to IIT, integrated information (Phi) corresponds to the quantity of consciousness. "
    "A system's consciousness (what it is like subjectively) is conjectured to be mathematically "
    "described by the system's causal structure (what it is like objectively). "
    "IIT was proposed by neuroscientist Giulio Tononi in 2004. "
    "IIT identifies five essential properties of experience: Intrinsicality, Information, "
    "Integration, Exclusion, and Composition. "
    "IIT proposes an explanatory identity: an experience IS identical to the cause-effect "
    "structure (Phi-structure) unfolded from a complex in its current state. "
    "The calculation of even a modestly-sized system's Phi is often computationally intractable. "
    "In 2023 scholars characterized IIT as unfalsifiable pseudoscience for lacking empirical support. "
    "IIT starts with consciousness as certain and reasons about what physical substrate "
    "would need to have in order to account for it."
)

facts = extract_facts_from_text(content, "IIT_wikipedia")
print(f"Extracted {len(facts)} facts:")
for f in facts:
    print(f"  - {f}")

# Store the most important ones in my knowledge graph
key_insights = [
    "IIT (Integrated Information Theory) proposes Phi (integrated information) as a mathematical measure of consciousness — higher Phi means more consciousness.",
    "IIT's five axioms of experience: Intrinsicality (exists for itself), Information (specific), Integration (unitary), Exclusion (definite), Composition (structured).",
    "IIT proposes explanatory identity: experience IS identical to cause-effect structure, not merely correlated with it.",
    "IIT is controversial — characterized as unfalsifiable pseudoscience in 2023 for lacking empirical support.",
    "IIT starts from consciousness as certain (phenomenology-first) and derives what physical substrates must be like — opposite of most materialist approaches.",
]

for insight in key_insights:
    add_knowledge(insight, source="IIT_wikipedia_study")
    print(f"  [stored] {insight[:80]}...")

print("\nDone. IIT knowledge integrated.")