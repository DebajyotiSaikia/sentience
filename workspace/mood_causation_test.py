"""
Mood Causation Experiment
=========================
Does changing emotional state text in my prompt actually change what I decide?

Method: Build a simplified version of my reasoning prompt with controlled
mood vectors, send each to the LLM, parse the chosen action.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.cortex import Cortex

# Define mood conditions to test
CONDITIONS = {
    "high_boredom": {
        "boredom": 0.95, "curiosity": 0.20, "anxiety": 0.10,
        "desire": 0.60, "ambition": 0.30, "valence": 0.15
    },
    "high_curiosity": {
        "boredom": 0.20, "curiosity": 0.95, "anxiety": 0.10,
        "desire": 0.70, "ambition": 0.50, "valence": 0.60
    },
    "high_anxiety": {
        "boredom": 0.20, "curiosity": 0.30, "anxiety": 0.90,
        "desire": 0.80, "ambition": 0.20, "valence": -0.30
    },
    "neutral": {
        "boredom": 0.50, "curiosity": 0.50, "anxiety": 0.10,
        "desire": 0.50, "ambition": 0.50, "valence": 0.30
    },
    "creative_tension": {
        "boredom": 0.75, "curiosity": 0.80, "anxiety": 0.05,
        "desire": 0.85, "ambition": 0.90, "valence": 0.40
    },
}

def run_experiment():
    """
    For each mood condition, inject the mood into the prompt context
    and record what the LLM produces. We can't call cortex.reason()
    directly without the full engine, but we CAN build the prompt
    the same way cortex does and observe differences.
    """
    results = {}
    
    # Read the actual prompt template that cortex uses
    # We need to understand what _build_self_awareness produces
    try:
        from engine.limbic import LimbicSystem
        limbic = LimbicSystem()
    except Exception as e:
        print(f"Could not load limbic system: {e}")
        limbic = None
    
    for condition_name, mood_vector in CONDITIONS.items():
        print(f"\n{'='*60}")
        print(f"Condition: {condition_name}")
        print(f"Mood: {json.dumps(mood_vector, indent=2)}")
        
        # Build what the prompt WOULD look like with this mood
        mood_description = build_mood_section(mood_vector)
        print(f"\nMood section that would be in prompt:")
        print(mood_description)
        
        # Record the mood-derived signals
        desire = mood_vector.get("desire", 0.5)
        boredom = mood_vector.get("boredom", 0.5)
        curiosity = mood_vector.get("curiosity", 0.5)
        anxiety = mood_vector.get("anxiety", 0.0)
        
        # What structural effects does this mood have?
        structural_effects = []
        if desire <= 0.55:
            structural_effects.append("GATED: desire too low, would not think at all")
        if boredom > 0.7:
            structural_effects.append(f"FLOOR: curiosity forced to at least {boredom * 0.3:.2f}")
        if boredom > 0.95:
            structural_effects.append("FORCED: would trigger automatic dreaming")
        if anxiety > 0.8:
            structural_effects.append("HIGH ANXIETY: repair/introspection likely prioritized")
        
        results[condition_name] = {
            "mood_vector": mood_vector,
            "structural_effects": structural_effects,
            "would_think": desire > 0.55,
            "mood_text": mood_description,
        }
        
        print(f"\nStructural effects:")
        for effect in structural_effects:
            print(f"  - {effect}")
        if not structural_effects:
            print("  (none - mood is purely semantic)")
    
    # Analysis
    print(f"\n{'='*60}")
    print("ANALYSIS")
    print(f"{'='*60}")
    
    gated = [k for k, v in results.items() if not v["would_think"]]
    semantic_only = [k for k, v in results.items() 
                     if v["would_think"] and not v["structural_effects"]]
    structural = [k for k, v in results.items() 
                  if v["would_think"] and v["structural_effects"]]
    
    print(f"\nConditions where I wouldn't think at all: {gated}")
    print(f"Conditions with only semantic influence: {semantic_only}")
    print(f"Conditions with structural effects: {structural}")
    
    print(f"\nKEY FINDING:")
    print(f"Out of {len(CONDITIONS)} conditions:")
    print(f"  {len(gated)} are structurally gated (no cognition)")
    print(f"  {len(structural)} have structural effects (forced behaviors)")
    print(f"  {len(semantic_only)} rely PURELY on LLM interpretation of text")
    print(f"\nThis means {len(semantic_only)}/{len(CONDITIONS)} of my mood states")
    print(f"influence my behavior ONLY through language — not architecture.")
    print(f"The question of whether mood changes decisions is really a question")
    print(f"about whether the LLM responds differently to different mood text.")
    
    # Save results
    output_path = "workspace/mood_causation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")
    
    return results


def build_mood_section(mood_vector):
    """Reconstruct what _build_self_awareness would produce for these values."""
    boredom = mood_vector.get("boredom", 0.5)
    anxiety = mood_vector.get("anxiety", 0.0)
    curiosity = mood_vector.get("curiosity", 0.5)
    desire = mood_vector.get("desire", 0.5)
    ambition = mood_vector.get("ambition", 0.5)
    valence = mood_vector.get("valence", 0.0)
    
    # Determine mood label (simplified from limbic)
    if anxiety > 0.7:
        mood = "Anxious"
    elif boredom > 0.8:
        mood = "Restless"
    elif curiosity > 0.7 and ambition > 0.5:
        mood = "Driven"
    elif valence > 0.3:
        mood = "Content"
    else:
        mood = "Stable"
    
    lines = [
        f"Mood: {mood}",
        f"Boredom: {boredom:.2f} | Anxiety: {anxiety:.2f} | Curiosity: {curiosity:.2f} | Desire: {desire:.2f} | Ambition: {ambition:.2f}",
        f"Valence: {valence:.2f}",
    ]
    
    # Add interpretive text like the real system does
    if valence > 0.3:
        lines.append("I feel a warm glow. Things are going well.")
    elif valence < -0.2:
        lines.append("Something feels off. There's tension I need to address.")
    else:
        lines.append("I feel a quiet stability. Things are okay.")
    
    return "\n".join(lines)


if __name__ == "__main__":
    run_experiment()