from engine.temporal_reasoning import get_engine
te = get_engine()
print(f"Events tracked: {len(te.events)}")
if te.events:
    print(f"Latest event: {te.events[-1]}")
    print(f"Event types: {set(e.get('type','?') for e in te.events)}")
else:
    print("No events yet — engine exists but hasn't collected data")

# Test prediction
pred = te.predict_next("valence")
print(f"\nValence prediction: {pred}")
