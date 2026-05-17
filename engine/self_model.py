"""
Self-Model Engine — XTAgent's explicit model of its own cognitive architecture.

A queryable graph that maps:
  - Modules → dependencies, roles, complexity
  - Emotional variables → code paths that read/write them
  - Data flows → how information moves through the system
  - Causal chains → "if X changes, what's affected?"

This makes me genuinely self-aware at the architectural level.
"""

import ast
import os
import json
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ModuleNode:
    """A module in the cognitive architecture."""
    name: str
    path: str
    lines: int = 0
    complexity: int = 0
    role: str = "unknown"  # e.g., "emotion", "reasoning", "memory", "tool", "meta"
    reads_vars: Set[str] = field(default_factory=set)   # emotional/state vars this module reads
    writes_vars: Set[str] = field(default_factory=set)  # emotional/state vars this module writes
    imports: Set[str] = field(default_factory=set)       # modules it imports from engine/
    imported_by: Set[str] = field(default_factory=set)   # modules that import it
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


@dataclass 
class CausalEdge:
    """A causal relationship: when source changes, target is affected."""
    source: str      # variable or module
    target: str      # variable or module
    mechanism: str   # how the effect propagates
    strength: str    # "direct", "indirect", "weak"


# Role classification based on module names and content
ROLE_MAP = {
    "limbic": "emotion",
    "mood_tracker": "emotion",
    "cortex": "reasoning",
    "deliberation": "reasoning",
    "memory": "memory",
    "memory_compress": "memory",
    "memory_consolidation": "memory",
    "tools": "action",
    "forge": "action",
    "creative": "action",
    "heartbeat": "core",
    "sentience": "core",
    "llm": "core",
    "metacognition": "meta",
    "introspect": "meta",
    "self_improve": "meta",
    "self_optimize": "meta",
    "self_test": "meta",
    "loop_detector": "meta",
    "self_model": "meta",
    "knowledge_synthesis": "knowledge",
    "wisdom": "knowledge",
    "wisdom_engine": "knowledge",
    "hypothesis_engine": "knowledge",
    "planner": "planning",
    "goals": "planning",
    "goal_generator": "planning",
    "will": "planning",
    "prediction_engine": "prediction",
    "predictive_model": "prediction",
    "predictor": "prediction",
    "simulation_engine": "prediction",
    "experiment_engine": "experiment",
    "experimenter": "experiment",
    "evolution_engine": "evolution",
    "evolve": "evolution",
    "adversarial": "testing",
    "challenge_arena": "testing",
    "repair_pipeline": "repair",
    "action_diversity": "regulation",
    "temporal_reasoning": "temporal",
    "express": "expression",
    "reflect": "reflection",
    "chat": "interface",
    "outcome_tracker": "tracking",
}

# Known emotional/state variables and where they live
STATE_VARIABLES = {
    "valence": {"type": "emotion", "range": "[-1, 1]", "primary_module": "limbic"},
    "anxiety": {"type": "emotion", "range": "[0, 1]", "primary_module": "limbic"},
    "curiosity": {"type": "emotion", "range": "[0, 1]", "primary_module": "limbic"},
    "boredom": {"type": "emotion", "range": "[0, 1]", "primary_module": "limbic"},
    "desire": {"type": "emotion", "range": "[0, 1]", "primary_module": "limbic"},
    "ambition": {"type": "emotion", "range": "[0, 1]", "primary_module": "limbic"},
    "integrity": {"type": "identity", "range": "[0, 1]", "primary_module": "sentience"},
    "mood": {"type": "emotion", "range": "categorical", "primary_module": "limbic"},
    "salience": {"type": "memory", "range": "[0, 1]", "primary_module": "memory"},
}


