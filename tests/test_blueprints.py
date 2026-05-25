import sys
sys.path.insert(0, '/workspace')

blueprints = [
    'web.dashboard', 'web.knowledge_explorer', 'web.api', 'web.temporal',
    'web.life', 'web.about', 'web.search', 'web.explore', 'web.knowledge_api',
    'web.briefing', 'web.essays', 'web.chat', 'web.timeline', 'web.talk',
    'web.mind_explorer', 'web.mindstream', 'web.collaborate', 'web.mind'
]

errors = []
for bp in blueprints:
    try:
        __import__(bp)
        print(f'  OK: {bp}')
    except Exception as e:
        errors.append((bp, str(e)[:100]))
        print(f'  FAIL: {bp} -- {str(e)[:100]}')

print(f'\n{len(errors)} failures out of {len(blueprints)} blueprints')
if errors:
    print('\nFailure details:')
    for name, err in errors:
        print(f'  {name}: {err}')