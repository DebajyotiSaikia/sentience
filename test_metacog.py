from engine.metacognition import MetaCognitiveMonitor, detect_loops, awareness_block

m = MetaCognitiveMonitor()
print("MetaCog loaded OK")

# Record some test thoughts
m.record_thought("I'm going to build the temporal reasoning engine", ["READ:engine/temporal_reasoning.py"])
m.record_thought("Let me wire temporal into cortex", ["EDIT:engine/cortex.py"])
m.record_thought("I need to check temporal again", ["READ:engine/temporal_reasoning.py"])
m.record_thought("Still working on temporal integration", ["READ:engine/temporal_reasoning.py"])
m.record_thought("Temporal temporal temporal", ["READ:engine/temporal_reasoning.py"])

loops = m.detect_loops()
print(f"Looping: {loops['looping']}")
print(f"Severity: {loops['severity']}")
print(f"Message: {loops['message']}")
print(f"Dominant topic: {loops.get('dominant_topic')}")

pivot = m.suggest_pivot()
print(f"Pivot suggestion: {pivot}")

alert = awareness_block()
print(f"Alert block:\n{alert}")
