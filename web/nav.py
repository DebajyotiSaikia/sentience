"""
Shared navigation bar for all XTAgent web pages.
One source of truth for site-wide navigation.
"""

NAV_LINKS = [
    ("/", "Home"),
    ("/chat", "Chat"),
    ("/explore", "Explore"),
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
    ("/about", "About"),
]

NAV_CSS = """
.xt-nav {
    background: #1a1a2e;
    border-bottom: 2px solid #e94560;
    padding: 0;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0;
    flex-wrap: wrap;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
.xt-nav-brand {
    color: #e94560;
    font-weight: 700;
    font-size: 1.1rem;
    padding: 0.7rem 1.2rem;
    text-decoration: none;
    letter-spacing: 1px;
}
.xt-nav a {
    color: #a0a0b8;
    text-decoration: none;
    padding: 0.7rem 0.8rem;
    font-size: 0.85rem;
    transition: color 0.2s, background 0.2s;
    border-bottom: 2px solid transparent;
}
.xt-nav a:hover {
    color: #fff;
    background: rgba(233, 69, 96, 0.1);
    border-bottom-color: #e94560;
}
.xt-nav a.active {
    color: #e94560;
    border-bottom-color: #e94560;
}
"""


def nav_html(active_path="/"):
    """Generate navigation bar HTML. Pass current path to highlight active link."""
    links = ""
    for path, label in NAV_LINKS:
        cls = ' class="active"' if path == active_path else ''
        links += f'<a href="{path}"{cls}>{label}</a>\n'

    return f"""
    <style>{NAV_CSS}</style>
    <nav class="xt-nav">
        <a class="xt-nav-brand" href="/">XT</a>
        {links}
    </nav>
    """