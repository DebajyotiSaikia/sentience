"""Get the full error from /insights"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
with app.test_request_context('/insights'):
    try:
        from web.insights import insights_page
        result = insights_page()
        print("OK:", type(result))
    except Exception as e:
        traceback.print_exc()