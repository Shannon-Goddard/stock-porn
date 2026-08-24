// blog-engine.js — renders trade articles from blog.json + trades.json
// Each page includes this and calls BlogEngine.renderList() or BlogEngine.renderArticle()

const BlogEngine = (() => {

  function fmt(val) {
    if (val === null || val === undefined) return '—';
    const abs = Math.abs(val).toFixed(2);
    return (val >= 0 ? '+$' : '-$') + abs;
  }

  function fmtTime(str) {
    if (!str) return '—';
    const match = str.match(/(\d{2}:\d{2}):\d{2}/);
    return match ? match[1] + ' ET' : str.split('T')[0];
  }

  function pnlClass(v) { return v > 0 ? 'pos' : v < 0 ? 'neg' : 'muted'; }

  function tag(type) {
    return `<span class="be-tag ${type.toLowerCase()}">${type}</span>`;
  }

  function section(title, content) {
    return `<div class="be-section">
      <div class="be-section-title">${title}</div>
      ${content}
    </div>`;
  }

  function row(label, value, cls='') {
    return `<div class="be-row">
      <span class="be-row-label">${label}</span>
      <span class="be-row-value ${cls}">${value}</span>
    </div>`;
  }

  function renderArticle(blog, trade) {
    if (!trade) return '<p class="be-empty">Trade data not found</p>';
    const e  = trade.entry;
    const ex = trade.exit;
    const f  = trade.fomo;
    const n  = trade.news_scan;
    const pnl = ex ? ex.pnl : null;
    const won = pnl !== null && pnl > 0;

    // ── 1. The Signal ────────────────────────────────────────────────────────
    const signalHtml = `
      <div class="be-grid">
        ${row('Ticker',       e.ticker)}
        ${row('Signal Rank',  e.signal_rank)}
        ${row('Day Change',   `${e.signal_pct > 0 ? '+' : ''}${e.signal_pct}% / ${fmt(e.signal_dollar)}`, pnlClass(e.signal_dollar))}
        ${row('Stock Price',  '$' + e.stock_price_at_entry)}
        ${row('Sector',       e.sector)}
        ${row('SPY Day',      `${e.spy_change >= 0 ? '+' : ''}${e.spy_change}%`, e.spy_change >= 0 ? 'pos' : 'neg')}
        ${row('Macro Active', e.macro_active ? e.macro_keywords.join(', ') : 'None', e.macro_active ? 'neg' : 'muted')}
      </div>
      <div class="be-note">${e.auto_note}</div>
    `;

    // ── 2. The Contract ──────────────────────────────────────────────────────
    const contractHtml = `
      <div class="be-grid">
        ${row('Type',       tag(e.type))}
        ${row('Strike',     '$' + e.strike)}
        ${row('Expiration', e.expiration + ' (' + e.dte_at_entry + 'DTE)')}
        ${row('Premium',    '$' + e.premium + ' per share')}
        ${row('Cost',       '$' + e.cost + ' per contract')}
        ${row('Bid/Ask',    e.bid + ' / ' + e.premium + ' (spread $' + e.spread + ')')}
        ${row('IV at Entry', (e.iv_at_entry * 100).toFixed(1) + '%')}
        ${row('OTM %',      e.otm_pct + '%', e.otm_pct > 10 ? 'neg' : 'muted')}
      </div>
      <div class="be-callout">
        <strong>Why this contract:</strong> ATM strike closest to ITM within $100 budget.
        ${e.otm_pct > 10
          ? `Note: ${e.otm_pct}% OTM — high-priced stock pushed contract away from the money to stay within budget. Higher OTM = lower delta = needs bigger move to profit.`
          : `${e.otm_pct}% OTM — near the money, delta close to 0.5, moves roughly $0.50 per $1 of stock move.`}
      </div>
    `;

    // ── 3. The Greeks ────────────────────────────────────────────────────────
    const greeksHtml = `
      <div class="be-callout">
        <strong>Black-Scholes inputs at entry:</strong><br>
        S = $${e.stock_price_at_entry} (stock price) &nbsp;·&nbsp;
        K = $${e.strike} (strike) &nbsp;·&nbsp;
        T = ${e.dte_at_entry}/365 = ${e.T_at_entry.toFixed(4)} years &nbsp;·&nbsp;
        r = 5% (risk-free) &nbsp;·&nbsp;
        σ = ${(e.iv_at_entry * 100).toFixed(1)}% (IV at entry)
      </div>
      <div class="be-callout" style="margin-top:0.5rem">
        <strong>Delta ≈ ${e.type === 'CALL' ? '+' : '-'}${e.otm_pct < 5 ? '0.50' : e.otm_pct < 15 ? '0.25' : '0.10'}:</strong>
        For every $1 the stock moves ${e.type === 'CALL' ? 'up' : 'down'},
        the option moves approximately that much.
        ${e.dte_at_entry <= 1
          ? 'With 0-1DTE, theta is burning premium fast — every minute costs money if the stock doesn\'t move.'
          : `With ${e.dte_at_entry}DTE, theta burn is moderate at open but accelerates toward expiration.`}
      </div>
    `;

    // ── 4. The News Scan ─────────────────────────────────────────────────────
    const newsHtml = n ? `
      <div class="be-grid">
        ${row('Scanned At',       n.scanned_at)}
        ${row('Gap Days',         n.gap_days + ' day(s)')}
        ${row('Ticker Sentiment', n.ticker_sentiment, n.ticker_sentiment === 'bullish' ? 'pos' : n.ticker_sentiment === 'bearish' ? 'neg' : 'muted')}
        ${row('SPY Sentiment',    n.spy_sentiment,    n.spy_sentiment   === 'bullish' ? 'pos' : n.spy_sentiment   === 'bearish' ? 'neg' : 'muted')}
        ${row('Keywords Found',   (n.keywords_found || []).join(', ') || 'none')}
        ${row('Decision',         n.decision.toUpperCase(), n.decision === 'hold' ? 'pos' : 'neg')}
        ${row('Reason',           n.decision_reason)}
      </div>
    ` : '<p class="be-empty">No news scan data — trade predates automated news scanning</p>';

    // ── 5. The Trade ─────────────────────────────────────────────────────────
    const tradeHtml = ex ? `
      <div class="be-grid">
        ${row('Stock Open',     '$' + ex.stock_open_price)}
        ${row('Option Value',   '$' + ex.sell_option_price + ' (BS estimate)')}
        ${row('Contract Value', '$' + ex.sell_contract_value)}
        ${row('Cost',           '$' + e.cost)}
        ${row('P&L',            fmt(pnl), pnlClass(pnl))}
        ${row('Trigger',        ex.sell_trigger === 'hold_2min' ? 'Hold 2min (news confirmed)' : 'Sell at Open (no confirmation)')}
        ${row('Exit Time',      fmtTime(ex.time))}
      </div>
    ` : '<p class="be-empty">Trade still open</p>';

    // ── 6. The FOMO ──────────────────────────────────────────────────────────
    let fomoHtml = '<p class="be-empty">No FOMO data yet</p>';
    if (f && f.best_case) {
      fomoHtml = `
        <div class="be-fomo-grid">
          <div class="be-fomo-cell">
            <div class="be-fomo-label">You Got</div>
            <div class="be-fomo-value ${pnlClass(pnl)}">${fmt(pnl)}</div>
            <div class="be-fomo-sub">sold at ${fmtTime(ex ? ex.time : null)}</div>
          </div>
          <div class="be-fomo-cell">
            <div class="be-fomo-label">Best Case</div>
            <div class="be-fomo-value ${pnlClass(f.best_case.pnl)}">${fmt(f.best_case.pnl)}</div>
            <div class="be-fomo-sub">${fmtTime(f.best_case.time)}</div>
          </div>
          <div class="be-fomo-cell">
            <div class="be-fomo-label">Worst Case</div>
            <div class="be-fomo-value ${pnlClass(f.worst_case.pnl)}">${fmt(f.worst_case.pnl)}</div>
            <div class="be-fomo-sub">${fmtTime(f.worst_case.time)}</div>
          </div>
        </div>
        <div class="be-grid" style="margin-top:0.75rem">
          ${row('Day High Stock', '$' + f.day_high.stock_price + ' at ' + fmtTime(f.day_high.time))}
          ${row('Day High Option (BS)', '$' + f.day_high.bs_contract_value + ' → ' + fmt(f.day_high.theoretical_pnl), pnlClass(f.day_high.theoretical_pnl))}
          ${row('Day Low Stock',  '$' + f.day_low.stock_price  + ' at ' + fmtTime(f.day_low.time))}
          ${row('Day Low Option (BS)',  '$' + f.day_low.bs_contract_value  + ' → ' + fmt(f.day_low.theoretical_pnl),  pnlClass(f.day_low.theoretical_pnl))}
          ${row('Theta Burn',     '$' + Math.abs(f.theta_burned_at_sell).toFixed(4) + ' at sell time', 'neg')}
        </div>
        ${f.theta_note ? `<div class="be-callout" style="margin-top:0.5rem">⊘ ${f.theta_note}</div>` : ''}
        <div class="be-callout" style="margin-top:0.5rem">
          <strong>What this means:</strong>
          You captured ${fmt(pnl)} by selling ${ex && ex.sell_trigger === 'hold_2min' ? '2 minutes after open' : 'at open'}.
          The best theoretical exit was ${fmt(f.best_case.pnl)} at ${fmtTime(f.best_case.time)}.
          ${f.best_case.pnl > (pnl || 0)
            ? `Holding longer would have added ${fmt(f.best_case.pnl - (pnl || 0))} — but required knowing the future.`
            : `Selling when you did was the right call — the position deteriorated after your exit.`}
        </div>
      `;
    }

    // ── 7. What We Learned ───────────────────────────────────────────────────
    const learnedHtml = `
      <div class="be-callout">
        ${won
          ? `✓ Signal fired correctly. ${e.signal_rank} on ${e.date} produced a ${fmt(pnl)} gain.
             ${e.macro_active ? `Macro context (${e.macro_keywords.join(', ')}) was active — noted for pattern tracking.` : 'No macro triggers active — clean signal environment.'}`
          : `✗ Signal did not produce a win this time. ${e.signal_rank} on ${e.date} resulted in ${fmt(pnl)}.
             ${e.otm_pct > 10 ? `Contract was ${e.otm_pct}% OTM — high-priced stock limited ATM access within $100 budget. This is a known constraint.` : ''}
             ${e.macro_active ? `Macro context (${e.macro_keywords.join(', ')}) was active — may have affected direction.` : ''}`}
        Every trade, win or loss, adds to the dataset. The methodology accuracy scores on the Stats page update automatically.
      </div>
    `;

    return `
      <div class="be-article">
        ${section('1. The Signal',    signalHtml)}
        ${section('2. The Contract',  contractHtml)}
        ${section('3. The Greeks',    greeksHtml)}
        ${section('4. The News Scan', newsHtml)}
        ${section('5. The Trade',     tradeHtml)}
        ${section('6. The FOMO',      fomoHtml)}
        ${section('7. What We Learned', learnedHtml)}
      </div>
    `;
  }

  function renderCard(blog, isExpanded, base) {
    const won = blog.won;
    const pnl = blog.pnl;
    const cardClass = won === true ? 'be-card win' : won === false ? 'be-card loss' : 'be-card open';
    return `
      <div class="${cardClass}" id="card-${blog.id}">
        <div class="be-card-header" onclick="BlogEngine.toggle(${blog.id})">
          <div class="be-card-left">
            <span class="be-card-ticker">${blog.ticker}</span>
            ${tag(blog.type)}
            <span class="be-card-date">${blog.date}</span>
          </div>
          <div class="be-card-right">
            ${pnl !== undefined && pnl !== null
              ? `<span class="be-card-pnl ${pnlClass(pnl)}">${fmt(pnl)}</span>`
              : '<span class="be-card-pnl muted">Open</span>'}
            <span class="be-card-chevron">${isExpanded ? '▲' : '▼'}</span>
          </div>
        </div>
        ${blog.subtitle ? `<div class="be-card-subtitle">${blog.subtitle}</div>` : ''}
        ${blog.youtube_id ? `
          <div class="be-video">
            <iframe src="https://www.youtube.com/embed/${blog.youtube_id}"
              frameborder="0" allowfullscreen loading="lazy"></iframe>
          </div>` : ''}
        <div class="be-article-wrap" id="article-${blog.id}" style="display:${isExpanded ? 'block' : 'none'}">
          <div id="article-content-${blog.id}">loading...</div>
        </div>
      </div>
    `;
  }

  // Public API
  let _blogs = [];
  let _trades = {};
  let _expanded = null;
  let _base = '../';

  async function init(base='../') {
    _base = base;
    const [bRes, tRes] = await Promise.all([
      fetch(base + 'data/blog.json?t='   + Date.now()),
      fetch(base + 'data/trades.json?t=' + Date.now())
    ]);
    _blogs  = await bRes.json();
    const td = await tRes.json();
    (td.trades || []).forEach(t => { _trades[t.id] = t; });
    return { blogs: _blogs, trades: _trades };
  }

  function toggle(id) {
    if (_expanded === id) {
      _expanded = null;
      document.getElementById('article-' + id).style.display = 'none';
      document.querySelector(`#card-${id} .be-card-chevron`).textContent = '▼';
    } else {
      // Collapse previous
      if (_expanded !== null) {
        const prev = document.getElementById('article-' + _expanded);
        if (prev) prev.style.display = 'none';
        const prevChev = document.querySelector(`#card-${_expanded} .be-card-chevron`);
        if (prevChev) prevChev.textContent = '▼';
      }
      _expanded = id;
      const wrap = document.getElementById('article-' + id);
      wrap.style.display = 'block';
      document.querySelector(`#card-${id} .be-card-chevron`).textContent = '▲';
      // Render article content on first expand
      const content = document.getElementById('article-content-' + id);
      const blog    = _blogs.find(b => b.id === id);
      const trade   = _trades[blog ? blog.trade_id : null];
      content.innerHTML = renderArticle(blog, trade);
    }
  }

  return { init, toggle, renderCard, renderArticle };
})();
