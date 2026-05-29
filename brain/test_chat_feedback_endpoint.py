"""Tests for the POST /chat/feedback endpoint in web/chat.py."""
import json
import os
import sys
import tempfile
import pytest

# Ensure workspace root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.user_alignment import record_feedback, load_feedback, FEEDBACK_PATH

FEEDBACK_BAK = str(FEEDBACK_PATH) + ".bak"

@pytest.fixture(autouse=True)
def clean_feedback_file():
    """Ensure feedback file is empty before each test."""
    if os.path.exists(FEEDBACK_PATH):
        os.rename(FEEDBACK_PATH, FEEDBACK_BAK)
    yield
    # Restore original
    if os.path.exists(FEEDBACK_BAK):
        os.rename(FEEDBACK_BAK, FEEDBACK_PATH)
    elif os.path.exists(FEEDBACK_PATH):
        os.remove(FEEDBACK_PATH)


def _get_app():
    """Create a minimal Flask test app with chat_bp."""
    from flask import Flask
    from web.chat import chat_bp
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(chat_bp, url_prefix='/chat')
    return app


def test_feedback_missing_body():
    app = _get_app()
    with app.test_client() as c:
        resp = c.post('/chat/feedback', data='', content_type='application/json')
        assert resp.status_code == 400


def test_feedback_missing_rating():
    app = _get_app()
    with app.test_client() as c:
        resp = c.post('/chat/feedback',
                       data=json.dumps({'message_id': 'x'}),
                       content_type='application/json')
        assert resp.status_code == 400
        assert 'rating' in resp.get_json()['error'].lower()


def test_feedback_invalid_rating_string():
    app = _get_app()
    with app.test_client() as c:
        resp = c.post('/chat/feedback',
                       data=json.dumps({'rating': 'bad'}),
                       content_type='application/json')
        assert resp.status_code == 400


def test_feedback_rating_out_of_range():
    app = _get_app()
    with app.test_client() as c:
        resp = c.post('/chat/feedback',
                       data=json.dumps({'rating': 6}),
                       content_type='application/json')
        assert resp.status_code == 400


def test_feedback_valid_minimal():
    app = _get_app()
    with app.test_client() as c:
        resp = c.post('/chat/feedback',
                       data=json.dumps({'rating': 4}),
                       content_type='application/json')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['status'] == 'recorded'
        assert body['feedback']['rating'] == 4


def test_feedback_valid_full():
    app = _get_app()
    with app.test_client() as c:
        resp = c.post('/chat/feedback',
                       data=json.dumps({
                           'message_id': 'msg-123',
                           'rating': 5,
                           'comment': 'Great answer!',
                           'tags': ['helpful', 'detailed']
                       }),
                       content_type='application/json')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['feedback']['rating'] == 5
        assert body['feedback']['comment'] == 'Great answer!'


def test_feedback_persisted():
    """Verify that feedback is actually saved to disk."""
    app = _get_app()
    with app.test_client() as c:
        c.post('/chat/feedback',
               data=json.dumps({'rating': 3, 'comment': 'okay'}),
               content_type='application/json')
    saved = load_feedback()
    assert len(saved) == 1
    assert saved[0]['rating'] == 3
    assert saved[0]['comment'] == 'okay'