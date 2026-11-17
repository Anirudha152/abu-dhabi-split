(() => {
  const inrFmt = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 });
  const aedFmt = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 });
  const rupees = (n) => '₹' + inrFmt.format(Math.round(n));
  const plain = (n) => inrFmt.format(Math.round(Math.abs(n)));
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const day = (d) => (d ? `${+d.slice(8, 10)} ${MONTHS[+d.slice(5, 7) - 1]}` : '—');
  const arrow = '<svg class="arrow" viewBox="0 0 14 10" aria-hidden="true"><path d="M0 5h12M8 1l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';

  const main = document.getElementById('main');
  let D, byId, filter = 'all';

  const name = (id) => byId[id].name;
  const link = (id) => `<a class="person-link" href="#${id}">${esc(name(id))}</a>`;
  const tag = (net) => {
    const r = Math.round(net);
    if (r === 0) return '<span class="tag even">EVEN</span>';
    return r < 0 ? `<span class="tag owes">OWES ${plain(r)}</span>` : `<span class="tag gets">GETS ${plain(r)}</span>`;
  };
  const amtClass = (n) => (n >= 20000 ? 'amt-xl' : n >= 5000 ? 'amt-l' : n >= 1000 ? 'amt-m' : 'amt-s');
  const payerText = (e, me) => (e.payer === 'card' ? 'forex card' : e.payer === me ? 'you paid' : `${name(e.payer)} paid`);
  const sorter = (a, b) => (a.date === b.date ? a.order - b.order : !a.date ? 1 : !b.date ? -1 : a.date < b.date ? -1 : 1);

  function nav(current) {
    document.getElementById('names').innerHTML = D.people
      .map((p) => `<li><a href="#${p.id}"${p.id === current ? ' aria-current="page"' : ''}>${esc(p.name).replace(' ', '&nbsp;')}</a></li>`)
      .join('');
  }

  // ---------------- dashboard ----------------
  function dashboard() {
    const groups = [];
    D.settlements.forEach((s) => {
      const g = groups.find((x) => x.from === s.from);
      g ? g.rows.push(s) : groups.push({ from: s.from, rows: [s] });
    });
    const settleRows = groups
      .map((g) =>
        g.rows
          .map((s, i) => `<tr class="${i === 0 ? 'first' : 'group-cont'}">
            <td class="from">${i === 0 ? link(s.from) : ''}</td>
            <td class="to">${arrow}${link(s.to)}</td>
            <td class="num ${amtClass(s.inr)}">${rupees(s.inr)}</td></tr>`)
          .join(''))
      .join('');

    const people = [...D.people].sort((a, b) => a.net - b.net);
    const balanceRows = people
      .map((p) => `<tr><td>${link(p.id)}</td><td class="num">${plain(p.spent)}</td><td class="num">${plain(p.paid)}</td><td class="num">${tag(p.net)}</td></tr>`)
      .join('');

    const exps = D.expenses.map((e) => ({ ...e, order: e.id })).sort(sorter);
    const entries = exps
      .map((e) => {
        const rate = e.aed != null ? `${aedFmt.format(e.aed)} AED at ₹${e.rate.toFixed(e.payer === 'card' ? 4 : 2)}` : 'Charged in INR';
        const shares = [...e.shares].sort((a, b) => b.inr - a.inr)
          .map((s) => `<tr><td>${link(s.person)}${s.note ? `<span class="sub">${esc(s.note)}</span>` : ''}</td><td class="num">${rupees(s.inr)}</td></tr>`)
          .join('');
        return `<details><summary><span class="e-date">${day(e.date)}</span>
          <span><span class="e-title">${esc(e.title)}</span><span class="sub">${esc(payerText(e))} · ${e.shares.length === 1 ? name(e.shares[0].person) : `${e.shares.length} people`}</span></span>
          <span class="e-amt">${rupees(e.inr)}</span></summary>
          <div class="e-body"><p class="meta">${esc(rate)}</p>
          <table><tbody>${shares}</tbody></table></div></details>`;
      })
      .join('');

    const c = D.card;
    main.innerHTML = `
      <section aria-labelledby="h-settle">
        <div class="sec-head"><h2 id="h-settle">Settle up</h2><p class="sec-note">${D.settlements.length} payments clear everything</p></div>
        <table class="settle"><thead><tr><th>Who pays</th><th>To</th><th class="num">Amount</th></tr></thead><tbody>${settleRows}</tbody></table>
      </section>

      <section aria-labelledby="h-bal">
        <div class="sec-head"><h2 id="h-bal">Everyone’s balance</h2><p class="sec-note">Tap a name to see every line</p></div>
        <table><thead><tr><th>Name</th><th class="num">Spent</th><th class="num">Paid in</th><th class="num">Balance</th></tr></thead>
        <tbody>${balanceRows}</tbody>
        <tfoot><tr><td><b>Trip total</b></td><td class="num"><b>${plain(D.totalSpent)}</b></td><td class="num"><b>${plain(D.totalSpent)}</b></td><td></td></tr></tfoot></table>
      </section>

      <section aria-labelledby="h-rates">
        <div class="sec-head"><h2 id="h-rates">How dirhams became rupees</h2></div>
        <dl class="rates">
          <div><dt>Forex card<span class="sub">₹${inrFmt.format(c.loadedINR)} loaded − ₹${inrFmt.format(c.withdrawnINR)} cashed out, over ${aedFmt.format(c.spentAED)} AED spent. Ani loaded ₹${inrFmt.format(c.ani)}, ${esc(name('bhatnagar'))} ₹${inrFmt.format(c.bhatnagar)}.</span></dt><dd>₹${D.rates.card.toFixed(4)}</dd></div>
          <div><dt>Nitye’s cash, Gaurish’s go-karting<span class="sub">No rate given, so the agreed default</span></dt><dd>₹${D.rates.cash.toFixed(2)}</dd></div>
          <div><dt>${esc(name('baid'))}’s payments in AED</dt><dd>₹${D.rates.baid.toFixed(2)}</dd></div>
          <div><dt>Card charges billed in INR<span class="sub">Warner Bros. World, both Dubai taxis paid by card, the Delhi airport taxi</span></dt><dd>actual ₹</dd></div>
        </dl>
      </section>

      <section aria-labelledby="h-all">
        <div class="sec-head"><h2 id="h-all">Every expense</h2><p class="sec-note">${D.expenses.length} entries · tap one for the split</p></div>
        <div class="entries">${entries}</div>
      </section>`;
  }

  // ---------------- one passbook ----------------
  function passbook(id) {
    const me = byId[id];
    const r = Math.round(me.net);
    const kind = r === 0 ? 'even' : r < 0 ? 'owes' : 'gets';

    const out = D.settlements.filter((s) => s.from === id);
    const inn = D.settlements.filter((s) => s.to === id);
    const todo = out.length
      ? out.map((s) => `<p class="todo-line"><span>Pay <a href="#${s.to}">${esc(name(s.to))}</a></span><span class="num">${rupees(s.inr)}</span></p>`).join('')
      : inn.map((s) => `<p class="todo-line"><span>Collect from <a href="#${s.from}">${esc(name(s.from))}</a></span><span class="num">${rupees(s.inr)}</span></p>`).join('');

    // passbook rows: shares are withdrawals (Dr), money put in is a deposit (Cr)
    const rows = [];
    D.expenses.forEach((e) => {
      e.shares.forEach((s) => {
        if (s.person !== id) return;
        const n = e.shares.length;
        const equal = e.shares.every((x) => Math.abs(x.inr - e.shares[0].inr) < 0.01);
        const how = s.note || (n === 1 ? '' : equal ? `split ${n} ways` : `your part of ${rupees(e.inr)}`);
        const aed = s.aed != null ? `${aedFmt.format(s.aed)} AED` : '';
        rows.push({ date: e.date, order: e.id + 0.5, type: 'spent', title: e.title, sub: [how, aed, payerText(e, id)].filter(Boolean).join(' · '), dr: s.inr, cr: 0 });
      });
    });
    D.payments.forEach((p) => {
      if (p.person !== id) return;
      const e = p.expense ? D.expenses.find((x) => x.id === p.expense) : null;
      const title = p.kind === 'expense' ? `Paid: ${p.title}` : p.title;
      const sub = e ? `the whole bill, shared by ${e.shares.length === 1 ? name(e.shares[0].person) : e.shares.length + ' people'}` : p.kind === 'transfer' ? (p.inr < 0 ? 'cash received, counts against what you put in' : 'cash, settled already') : p.inr < 0 ? 'counts against what you put in' : 'forex card';
      const order = p.kind === 'card' && p.date ? 0 : e ? e.id : 9999;
      rows.push({ date: p.date, order, type: 'paid', title, sub, dr: 0, cr: p.inr });
    });
    rows.sort(sorter);
    let bal = 0;
    rows.forEach((x) => { bal += x.cr - x.dr; x.bal = bal; });

    const shown = rows.filter((x) => filter === 'all' || x.type === filter);
    const showBal = filter === 'all';
    const recd = (x) => (x.cr < 0 ? '<span class="side">recd</span>' : '');
    const side = (b) => (Math.round(b) < 0 ? 'Dr' : 'Cr');
    const balCell = (b) => `<td class="num bal both">${plain(b)}<span class="side">${side(b)}</span></td>`;
    const balSub = (b) => (showBal ? `<span class="sub bal-sub">bal ${plain(b)} ${side(b)}</span>` : '');
    const body = shown.length
      ? shown.map((x) => `<tr>
          <td class="date">${day(x.date)}</td>
          <td>${esc(x.title)}${x.sub ? `<span class="sub">${esc(x.sub)}</span>` : ''}</td>
          <td class="num amt one ${x.dr ? 'dr' : 'cr'}">${x.dr ? '−' + plain(x.dr) : (x.cr < 0 ? '−' : '+') + plain(x.cr) + recd(x)}${balSub(x.bal)}</td>
          <td class="num amt both dr">${x.dr ? plain(x.dr) : ''}</td>
          <td class="num amt both cr">${x.cr ? (x.cr < 0 ? '−' : '') + plain(x.cr) + recd(x) : ''}</td>
          ${showBal ? balCell(x.bal) : ''}</tr>`).join('')
      : `<tr class="empty-row"><td colspan="6">Nothing here. ${esc(me.name)} didn’t pay for anything directly.</td></tr>`;
    const totDr = shown.reduce((a, x) => a + x.dr, 0), totCr = shown.reduce((a, x) => a + x.cr, 0);

    const btn = (k, label) => `<button type="button" data-filter="${k}" aria-pressed="${filter === k}">${label}</button>`;
    main.innerHTML = `
      <div class="account">
        <div class="acct-row">
          <div>
            <h1 class="acct-name">${esc(me.name)}</h1>
            <p class="acct-sum">Spent <b>${rupees(me.spent)}</b><br>Paid in <b>${rupees(me.paid)}</b></p>
          </div>
          <div class="stamp ${kind} land" role="img" aria-label="${kind === 'even' ? 'All square' : (kind === 'owes' ? 'Owes ' : 'Gets back ') + rupees(r)}">
            <span class="s-word">${kind === 'even' ? 'Settled' : kind === 'owes' ? 'Owes' : 'Gets back'}</span>
            ${kind === 'even' ? '' : `<span class="s-amt"><span class="r">₹</span>${plain(r)}</span>`}
          </div>
        </div>
        ${todo ? `<div class="todo">${todo}</div>` : '<p class="todo-none">Nothing to pay or collect.</p>'}
      </div>

      <section aria-labelledby="h-book">
        <div class="sec-head"><h2 id="h-book">Passbook</h2>
          <div class="filters" role="group" aria-label="Show">${btn('all', 'All')}${btn('spent', 'Spent')}${btn('paid', 'Paid in')}</div></div>
        <table class="book">
          <thead><tr><th class="date">Date</th><th>Particulars</th>
            <th class="num one">Amount</th><th class="num both">Spent</th><th class="num both">Paid in</th>${showBal ? '<th class="num both">Balance</th>' : ''}</tr></thead>
          <tbody>${body}</tbody>
          <tfoot><tr><td></td><td>${showBal ? 'Closing balance' : 'Total'}</td>
            <td class="num one">${showBal ? `${plain(bal)} ${side(bal)}` : filter === 'spent' ? '−' + plain(totDr) : (totCr - totDr >= 0 ? '+' : '−') + plain(totCr - totDr)}</td>
            <td class="num both">${plain(totDr)}</td><td class="num both">${plain(totCr)}</td>${showBal ? balCell(bal) : ''}</tr></tfoot>
        </table>
        <a class="back" href="#"><span class="back-arrow">${arrow}</span>Everyone</a>
      </section>`;

    main.querySelectorAll('[data-filter]').forEach((b) =>
      b.addEventListener('click', () => {
        filter = b.dataset.filter;
        passbook(id);
        main.querySelector('.stamp').classList.remove('land');
      }));
  }

  function route() {
    const id = decodeURIComponent(location.hash.slice(1));
    nav(byId[id] ? id : null);
    filter = 'all';
    if (byId[id]) {
      passbook(id);
      document.title = `${byId[id].name} · Trip Passbook`;
    } else {
      dashboard();
      document.title = 'Trip Passbook';
    }
  }

  fetch('data.json')
    .then((r) => r.json())
    .then((data) => {
      D = data;
      byId = Object.fromEntries(D.people.map((p) => [p.id, p]));
      document.getElementById('cover-meta').textContent = `${D.trip.name} · ${D.trip.dates}`;
      document.getElementById('foot').innerHTML = `
        <p>Amounts are rounded to the nearest rupee, so nobody is off by more than ₹1. Every split adds back up to its bill, the forex card reconciles to the fils, and money spent equals money paid in: ${rupees(D.totalSpent)}.</p>
        <p>Spot a mistake? Tell Ani and the page gets regenerated from the ledger.</p>`;
      route();
      window.addEventListener('hashchange', () => {
        route();
        window.scrollTo({ top: 0 });
        main.focus({ preventScroll: true });
      });
    })
    .catch(() => { main.innerHTML = '<p class="loading">Couldn’t load the passbooks. Refresh the page to try again.</p>'; });
})();
