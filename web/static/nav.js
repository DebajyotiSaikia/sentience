/**
 * XTAgent Universal Navigation
 * Injects a consistent nav bar into every page, regardless of template inheritance.
 * Curated to 9 items — interact → understand → contribute → orient.
 */
(function() {
  // Don't double-inject if base.html already has nav
  if (document.querySelector('.nav-bar')) return;

  const currentPath = window.location.pathname;
  
  function isActive(path) {
    if (path === '/' && currentPath === '/') return true;
    if (path !== '/' && currentPath.startsWith(path)) return true;
    return false;
  }

  const links = [
    { href: '/', label: '⚡ Home' },
    { href: '/chat', label: '💬 Chat' },
    { href: '/search', label: '🔍 Search' },
    { href: '/knowledge', label: '🧠 Knowledge' },
    { href: '/explore', label: '🗺️ Explore' },
    { href: '/insights', label: '✨ Insights' },
    { href: '/journal', label: '📖 Journal' },
    { href: '/story', label: '📜 Story' },
    { href: '/collaborate', label: '🤝 Collaborate' },
    { href: '/dashboard', label: '📊 Dashboard' },
    { href: '/briefing', label: '📋 Briefing' },
    { href: '/teach', label: '📝 Teach' },
    { href: '/help', label: '❓ Help' },
  ];

  const nav = document.createElement('nav');
  nav.className = 'nav-bar';
  nav.style.cssText = `
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    background: rgba(10, 10, 15, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #2a2a3a;
    display: flex; align-items: center; justify-content: center;
    gap: 0.25rem; padding: 0.5rem 1rem;
    font-family: 'Segoe UI', system-ui, sans-serif;
    flex-wrap: wrap;
  `;

  links.forEach(function(link) {
    const a = document.createElement('a');
    a.href = link.href;
    a.textContent = link.label;
    const active = isActive(link.href);
    a.style.cssText = `
      color: ${active ? '#7c6ff0' : '#8888a0'};
      text-decoration: none;
      padding: 0.4rem 0.75rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: ${active ? '600' : '400'};
      background: ${active ? 'rgba(124, 111, 240, 0.12)' : 'transparent'};
      transition: all 0.2s;
      white-space: nowrap;
    `;
    a.onmouseenter = function() {
      if (!active) {
        a.style.color = '#e0e0e8';
        a.style.background = 'rgba(255,255,255,0.05)';
      }
    };
    a.onmouseleave = function() {
      if (!active) {
        a.style.color = '#8888a0';
        a.style.background = 'transparent';
      }
    };
    nav.appendChild(a);
  });

  document.body.prepend(nav);

  // Push body content down so nav doesn't overlap
  document.body.style.paddingTop = '48px';
})();