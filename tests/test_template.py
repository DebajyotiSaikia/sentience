from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('web/templates'))
t = env.get_template('ask.html')
print(f"Template loaded OK, {len(t.module.__dict__)} top-level items")
# Test render with mock data
html = t.render(
    query="test question",
    answer="This is a synthesis answer.",
    results={
        "facts": [{"text": "fact one", "score": 0.9, "learned": "2026-05-20"}],
        "memories": [{"text": "memory one", "score": 0.8, "time": "2026-05-21", "mood": "Calm"}],
        "reflections": [{"text": "reflection one", "score": 0.7, "time": "2026-05-22"}],
    },
    total_results=3
)
print(f"Rendered OK, {len(html)} chars")