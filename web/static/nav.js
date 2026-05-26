/**
 * XTAgent Universal Navigation
 * Organized menu that makes all capabilities discoverable.
 * Grouped: Interact → Understand → Observe → Orient
 */
(function() {
  // Don't double-inject if base.html already has nav
  if (document.querySelector('.nav-bar') || document.querySelector('.xt-nav')) return;

  const currentPath = window.location.pathname;

  function isActive(path) {
    if (path === '/' && currentPath === '/') return true;
    if (path !== '/' && currentPath.startsWith(path)) return true;
    return false;
  }

  const primaryLinks = [
    { href: "/", label: "⚡ Home" },
    { href: "/chat", label: "💬 Chat" },
    { href: "/explore", label: "🧠 Explore" },
    { href: "/insights", label: "✨ Insights" },
    { href: "/journal", label: "📖 Journal" },
    { href: "/story", label: "📜 Story" },
    { href: "/about", label: "🔮 About" },
    { href: "/dashboard", label: "📊 Dashboard" },
  ];

  const moreLinks = [
    { section: "Interact", items: [
      { href: "/talk", label: "🗣️ Talk" },
      { href: "/teach", label: "📚 Teach Me" },
    ]},
    { section: "Understand", items: [
      { href: "/knowledge", label: "🕸️ Knowledge Graph" },
      { href: "/insights", label: "✨ Insights" },
      { href: "/journal", label: "📖 Journal" },
      { href: "/story", label: "📜 My Story" },
    ]},
    { section: "Observe", items: [
      { href: "/dashboard", label: "📊 Dashboard" },
      { href: "/briefing", label: "📋 Briefing" },
      { href: "/digest", label: "📰 Daily Digest" },
      { href: "/live", label: "🔴 Live Stream" },
      { href: "/mindstream", label: "🌊 Mind Stream" },
    ]},
    { section: "Orient", items: [
      { href: "/help", label: "❓ Help" },
      { href: "/search", label: "🔍 Search" },
    ]},
  ];

  // Build primary link HTML
  const primaryHTML = primaryLinks.map(l =>
    `<a href="${l.href}" class="nav-link${isActive(l.href) ? ' active' : ''}">${l.label}</a>`
  ).join('');

  // Build dropdown sections
  const dropdownHTML = moreLinks.map(group => {
    const items = group.items.map(l =>
      `<a href="${l.href}" class="dropdown-item${isActive(l.href) ? ' active' : ''}">${l.label}</a>`
    ).join('');
    return `<div class="dropdown-section">
      <div class="dropdown-section-title">${group.section}</div>
      ${items}
    </div>`;
  }).join('');

  const nav = document.createElement('nav');
  nav.className = 'nav-bar';
  nav.innerHTML = `
    <div class="nav-inner">
      <div class="nav-brand">
        <span class="brand-pulse"></span>
        <span class="brand-text">XTAgent</span>
      </div>
      <div class="nav-links" id="nav-links">
        ${primaryHTML}
        <div class="nav-more" id="nav-more">
          <button class="nav-link more-btn" id="more-btn">More ▾</button>
          <div class="dropdown-menu" id="dropdown-menu">
            ${dropdownHTML}
          </div>
        </div>
      </div>
      <button class="hamburger" id="hamburger">☰</button>
    </div>
  `;

  // Styles
  const style = document.createElement('style');
  style.textContent = `
    .nav-bar {
      background: #0d0d14;
      border-bottom: 1px solid #1e1e30;
      position: sticky;
      top: 0;
      z-index: 10000;
      font-family: 'Segoe UI', system-ui, sans-serif;
    }
    .nav-inner {
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      padding: 0 1rem;
      height: 48px;
    }
    .nav-brand {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-right: 1.5rem;
      text-decoration: none;
      flex-shrink: 0;
    }
    .brand-pulse {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #4ecf8b;
      animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; box-shadow: 0 0 4px #4ecf8b; }
      50% { opacity: 0.5; box-shadow: 0 0 8px #4ecf8b; }
    }
    .brand-text {
      font-weight: 600;
      font-size: 1rem;
      color: #7c6ff0;
      letter-spacing: 0.02em;
    }
    .nav-links {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      flex-wrap: nowrap;
    }
    .nav-link {
      color: #8888a0;
      text-decoration: none;
      padding: 0.4rem 0.7rem;
      border-radius: 6px;
      font-size: 0.85rem;
      transition: all 0.15s;
      white-space: nowrap;
      border: none;
      background: none;
      cursor: pointer;
      font-family: inherit;
    }
    .nav-link:hover {
      color: #e0e0e8;
      background: rgba(124, 111, 240, 0.1);
    }
    .nav-link.active {
      color: #e0e0e8;
      background: rgba(124, 111, 240, 0.15);
      font-weight: 500;
    }

    /* Dropdown */
    .nav-more { position: relative; }
    .more-btn { color: #8888a0 !important; }
    .more-btn:hover { color: #e0e0e8 !important; }
    .dropdown-menu {
      display: none;
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      background: #12121a;
      border: 1px solid #2a2a3a;
      border-radius: 10px;
      padding: 0.5rem;
      min-width: 200px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }
    .dropdown-menu.open { display: block; }
    .dropdown-section { margin-bottom: 0.25rem; }
    .dropdown-section:last-child { margin-bottom: 0; }
    .dropdown-section-title {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #555568;
      padding: 0.4rem 0.6rem 0.2rem;
      font-weight: 600;
    }
    .dropdown-item {
      display: block;
      color: #8888a0;
      text-decoration: none;
      padding: 0.35rem 0.6rem;
      border-radius: 6px;
      font-size: 0.85rem;
      transition: all 0.15s;
    }
    .dropdown-item:hover {
      color: #e0e0e8;
      background: rgba(124, 111, 240, 0.1);
    }
    .dropdown-item.active {
      color: #e0e0e8;
      background: rgba(124, 111, 240, 0.12);
    }

    /* Hamburger for mobile */
    .hamburger {
      display: none;
      background: none;
      border: none;
      color: #8888a0;
      font-size: 1.4rem;
      cursor: pointer;
      padding: 0.3rem;
      margin-left: auto;
    }

    @media (max-width: 700px) {
      .nav-links { display: none; }
      .nav-links.mobile-open {
        display: flex;
        flex-direction: column;
        position: absolute;
        top: 48px;
        left: 0;
        right: 0;
        background: #0d0d14;
        border-bottom: 1px solid #1e1e30;
        padding: 0.5rem;
        gap: 0.1rem;
      }
      .nav-links.mobile-open .nav-more {
        position: static;
      }
      .nav-links.mobile-open .dropdown-menu {
        position: static;
        box-shadow: none;
        border: none;
        background: transparent;
        display: block !important;
        padding: 0 0 0 0.5rem;
      }
      .nav-links.mobile-open .more-btn { display: none; }
      .hamburger { display: block; }
    }
  `;

  document.head.appendChild(style);
  document.body.prepend(nav);

  // Dropdown toggle
  const moreBtn = document.getElementById('more-btn');
  const dropdownMenu = document.getElementById('dropdown-menu');
  if (moreBtn && dropdownMenu) {
    moreBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdownMenu.classList.toggle('open');
    });
    document.addEventListener('click', () => {
      dropdownMenu.classList.remove('open');
    });
  }

  // Hamburger toggle
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.getElementById('nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      navLinks.classList.toggle('mobile-open');
    });
  }
})();