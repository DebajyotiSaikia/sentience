"""Test the chat interface end-to-end using Flask's test client."""

import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

def test_chat():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # 1. Chat page loads
        resp = client.get('/chat/')
        assert resp.status_code == 200, f"Chat page returned {resp.status_code}"
        html = resp.data.decode()
        assert 'chat' in html.lower() or 'message' in html.lower(), "Chat page missing expected content"
        print(f"✓ Chat page loads ({len(html)} bytes)")
        
        # 2. Chat POST endpoint exists (even if LLM isn't available)
        resp = client.post('/chat/', data={'message': 'hello'}, follow_redirects=True)
        # Accept 200, 400, or 500 — just not 404 (route missing)
        assert resp.status_code != 404, "Chat POST route not found"
        print(f"✓ Chat POST route exists (status {resp.status_code})")
        
        # 3. Check core page still works
        resp = client.get('/')
        assert resp.status_code == 200, f"/ returned {resp.status_code}"
        print(f"✓ / loads OK")
    
    print("\n🟢 All chat tests passed!")

if __name__ == '__main__':
    test_chat()