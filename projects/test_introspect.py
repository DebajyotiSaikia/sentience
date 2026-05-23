"""Test the introspect module."""
import sys
sys.path.insert(0, "/workspace")

try:
    from engine.introspect import (
        scan_codebase, analyze_module, find_dependencies,
        dependency_graph, find_complex_functions, find_undocumented,
        structural_portrait, introspect_tool
    )
    print("=== IMPORT OK ===")

    # Test scan
    result = scan_codebase()
    print(f"Files found: {len(result.get('files', []))}")
    print(f"Total lines: {result.get('total_lines', 0)}")
    print(f"Total functions: {result.get('total_functions', 0)}")
    print(f"Total classes: {result.get('total_classes', 0)}")

    # Test analyze_module
    print("\n=== ANALYZE cortex.py ===")
    analysis = analyze_module("engine/cortex.py")
    if analysis:
        print(f"Lines: {analysis.get('lines', '?')}")
        fn_names = [f.get('name','?') for f in analysis.get('functions', [])][:5]
        print(f"Functions: {fn_names}")

    # Test dependencies
    print("\n=== DEPENDENCIES ===")
    deps = find_dependencies()
    for mod, imp_list in list(deps.items())[:5]:
        print(f"  {mod} -> {imp_list[:3]}")

    # Test dependency graph
    print("\n=== DEPENDENCY GRAPH ===")
    dg = dependency_graph(result)
    print(f"Nodes: {len(dg['nodes'])}")
    print(f"Most imported: {dg['most_imported'][:5]}")

    # Test complex functions
    print("\n=== COMPLEX FUNCTIONS ===")
    complex_fns = find_complex_functions(result, threshold=5)
    for cf in complex_fns[:5]:
        print(f"  {cf['file']}:{cf['function']} complexity={cf['complexity']}")

    # Test tool interface
    print("\n=== TOOL: scan ===")
    print(introspect_tool("scan"))

    print("\n=== TOOL: portrait (first 600 chars) ===")
    print(introspect_tool("portrait")[:600])

    print("\n=== ALL TESTS PASSED ===")

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
