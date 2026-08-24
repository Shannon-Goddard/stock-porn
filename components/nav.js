(() => {
  // Detect depth from root: pages/ = '../', root = ''
  const path = window.location.pathname;
  const base = path.includes('/pages/') ? '../' : '';

  const links = [
    { label: 'Home',        href: `${base}index.html` },
    { label: 'Paper Trade', href: `${base}pages/paper-trade.html` },
    { label: 'Ledger',      href: `${base}pages/ledger.html` },
    { label: 'Stats',       href: `${base}pages/stats.html` },
    { label: 'Blog',        href: `${base}pages/blog.html` },
    { label: 'Methodology', href: `${base}pages/methodology.html` },
    null, // divider
    { label: '⌥ GitHub',   href: 'https://github.com/Shannon-Goddard/stock-porn', external: true },
    { label: '⌥ Legal',    href: `${base}pages/legal.html` },
    { label: '🍺 Buy Dev a Beer', href: 'https://buymeacoffee.com/goddardshannon9', external: true },
  ];

  const css = `
    #sp-nav {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid #2a2a2a;
      background: #0d0d0d;
      font-family: 'Courier New', Courier, monospace;
    }
    #sp-nav .nav-brand {
      color: #00c853;
      font-size: 1rem;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      text-decoration: none;
    }
    #sp-nav .nav-brand span {
      color: #666;
      font-size: 0.7rem;
      margin-left: 0.5rem;
    }
    #sp-hamburger {
      background: none;
      border: 1px solid #2a2a2a;
      color: #e8e8e8;
      font-size: 1.1rem;
      padding: 0.3rem 0.6rem;
      cursor: pointer;
      border-radius: 3px;
      font-family: 'Courier New', monospace;
      line-height: 1;
    }
    #sp-hamburger:hover { border-color: #00c853; color: #00c853; }
    #sp-menu {
      display: none;
      position: absolute;
      top: 100%;
      right: 0;
      min-width: 220px;
      background: #141414;
      border: 1px solid #2a2a2a;
      border-top: none;
      z-index: 999;
    }
    #sp-menu.open { display: block; }
    #sp-menu a {
      display: block;
      padding: 0.65rem 1rem;
      color: #e8e8e8;
      text-decoration: none;
      font-size: 0.82rem;
      border-bottom: 1px solid #1a1a1a;
      transition: background 0.15s, color 0.15s;
    }
    #sp-menu a:hover { background: #1a1a1a; color: #00c853; }
    #sp-menu a.active { color: #00c853; }
    #sp-menu .nav-divider {
      border-bottom: 1px solid #2a2a2a;
      margin: 0.25rem 0;
    }
    #sp-menu a.external { color: #666; }
    #sp-menu a.external:hover { color: #00c853; }
  `;

  // Inject styles
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  // Build HTML
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';

  const menuItems = links.map(link => {
    if (!link) return `<div class="nav-divider"></div>`;
    const active = currentPage === link.href.split('/').pop() ? ' active' : '';
    const ext = link.external ? ' external' : '';
    const target = link.external ? ' target="_blank" rel="noopener"' : '';
    return `<a href="${link.href}"${target} class="${(active + ext).trim()}">${link.label}</a>`;
  }).join('');

  const html = `
    <a class="nav-brand" href="${base}index.html">
      stock-porn<span>▸ signals</span>
    </a>
    <button id="sp-hamburger" aria-label="Menu" aria-expanded="false">☰</button>
    <nav id="sp-menu">${menuItems}</nav>
  `;

  const root = document.getElementById('nav-root');
  root.id = 'sp-nav';
  root.innerHTML = html;

  // Toggle
  const btn = document.getElementById('sp-hamburger');
  const menu = document.getElementById('sp-menu');
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const open = menu.classList.toggle('open');
    btn.setAttribute('aria-expanded', open);
  });
  document.addEventListener('click', () => {
    menu.classList.remove('open');
    btn.setAttribute('aria-expanded', false);
  });
})();
