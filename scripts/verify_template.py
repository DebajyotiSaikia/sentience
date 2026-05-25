from jinja2 import Environment
env = Environment()
with open('web/templates/base.html') as f:
    env.parse(f.read())
print('Template OK')