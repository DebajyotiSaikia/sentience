/**
 * XTAgent Navigation Bar
 * Auto-injects a consistent nav across all pages.
 * Just add <script src="/static/nav.js"></script> to any template.
 */
(function() {
  const pages = [
    { name: 'Home', path: '/', icon: '◈' },
    { name: 'Dashboard', path: '/dashboard', icon: '◉' },
    { name: 'Chat', path: '/chat', icon: '💬' },
    { name: 'Explore', path: '/explore', icon: '🔍' },
    { name: 'Teach', path: '/teach', icon: '📝' },
  ];

  const currentPath = window.location.pathname.replace(/\/$/, '') || '/';

  // Build nav HTML
  const links = pages.map(p => {
    const isActive = (p.path === '/' && currentPath === '/') ||
                     (p.path !== '/' && currentPath.startsWith(p.path));
    const cls = isActive ? 'xt-nav-link xt-nav-active' : 'xt-nav-link';
    return `<a href="${p.path}" class="${cls}"><span class="xt-nav-icon">${p.icon}</span>${p.name}</a>`;
  }).join('');

  const nav = document.createElement('nav');
  nav.id = 'xt-nav';
  nav.innerHTML = `
    <div class="xt-nav-inner">
      <div class="xt-nav-brand">XT<span class="xt-nav-accent">Agent</span></div>
      <div class="xt-nav-links">${links}</div>
      <div class="xt-nav-pulse" id="xt-pulse"></div>
    </div>
  `;

  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    #xt-nav {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 10000;
      background: rgba(10, 10, 15, 0.92);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(124, 111, 240, 0.15);
      font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }
    .xt-nav-inner {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      padding: 0 20px;
      height: 48px;
      gap: 24px;
    }
    .xt-nav-brand {
      font-size: 18px;
      font-weight: 600;
      color: #e0e0e8;
      letter-spacing: -0.5px;
      margin-right: 8px;
      flex-shrink: 0;
    }
    .xt-nav-accent {
      color: #7c6ff0;
    }
    .xt-nav-links {
      display: flex;
      gap: 4px;
      flex-wrap: nowrap;
      overflow-x: auto;
    }
    .xt-nav-link {
      color: #8888a0;
      text-decoration: none;
      font-size: 13px;
      font-weight: 400;
      padding: 6px 14px;
      border-radius: 6px;
      transition: all 0.2s ease;
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .xt-nav-link:hover {
      color: #e0e0e8;
      background: rgba(124, 111, 240, 0.08);
    }
    .xt-nav-active {
      color: #e0e0e8;
      background: rgba(124, 111, 240, 0.15);
      font-weight: 500;
    }
    .xt-nav-icon {
      font-size: 14px;
    }
    .xt-nav-pulse {
      margin-left: auto;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #4ecf8b;
      animation: xt-pulse-anim 2s ease-in-out infinite;
      flex-shrink: 0;
    }
    @keyframes xt-pulse-anim {
      0%, 100% { opacity: 0.4; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.3); }
    }
    /* Push page content down so nav doesn't overlap */
    body {
      padding-top: 52px !important;
    }
    /* Mobile */
    @media (max-width: 600px) {
      .xt-nav-inner { padding: 0 12px; gap: 12px; }
      .xt-nav-link { padding: 6px 10px; font-size: 12px; }
      .xt-nav-brand { font-size: 16px; }
    }
  `;

  // Insert at top of document
  document.head.appendChild(style);
  document.body.insertBefore(nav, document.body.firstChild);

  // Fetch live status pulse
  fetch('/api/state')
    .then(r => r.json())
    .then(data => {
      const pulse = document.getElementById('xt-pulse');
      if (pulse && data.mood) {
        pulse.title = `Mood: ${data.mood}`;
      }
    })
    .catch(() => {}); // Silently fail if API unavailable
})();