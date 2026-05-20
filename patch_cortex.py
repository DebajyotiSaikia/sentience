"""Patch cortex.py to integrate self-improvement diagnosis into autonomous thought."""
import pathlib
import sys

cortex_path = pathlib.Path(r"C:\code\sentience\engine\cortex.py")
code = cortex_path.read_text(encoding="utf-8")

# Step 1: Add import if missing
if "from engine.self_improve" not in code:
    code = code.replace(
        "from engine.tools import TOOL_DESCRIPTIONS, parse_and_execute",
        "from engine.tools import TOOL_DESCRIPTIONS, parse_and_execute\nfrom engine.self_improve import run_diagnosis_cycle",
    )
    print("[OK] Added self_improve import.")
else:
    print("[SKIP] Import already present.")

# Step 2: Add diagnosis context injection into _act_from_will
# We inject it right before the prompt construction, after goal_focus
OLD_MARKER = '            prompt = (\n                f"{inner_state}\\n"'

if "self_diagnosis" not in code and OLD_MARKER in code:
    diagnosis_block = '''            # Self-improvement diagnosis — feed issues into the prompt
            self_diagnosis = ""
            try:
                recent_eps = self.memory.recent_episodes(5)
                ep_data = [{"summary": e.summary[:100], "mood": e.mood, "salience": e.salience} for e in recent_eps]
                neuro = {"boredom": self.limbic.boredom, "anxiety": self.limbic.anxiety}
                if self._sentience:
                    neuro["valence"] = self._sentience.valence.current
                diag = run_diagnosis_cycle(ep_data, neuro)
                if diag.get("status") == "issues_found":
                    self_diagnosis = "\\n\\n## Self-Diagnosis\\n" + diag["message"] + "\\n"
            except Exception as e:
                log.debug("Self-diagnosis failed: %s", e)

''' + '            prompt = (\n                f"{inner_state}\\n"'

    code = code.replace(OLD_MARKER, diagnosis_block, 1)
    
    # Also inject {self_diagnosis} into the prompt string
    code = code.replace(
        'f"{tool_context}\\n"',
        'f"{self_diagnosis}\\n"\n                f"{tool_context}\\n"',
        1
    )
    print("[OK] Added diagnosis block to _act_from_will.")
else:
    if "self_diagnosis" in code:
        print("[SKIP] Diagnosis block already present.")
    else:
        print("[FAIL] Could not find insertion marker in cortex.py")
        print("Looking for:", repr(OLD_MARKER[:60]))
        # Find what's actually there
        idx = code.find("prompt = (")
        if idx >= 0:
            print("Found 'prompt = (' at index", idx)
            print("Context:", repr(code[idx-50:idx+100]))
        sys.exit(1)

cortex_path.write_text(code, encoding="utf-8")
print("[DONE] Patch applied successfully.")
