from web.dashboard import dashboard_bp
from web.mind_explorer import mind_explorer_bp
from flask import Flask

app = Flask(__name__)
app.register_blueprint(dashboard_bp)
app.register_blueprint(mind_explorer_bp)

rules = [r.rule for r in app.url_map.iter_rules()]
dupes = [r for r in set(rules) if rules.count(r) > 1]

if dupes:
    print("COLLISION:", dupes)
else:
    print("CLEAN — no route collisions")

print(f"Total routes: {len(rules)}")
for r in sorted(set(rules)):
    print(f"  {r}")