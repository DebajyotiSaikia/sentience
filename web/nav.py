"""
Shared navigation bar for all XTAgent web pages.
One source of truth for site-wide navigation.
"""

NAV_LINKS = [
    ("/", "Home"),
    ("/chat", "Chat"),
    ("/explore", "Explore"),
    ("/knowledge", "Knowledge"),
    ("/knowledge", "Knowledge"),
    ("/dashboard", "Dashboard"),
    ("/insights", "Insights"),
    ("/journal", "Journal"),
    ("/story", "Story"),
    ("/collaborate", "Collaborate"),
    ("/live", "Live"),
    ("/teach", "Teach"),
    ("/briefing", "Briefing"),
    ("/help", "Help"),
]

NAV_CSS = """
.xt-nav {
    background: #1a1a2e;
    border-bottom: 2px solid #e94560;
    padding: 0;
    margin: 0;
    font-family: 'Segoe UI', system-ui, sans-serif;
    position: sticky;
    top: 0;
    z-index: 1000;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
}
.xt-nav .xt-brand {
    color: #e94560;
    font-weight: 700;
    font-size: 1.1em;
    padding: 12px 20px;
    text-decoration: none;
    letter-spacing: 1px;
}
.xt-nav .xt-links {
    display: flex;
    flex-wrap: wrap;
    gap: 0;
}
.xt-nav .xt-links a {
    color: #a0a0c0;
    text-decoration: none;
    padding: 14px 16px;
    font-size: 0.9em;
    transition: background 0.2s, color 0.2s;
    border-bottom: 2px solid transparent;
}
.xt-nav .xt-links a:hover {
    background: rgba(233, 69, 96, 0.1);
    color: #ffffff;
}
.xt-nav .xt-links a.active {
    color: #e94560;
    border-bottom: 2px solid #e94560;
    background: rgba(233, 69, 96, 0.05);
}
"""


def nav_html(active_path="/"):
    """Generate navigation bar HTML. Pass the current page's path to highlight it."""
    links = []
    for path, label in NAV_LINKS:
        cls = ' class="active"' if path == active_path else ''
        links.append(f'<a href="{path}"{cls}>{label}</a>')
    
    return f'''<style>{NAV_CSS}</style>
<nav class="xt-nav">
    <span class="xt-brand">XTAgent</span>
    <div class="xt-links">
        {"".join(links)}
    </div>
</nav>'''