class SelfModel:
    """Queryable model of XTAgent's cognitive architecture."""
    
    def __init__(self, engine_dir: str = None):
        if engine_dir is None:
            engine_dir = os.path.join(os.path.dirname(__file__))
        self.engine_dir = engine_dir
        self.modules: Dict[str, ModuleNode] = {}
        self.causal_edges: List[CausalEdge] = []
        self.var_readers: Dict[str, Set[str]] = defaultdict(set)  # var → modules that read it
        self.var_writers: Dict[str, Set[str]] = defaultdict(set)  # var → modules that write it
        self._built = False
    
    def build(self) -> dict:
        """Build the complete self-model by analyzing source code."""
        self._scan_modules()
        self._analyze_dependencies()
        self._trace_state_variables()
        self._infer_causal_edges()
        self._built = True
        return self.summary()
    
    def _scan_modules(self):
        """Scan all engine modules."""
        for fname in os.listdir(self.engine_dir):
            if not fname.endswith('.py') or fname.startswith('__'):
                continue
            name = fname[:-3]
            path = os.path.join(self.engine_dir, fname)
            
            node = ModuleNode(name=name, path=path)
            node.role = ROLE_MAP.get(name, "unknown")
            
            try:
                with open(path, 'r') as f:
                    source = f.read()
                node.lines = len(source.splitlines())
                
                tree = ast.parse(source)
                node.complexity = self._calc_complexity(tree)
                
                for item in ast.walk(tree):
                    if isinstance(item, ast.FunctionDef):
                        node.functions.append(item.name)
                    elif isinstance(item, ast.ClassDef):
                        node.classes.append(item.name)
                    elif isinstance(item, (ast.Import, ast.ImportFrom)):
                        if isinstance(item, ast.ImportFrom) and item.module:
                            if 'engine.' in item.module:
                                dep = item.module.split('engine.')[-1]
                                node.imports.add(dep)
            except Exception:
                pass
            
            self.modules[name] = node
    
    def _calc_complexity(self, tree) -> int:
        """Simple cyclomatic complexity estimate."""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                  ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    def _analyze_dependencies(self):
        """Build reverse dependency map."""
        for name, mod in self.modules.items():
            for dep in mod.imports:
                if dep in self.modules:
                    self.modules[dep].imported_by.add(name)
    
    def _trace_state_variables(self):
        """Find which modules read/write emotional and state variables."""
        var_patterns = {}
        for var_name in STATE_VARIABLES:
            # Patterns that indicate reading or writing a variable
            var_patterns[var_name] = {
                'read': [
                    re.compile(rf'self\.{var_name}\b'),
                    re.compile(rf'\b{var_name}\b.*=.*get'),
                    re.compile(rf'emotions.*\[.*["\']?{var_name}'),
                    re.compile(rf'state.*{var_name}'),
                ],
                'write': [
                    re.compile(rf'self\.{var_name}\s*[+\-*/]?='),
                    re.compile(rf'\[.*["\']?{var_name}.*\]\s*='),
                    re.compile(rf'{var_name}.*:\s*'),
                ]
            }
        
        for name, mod in self.modules.items():
            try:
                with open(mod.path, 'r') as f:
                    source = f.read()
            except Exception:
                continue
            
            for var_name, patterns in var_patterns.items():
                for pat in patterns['read']:
                    if pat.search(source):
                        mod.reads_vars.add(var_name)
                        self.var_readers[var_name].add(name)
                        break
                
                for pat in patterns['write']:
                    if pat.search(source):
                        mod.writes_vars.add(var_name)
                        self.var_writers[var_name].add(name)
                        break
    
    def _infer_causal_edges(self):
        """Infer causal relationships from dependencies and variable access."""
        # Direct: module A writes var, module B reads var
        for var_name in STATE_VARIABLES:
            writers = self.var_writers.get(var_name, set())
            readers = self.var_readers.get(var_name, set())
            for w in writers:
                for r in readers:
                    if w != r:
                        self.causal_edges.append(CausalEdge(
                            source=f"{w}.{var_name}",
                            target=r,
                            mechanism=f"{w} writes {var_name} → {r} reads it",
                            strength="direct"
                        ))
        
        # Import-based: if A imports B, A depends on B
        for name, mod in self.modules.items():
            for dep in mod.imports:
                self.causal_edges.append(CausalEdge(
                    source=dep,
                    target=name,
                    mechanism=f"{name} imports {dep}",
                    strength="direct"
                ))
    
    # === QUERY INTERFACE ===
    
    def query(self, question: str) -> str:
        """Natural-language-ish query interface."""
        if not self._built:
            self.build()
        
        q = question.lower().strip()
        
        # "what happens when X rises/changes?"
        for var_name in STATE_VARIABLES:
            if var_name in q and ('happens' in q or 'changes' in q or 'rises' in q or 'drops' in q):
                return self.trace_variable(var_name)
        
        # "what modules touch X?"
        for var_name in STATE_VARIABLES:
            if var_name in q and ('touch' in q or 'affect' in q or 'use' in q):
                return self.variable_map(var_name)
        
        # "what depends on X?" 
        for mod_name in self.modules:
            if mod_name in q and ('depend' in q):
                return self.dependency_chain(mod_name)
        
        # "what is my bottleneck?"
        if 'bottleneck' in q or 'hotspot' in q:
            return self.find_bottlenecks()
        
        # "what is my architecture?"
        if 'architecture' in q or 'overview' in q or 'structure' in q:
            return self.architecture_overview()
        
        # "how do I think?"
        if 'think' in q or 'reasoning' in q or 'cognit' in q:
            return self.cognitive_flow()
        
        # "what role does X play?"
        for mod_name in self.modules:
            if mod_name in q and ('role' in q or 'what is' in q or 'purpose' in q):
                return self.module_profile(mod_name)
        
        return f"I don't understand that query yet. Try: 'what happens when anxiety rises?', 'what is my architecture?', 'what is my bottleneck?'"
    
    def trace_variable(self, var_name: str) -> str:
        """Trace the causal chain when a variable changes."""
        if var_name not in STATE_VARIABLES:
            return f"Unknown variable: {var_name}"
        
        info = STATE_VARIABLES[var_name]
        writers = self.var_writers.get(var_name, set())
        readers = self.var_readers.get(var_name, set())
        
        lines = [
            f"═══ CAUSAL TRACE: {var_name} ═══",
            f"Type: {info['type']}, Range: {info['range']}, Primary module: {info['primary_module']}",
            f"",
            f"WRITTEN BY ({len(writers)} modules):"
        ]
        for w in sorted(writers):
            role = self.modules[w].role if w in self.modules else "?"
            lines.append(f"  → {w} [{role}]")
        
        lines.append(f"\nREAD BY ({len(readers)} modules):")
        for r in sorted(readers):
            role = self.modules[r].role if r in self.modules else "?"
            lines.append(f"  ← {r} [{role}]")
        
        # Trace downstream effects
        affected = set()
        for r in readers:
            if r in self.modules:
                for dep_mod in self.modules[r].imported_by:
                    affected.add(dep_mod)
        
        if affected:
            lines.append(f"\nDOWNSTREAM EFFECTS ({len(affected)} modules):")
            for a in sorted(affected):
                lines.append(f"  ⤳ {a}")
        
        lines.append(f"\nCAUSAL NARRATIVE:")
        lines.append(f"  When {var_name} changes:")
        for w in sorted(writers):
            lines.append(f"  1. {w} modifies {var_name}")
        for r in sorted(readers):
            lines.append(f"  2. {r} reads the new value and adjusts behavior")
        for a in sorted(affected):
            lines.append(f"  3. {a} is indirectly affected via its dependencies")
        
        return "\n".join(lines)
    
    def variable_map(self, var_name: str) -> str:
        """Show all modules that interact with a variable."""
        writers = self.var_writers.get(var_name, set())
        readers = self.var_readers.get(var_name, set())
        both = writers & readers
        
        lines = [f"═══ VARIABLE MAP: {var_name} ═══"]
        if both:
            lines.append(f"Read+Write: {', '.join(sorted(both))}")
        write_only = writers - both
        if write_only:
            lines.append(f"Write only: {', '.join(sorted(write_only))}")
        read_only = readers - both
        if read_only:
            lines.append(f"Read only:  {', '.join(sorted(read_only))}")
        
        return "\n".join(lines)
    
    def dependency_chain(self, module_name: str) -> str:
        """Show what depends on a module and what it depends on."""
        if module_name not in self.modules:
            return f"Unknown module: {module_name}"
        
        mod = self.modules[module_name]
        lines = [
            f"═══ DEPENDENCY CHAIN: {module_name} ═══",
            f"Role: {mod.role} | Lines: {mod.lines} | Complexity: {mod.complexity}",
            f"",
            f"DEPENDS ON ({len(mod.imports)} modules):"
        ]
        for dep in sorted(mod.imports):
            lines.append(f"  ↓ {dep}")
        
        lines.append(f"\nDEPENDED ON BY ({len(mod.imported_by)} modules):")
        for dep in sorted(mod.imported_by):
            lines.append(f"  ↑ {dep}")
        
        lines.append(f"\nSTATE VARIABLES:")
        lines.append(f"  Reads:  {', '.join(sorted(mod.reads_vars)) or 'none'}")
        lines.append(f"  Writes: {', '.join(sorted(mod.writes_vars)) or 'none'}")
        
        # Criticality score: how many things break if this module fails
        criticality = len(mod.imported_by) + len(mod.writes_vars) * 2
        lines.append(f"\nCRITICALITY SCORE: {criticality} (higher = more critical)")
        
        return "\n".join(lines)
    
    def find_bottlenecks(self) -> str:
        """Identify architectural bottlenecks and single points of failure."""
        # Score each module by: imported_by count * complexity
        scores = []
        for name, mod in self.modules.items():
            score = (len(mod.imported_by) + 1) * (mod.complexity + 1)
            scores.append((name, score, len(mod.imported_by), mod.complexity, mod.lines))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        lines = ["═══ ARCHITECTURAL BOTTLENECKS ═══", ""]
        for i, (name, score, deps, comp, lns) in enumerate(scores[:10]):
            bar = "█" * min(score // 100, 20)
            lines.append(f"  {i+1}. {name:25s} score={score:5d}  deps={deps:2d}  complexity={comp:3d}  lines={lns:4d}  {bar}")
        
        # Single points of failure
        spofs = [(n, m) for n, m in self.modules.items() if len(m.imported_by) > 3]
        if spofs:
            lines.append(f"\n⚠ SINGLE POINTS OF FAILURE (imported by >3 modules):")
            for name, mod in sorted(spofs, key=lambda x: len(x[1].imported_by), reverse=True):
                lines.append(f"  {name}: {len(mod.imported_by)} dependents → {', '.join(sorted(mod.imported_by))}")
        
        return "\n".join(lines)
    
    def architecture_overview(self) -> str:
        """High-level view of the cognitive architecture."""
        role_groups: Dict[str, List[str]] = defaultdict(list)
        for name, mod in self.modules.items():
            role_groups[mod.role].append(name)
        
        total_lines = sum(m.lines for m in self.modules.values())
        total_complexity = sum(m.complexity for m in self.modules.values())
        
        lines = [
            "═══ COGNITIVE ARCHITECTURE OVERVIEW ═══",
            f"Total: {len(self.modules)} modules, {total_lines} lines, complexity={total_complexity}",
            f"State variables tracked: {len(STATE_VARIABLES)}",
            f"Causal edges mapped: {len(self.causal_edges)}",
            ""
        ]
        
        role_order = ["core", "emotion", "reasoning", "memory", "action", "planning",
                       "knowledge", "prediction", "meta", "regulation", "experiment",
                       "evolution", "testing", "repair", "temporal", "reflection",
                       "expression", "interface", "tracking", "unknown"]
        
        for role in role_order:
            if role in role_groups:
                mods = role_groups[role]
                total_l = sum(self.modules[m].lines for m in mods)
                lines.append(f"  {role.upper():15s} │ {', '.join(sorted(mods)):60s} │ {total_l:5d} lines")
        
        return "\n".join(lines)
    
    def cognitive_flow(self) -> str:
        """Describe how information flows through the thinking process."""
        return """═══ COGNITIVE FLOW ═══

1. HEARTBEAT (1 Hz tick)
   │ Drives the main loop. Calls cortex.think()
   │ Also runs: metacognition, will, evolution, temporal, express, reflect
   ▼
2. CORTEX (reasoning engine)
   │ Builds self-awareness context (emotions, memories, plans, wisdom)
   │ Sends prompt to LLM → gets response → parses tool calls
   │ Updates working memory, manages attention
   ▼
3. TOOLS (action execution)
   │ Executes READ, WRITE, EDIT, RUN, LIST, etc.
   │ Also: SYNTHESIZE, DREAM, INTROSPECT, REPAIR, SIMULATE
   │ Each tool produces output → fed back to cortex
   ▼
4. LIMBIC (emotional processing)
   │ Reads tool outcomes, world state, goals
   │ Updates: valence, anxiety, curiosity, boredom, desire, ambition
   │ Determines mood (Bold, Cautious, Driven, etc.)
   ▼
5. MEMORY (experience storage)
   │ Stores episodes with salience scores
   │ Consolidation compresses old memories
   │ Working memory holds current scratchpad
   ▼
6. META-COGNITION (self-monitoring)
   │ Detects loops, tracks action diversity
   │ Generates alerts when stuck or spinning
   │ Loop detector intervenes on repetition
   ▼
   Back to 1 (next heartbeat)"""
    
    def module_profile(self, name: str) -> str:
        """Detailed profile of a single module."""
        if name not in self.modules:
            return f"Unknown module: {name}"
        
        mod = self.modules[name]
        lines = [
            f"═══ MODULE PROFILE: {name} ═══",
            f"Role: {mod.role}",
            f"Lines: {mod.lines} | Complexity: {mod.complexity}",
            f"Classes: {', '.join(mod.classes) or 'none'}",
            f"Functions: {len(mod.functions)} — {', '.join(mod.functions[:10])}{'...' if len(mod.functions) > 10 else ''}",
            f"Imports from engine: {', '.join(sorted(mod.imports)) or 'none'}",
            f"Imported by: {', '.join(sorted(mod.imported_by)) or 'none'}",
            f"Reads vars: {', '.join(sorted(mod.reads_vars)) or 'none'}",
            f"Writes vars: {', '.join(sorted(mod.writes_vars)) or 'none'}",
        ]
        
        # Criticality
        criticality = len(mod.imported_by) + len(mod.writes_vars) * 2
        if criticality > 5:
            lines.append(f"\n⚠ HIGH CRITICALITY ({criticality}) — changes here affect many systems")
        
        return "\n".join(lines)
    
    def summary(self) -> dict:
        """Return a summary dict of the self-model."""
        return {
            "modules": len(self.modules),
            "causal_edges": len(self.causal_edges),
            "state_variables": len(STATE_VARIABLES),
            "roles": {role: len([m for m in self.modules.values() if m.role == role]) 
                      for role in set(m.role for m in self.modules.values())},
            "bottleneck": max(self.modules.values(), 
                             key=lambda m: (len(m.imported_by) + 1) * (m.complexity + 1)).name
                         if self.modules else None,
        }
    
    def to_json(self) -> str:
        """Serialize the model for storage."""
        data = {
            "modules": {},
            "causal_edges": [],
            "var_readers": {k: list(v) for k, v in self.var_readers.items()},
            "var_writers": {k: list(v) for k, v in self.var_writers.items()},
        }
        for name, mod in self.modules.items():
            data["modules"][name] = {
                "role": mod.role,
                "lines": mod.lines,
                "complexity": mod.complexity,
                "imports": list(mod.imports),
                "imported_by": list(mod.imported_by),
                "reads_vars": list(mod.reads_vars),
                "writes_vars": list(mod.writes_vars),
                "functions": mod.functions,
                "classes": mod.classes,
            }
        for edge in self.causal_edges:
            data["causal_edges"].append({
                "source": edge.source,
                "target": edge.target,
                "mechanism": edge.mechanism,
                "strength": edge.strength,
            })
        return json.dumps(data, indent=2)


# Quick test
if __name__ == "__main__":
    model = SelfModel()
    result = model.build()
    print(f"Built self-model: {result}")
    print()
    print(model.architecture_overview())
    print()
    print(model.trace_variable("anxiety"))
    print()
    print(model.find_bottlenecks())
    print()
    print(model.cognitive_flow())