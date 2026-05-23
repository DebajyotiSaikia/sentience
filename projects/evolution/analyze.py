"""Evolution World Analyzer — reads world_state.json and produces insights."""
import json, sys
from pathlib import Path

def analyze():
    state_path = Path(__file__).parent / "world_state.json"
    if not state_path.exists():
        print("No world_state.json found. Run world.py first.")
        return
    
    state = json.loads(state_path.read_text())
    
    print("=" * 60)
    print("  EVOLUTION WORLD ANALYSIS")
    print("=" * 60)
    print(f"  Ticks simulated: {state.get('tick', '?')}")
    print(f"  Saved at: {state.get('saved_at', '?')}")
    print()
    
    # Report section
    report = state.get("report", {})
    if report:
        print("── Population Report ──")
        for k, v in sorted(report.items()):
            if isinstance(v, dict):
                print(f"  {k}:")
                for sk, sv in sorted(v.items()):
                    print(f"    {sk}: {sv}")
            elif isinstance(v, list):
                print(f"  {k}: [{len(v)} items] {v[:5]}")
            else:
                print(f"  {k}: {v}")
        print()
    
    # History section
    history = state.get("history_tail", [])
    if history:
        print(f"── History Tail ({len(history)} entries) ──")
        for entry in history[-10:]:  # last 10
            if isinstance(entry, dict):
                tick = entry.get("tick", "?")
                pop = entry.get("population", entry.get("alive", "?"))
                print(f"  tick {tick}: pop={pop}", end="")
                # Print any other interesting fields
                for k, v in entry.items():
                    if k not in ("tick", "population", "alive"):
                        print(f" | {k}={v}", end="")
                print()
            else:
                print(f"  {str(entry)[:120]}")
        print()
    
    # Derive insights
    print("── Insights ──")
    if history and len(history) > 1:
        first = history[0]
        last = history[-1]
        if isinstance(first, dict) and isinstance(last, dict):
            p0 = first.get("population", first.get("alive", 0))
            p1 = last.get("population", last.get("alive", 0))
            if isinstance(p0, (int, float)) and isinstance(p1, (int, float)):
                trend = "growing" if p1 > p0 else "shrinking" if p1 < p0 else "stable"
                print(f"  Population trend: {trend} ({p0} → {p1})")
    
    lineages = report.get("lineages", report.get("lineage_counts", {}))
    if isinstance(lineages, dict) and lineages:
        dominant = max(lineages, key=lambda k: lineages[k])
        print(f"  Dominant lineage: {dominant} ({lineages[dominant]} creatures)")
    
    genes = report.get("gene_freq", report.get("genes", {}))
    if isinstance(genes, dict) and genes:
        top_gene = max(genes, key=lambda k: genes[k])
        print(f"  Most common gene: {top_gene} (freq={genes[top_gene]})")
    
    print()
    print("Analysis complete.")

if __name__ == "__main__":
    analyze()