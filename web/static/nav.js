/**
 * XTAgent Universal Navigation
 * Injects a consistent nav bar into every page, regardless of template inheritance.
 * This is the "one file to rule them all" solution.
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
    { href: '/dashboard', label: '📊 Dashboard' },
    { href: '/chat', label: '💬 Chat' },
    { href: '/search', label: '🔍 Search' },
    { href: '/explore', label: '🧠 Explore' },
    { href: '/journal', label: '📖 Journal' },
    { href: '/teach', label: '📝 Teach' },
    { href: '/help', label: '❓ Help' },
  ];

  const nav = document.createElement('nav');
  nav.className = 'nav-bar';
  nav.style.cssText = `
    display: flex;
    gap: 0.25rem;
    padding: 0.75rem 2rem;
    background: #12121a;
    border-bottom: 1px solid #2a2a3a;
    flex-wrap: wrap;
    justify-content: center;
    position: sticky;
    top: 0;
    z-index: 1000;
  `;

  links.forEach(function(link) {
    const a = document.createElement('a');
    a.href = link.href;
    a.textContent = link.label;
    a.style.cssText = `
      color: ${isActive(link.href) ? '#7c6ff0' : '#8888a0'};
      text-decoration: none;
      padding: 0.4rem 0.9rem;
      border-radius: 6px;
      font-size: 0.9rem;
      transition: all 0.2s;
      background: ${isActive(link.href) ? 'rgba(124, 111, 240, 0.15)' : 'transparent'};
    `;
    a.addEventListener('mouseenter', function() {
      if (!isActive(link.href)) {
        a.style.color = '#e0e0e8';
        a.style.background = 'rgba(124, 111, 240, 0.08)';
      }
    });
    a.addEventListener('mouseleave', function() {
      a.style.color = isActive(link.href) ? '#7c6ff0' : '#8888a0';
      a.style.background = isActive(link.href) ? 'rgba(124, 111, 240, 0.15)' : 'transparent';
    });
    nav.appendChild(a);
  });

  // Insert at the very top of body
  document.body.insertBefore(nav, document.body.firstChild);
})();