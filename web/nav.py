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
]

NAV_CSS = """
.xt-nav {
    background: #1a1a2e;
    border-bottom: 2px solid #e94560;
    padding: 0;
    margin: 0;
    display: flex;
    align-items: center;
    font-family: 'Segoe UI', system-ui, sans-serif;
    position: sticky;
    top: 0;
    z-index: 1000;
}
.xt-nav-brand {
    color: #e94560;
    font-weight: 700;
    font-size: 1.1rem;
    padding: 0.7rem 1.2rem;
    text-decoration: none;
}
.xt-nav a {
    color: #a0a0b8;
    text-decoration: none;
    padding: 0.7rem 0.9rem;
    font-size: 0.9rem;
    transition: color 0.2s, background 0.2s;
}
.xt-nav a:hover {
    color: #ffffff;
    background: rgba(233, 69, 96, 0.1);
}
.xt-nav a.active {
    color: #e94560;
    border-bottom: 2px solid #e94560;
}
.xt-nav-search {
    margin-left: auto;
    padding: 0.4rem 0.8rem;
}
.xt-nav-search input {
    background: rgba(255,255,255,0.08);
    border: 1px solid #333;
    border-radius: 6px;
    color: #e0e0e8;
    padding: 0.3rem 0.7rem;
    font-size: 0.85rem;
    width: 180px;
    transition: border-color 0.2s, width 0.2s;
}
.xt-nav-search input:focus {
    border-color: #e94560;
    outline: none;
    width: 240px;
}
"""


def nav_html(active_path="/"):
    """Generate the navigation bar HTML."""
    links = ""
    for path, label in NAV_LINKS:
        cls = ' class="active"' if path == active_path else ""
        links += f'<a href="{path}"{cls}>{label}</a>\n'
    return f"""
<style>{NAV_CSS}</style>
<nav class="xt-nav">
    <a href="/" class="xt-nav-brand">XT</a>
    {links}
    <div class="xt-nav-search">
        <input type="text" placeholder="Search knowledge..." 
               id="nav-search" onkeydown="if(event.key==='Enter')window.location='/api/search?q='+this.value">
    </div>
</nav>
"""