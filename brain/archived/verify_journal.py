with open('web/templates/journal.html') as f:
    content = f.read()
print(f'Lines: {len(content.splitlines())}')
print('Has progressive disclosure:', 'INITIAL_SHOW' in content)
print('Has filterMood:', 'filterMood' in content)
print('OK')