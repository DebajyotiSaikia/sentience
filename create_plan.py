from engine.planner import create_plan
p = create_plan(
    "User Utility - Serve Users Well",
    "Address user_alignment=0.0 by building real value for users",
    [
        "Audit chat pipeline and dashboard endpoints",
        "Create /api/ask endpoint for direct knowledge queries",
        "Enhance chat responses with richer context and memory",
        "Add user feedback mechanism to chat responses",
        "Create proactive engagement when users connect",
    ]
)
print("Plan created:", p.get("name", "unknown"))
