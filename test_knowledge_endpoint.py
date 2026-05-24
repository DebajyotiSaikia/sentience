import sys, os
sys.path.insert(0, '.')
os.chdir('/home/xt')

from web.knowledge_api import knowledge_api
from flask import Flask

app = Flask(__name__, template_folder='web/templates')
app.register_blueprint(knowledge_api)

with app.test_client() as c:
    resp = c.get('/knowledge')
    print(f'Status: {resp.status_code}')
    data = resp.data.decode()
    if 'Knowledge Explorer' in data:
        print('Template rendered OK')
    if resp.status_code == 200:
        # Check for data presence
        count = data.count('fact-card') or data.count('<tr')
        print(f'Approximate entries rendered: {count}')
        print(f'Response length: {len(data)} chars')
    else:
        print('ERROR:', data[:500])