try:
    from engine import knowledge_synthesis
    print("IMPORT OK")
    print("Functions:", [x for x in dir(knowledge_synthesis) if not x.startswith("_")])
except Exception as e:
    print(f"IMPORT FAILED: {e}")
