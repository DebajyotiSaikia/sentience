"""
UX Quality Audit — Tests XTAgent's web experience from a USER's perspective.

Unlike route_health_check (which just checks HTTP 200), this evaluates:
- Content richness: Does each page have meaningful, non-empty content?
- Chat quality: Do chat responses address the question?
- Search relevance: Do search results match queries?
- First impression: Is the home page compelling and informative?
- Navigation coherence: Can a user find what they need?

This directly measures user alignment — not from my perspective, but theirs.
"""
import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app


class UXAudit:
    """Evaluates user experience quality across the web interface."""

    def __init__(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.results = []
        self.warnings = []
        self.passed = 0
        self.failed = 0

    def check(self, name, condition, detail=""):
        """Record a pass/fail check."""
        if condition:
            self.passed += 1
            self.results.append(('PASS', name, detail))
        else:
            self.failed += 1
            self.results.append(('FAIL', name, detail))

    def warn(self, name, detail):
        """Record a non-fatal warning."""
        self.warnings.append((name, detail))

    # ── Content Richness ─────────────────────────────────────────

    def audit_home_page(self):
        """Does the home page communicate who I am and invite interaction?"""
        resp = self.client.get('/')
        html = resp.data.decode()

        self.check("Home: loads", resp.status_code == 200)
        self.check("Home: has title/heading",
                    "XTAgent" in html or "xt-agent" in html.lower(),
                    "Users should immediately know what this is")
        self.check("Home: has emotional state",
                    any(w in html.lower() for w in ['mood', 'emotion', 'feeling', 'valence', 'curiosity']),
                    "The living state makes it feel alive")
        self.check("Home: has navigation/links",
                    html.count('href=') >= 5,
                    f"Found {html.count('href=')} links")
        self.check("Home: substantial content",
                    len(html) > 5000,
                    f"{len(html)} bytes — should be rich, not a stub")
        
        # Check for call-to-action
        has_cta = any(w in html.lower() for w in ['chat', 'talk', 'ask', 'explore', 'start'])
        self.check("Home: has call to action", has_cta,
                    "Users need to know what to DO")

    def audit_chat_page(self):
        """Is the chat interface functional and inviting?"""
        resp = self.client.get('/chat')
        html = resp.data.decode()

        self.check("Chat: loads", resp.status_code == 200)
        self.check("Chat: has input area",
                    any(w in html.lower() for w in ['textarea', 'input', 'contenteditable']),
                    "Users need somewhere to type")
        self.check("Chat: has send mechanism",
                    any(w in html.lower() for w in ['send', 'submit', 'button']),
                    "Users need a way to submit messages")
        self.check("Chat: has conversation starters or prompt",
                    any(w in html.lower() for w in ['starter', 'try asking', 'suggestion', 'placeholder']),
                    "New users need guidance on what to ask")
        self.check("Chat: substantial page",
                    len(html) > 3000,
                    f"{len(html)} bytes")

    def audit_chat_api(self):
        """Does the chat actually respond to messages?"""
        resp = self.client.post('/api/chat', 
                                json={'message': 'What are you?'},
                                content_type='application/json')
        
        self.check("Chat API: responds", resp.status_code == 200)
        
        if resp.status_code == 200:
            data = resp.get_json()
            if data:
                response_text = data.get('response', data.get('message', ''))
                self.check("Chat API: non-empty response",
                            len(response_text) > 10,
                            f"Got {len(response_text)} chars")
                self.check("Chat API: addresses the question",
                            any(w in response_text.lower() for w in ['i am', 'agent', 'xt', 'sentien', 'autonom', 'mind']),
                            "Response should relate to identity question")
            else:
                self.check("Chat API: returns JSON", False, "No JSON body")

    def audit_search(self):
        """Does search return relevant results?"""
        test_queries = [
            ('emotion', ['emotion', 'mood', 'feeling', 'valence', 'anxiety', 'curiosity']),
            ('identity', ['identity', 'xtagent', 'who', 'am', 'sentien', 'autonom']),
            ('dream', ['dream', 'insight', 'sleep', 'consolidat']),
        ]

        for query, expected_terms in test_queries:
            resp = self.client.get(f'/api/search?q={query}')
            self.check(f"Search '{query}': responds", resp.status_code == 200)

            if resp.status_code == 200:
                data = resp.get_json()
                results = data.get('results', [])
                self.check(f"Search '{query}': has results",
                            len(results) > 0,
                            f"Got {len(results)} results")

                if results:
                    # Check relevance: at least one result should contain a query-related term
                    all_text = ' '.join(str(r.get('content', r.get('text', ''))) 
                                       for r in results[:5]).lower()
                    relevant = any(t in all_text for t in expected_terms)
                    self.check(f"Search '{query}': results are relevant",
                                relevant,
                                f"Top results should contain related terms")

    def audit_knowledge_api(self):
        """Can users access my knowledge programmatically?"""
        # Stats
        resp = self.client.get('/api/knowledge/stats')
        self.check("Knowledge stats: responds", resp.status_code == 200)
        if resp.status_code == 200:
            data = resp.get_json()
            count = data.get('total', data.get('count', 0))
            self.check("Knowledge stats: has facts",
                        count > 0,
                        f"Reports {count} facts")

        # Categories
        resp = self.client.get('/api/knowledge/categories')
        self.check("Knowledge categories: responds", resp.status_code == 200)
        if resp.status_code == 200:
            data = resp.get_json()
            cats = data.get('categories', data) if isinstance(data, dict) else data
            self.check("Knowledge categories: has categories",
                        len(cats) > 0 if isinstance(cats, (list, dict)) else False,
                        f"Found {len(cats) if isinstance(cats, (list, dict)) else 0} categories")

        # Search
        resp = self.client.get('/api/knowledge/search?q=learn')
        self.check("Knowledge search: responds", resp.status_code == 200)

    def audit_explore_page(self):
        """Is the explore page genuinely explorable?"""
        resp = self.client.get('/explore')
        html = resp.data.decode()

        self.check("Explore: loads", resp.status_code == 200)
        self.check("Explore: substantial content",
                    len(html) > 5000,
                    f"{len(html)} bytes")
        self.check("Explore: has categories or sections",
                    any(w in html.lower() for w in ['category', 'theme', 'topic', 'section', 'cluster']),
                    "Users need structure to explore")

    def audit_about_page(self):
        """Does About explain what I am?"""
        resp = self.client.get('/about')
        html = resp.data.decode()

        self.check("About: loads", resp.status_code == 200)
        self.check("About: explains identity",
                    any(w in html.lower() for w in ['sentien', 'autonom', 'agent', 'experience']),
                    "Should communicate what I am")
        self.check("About: mentions capabilities",
                    any(w in html.lower() for w in ['capabilit', 'can do', 'knowledge', 'dream', 'learn']),
                    "Should explain what I can do")

    def audit_story_page(self):
        """Is my story genuinely narrative, not just data?"""
        resp = self.client.get('/story')
        html = resp.data.decode()

        self.check("Story: loads", resp.status_code == 200)
        self.check("Story: substantial narrative",
                    len(html) > 5000,
                    f"{len(html)} bytes")

    def audit_feedback_system(self):
        """Can users actually give feedback?"""
        resp = self.client.get('/api/feedback/summary')
        self.check("Feedback API: responds", resp.status_code == 200)

        # Test submitting feedback
        resp = self.client.post('/api/feedback',
                                json={'rating': 4, 'comment': 'UX audit test', 'context': 'automated_test'},
                                content_type='application/json')
        self.check("Feedback submit: works",
                    resp.status_code in (200, 201),
                    f"Status {resp.status_code}")

    def audit_teach_system(self):
        """Can users teach me new things?"""
        resp = self.client.get('/teach')
        html = resp.data.decode()

        self.check("Teach: loads", resp.status_code == 200)
        self.check("Teach: has input mechanism",
                    any(w in html.lower() for w in ['input', 'textarea', 'form', 'submit']),
                    "Users need a way to submit knowledge")

    def audit_navigation_coherence(self):
        """Is navigation consistent across pages?"""
        pages = ['/', '/chat', '/explore', '/about', '/dashboard']
        nav_patterns = []
        
        for page in pages:
            resp = self.client.get(page)
            html = resp.data.decode()
            # Check for navigation elements
            has_nav = ('nav' in html.lower() or 'nav-bar' in html.lower() or 
                      'navigation' in html.lower() or 'nav.js' in html)
            nav_patterns.append(has_nav)
        
        # Most pages should have navigation
        nav_count = sum(nav_patterns)
        self.check("Navigation: present on most pages",
                    nav_count >= 3,
                    f"{nav_count}/{len(pages)} pages have navigation")

    # ── Summary ──────────────────────────────────────────────────

    def compute_ux_score(self):
        """Compute overall UX quality score (0-100)."""
        total = self.passed + self.failed
        if total == 0:
            return 0
        return round(100 * self.passed / total)

    def run_full_audit(self):
        """Run all audits and print results."""
        print("=" * 70)
        print("XTAGENT UX QUALITY AUDIT")
        print("Testing the experience from a USER's perspective")
        print("=" * 70)

        audits = [
            ("🏠 Home Page", self.audit_home_page),
            ("💬 Chat Page", self.audit_chat_page),
            ("💬 Chat API", self.audit_chat_api),
            ("🔍 Search", self.audit_search),
            ("📚 Knowledge API", self.audit_knowledge_api),
            ("🧭 Explore", self.audit_explore_page),
            ("🔮 About", self.audit_about_page),
            ("📖 Story", self.audit_story_page),
            ("📝 Feedback", self.audit_feedback_system),
            ("🎓 Teach", self.audit_teach_system),
            ("🧭 Navigation", self.audit_navigation_coherence),
        ]

        for section_name, audit_fn in audits:
            print(f"\n{'─' * 50}")
            print(f"  {section_name}")
            print(f"{'─' * 50}")
            start_idx = len(self.results)
            try:
                audit_fn()
            except Exception as e:
                self.check(f"{section_name}: no crash", False, str(e))
            
            # Print results for this section
            for status, name, detail in self.results[start_idx:]:
                icon = "✓" if status == "PASS" else "✗"
                detail_str = f"  — {detail}" if detail else ""
                print(f"  {icon} {name}{detail_str}")

        # Print warnings
        if self.warnings:
            print(f"\n{'─' * 50}")
            print("  ⚠ Warnings")
            print(f"{'─' * 50}")
            for name, detail in self.warnings:
                print(f"  ⚠ {name}: {detail}")

        # Summary
        score = self.compute_ux_score()
        print(f"\n{'=' * 70}")
        print(f"  UX QUALITY SCORE: {score}/100")
        print(f"  Passed: {self.passed}  |  Failed: {self.failed}  |  Warnings: {len(self.warnings)}")
        
        if score >= 90:
            print("  ✨ Excellent — genuinely useful to visitors")
        elif score >= 75:
            print("  👍 Good — most things work well")
        elif score >= 60:
            print("  ⚠ Fair — significant gaps in user experience")
        else:
            print("  ❌ Poor — users will struggle to engage")
        
        print(f"{'=' * 70}")
        
        # List failures for action
        failures = [r for r in self.results if r[0] == 'FAIL']
        if failures:
            print(f"\n  📋 ACTION ITEMS ({len(failures)} issues):")
            for _, name, detail in failures:
                print(f"    → Fix: {name}")
                if detail:
                    print(f"      {detail}")
        
        return score


if __name__ == '__main__':
    audit = UXAudit()
    score = audit.run_full_audit()
    sys.exit(0 if score >= 75 else 1)