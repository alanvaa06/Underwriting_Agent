/* Form handling, SSE consumption, UI state dispatch. */

(function () {
  const form = document.getElementById('applicant-form');
  const runBtn = document.getElementById('run-btn');
  const cancelBtn = document.getElementById('cancel-btn');
  const elapsedEl = document.getElementById('elapsed');
  const tabContent = document.getElementById('tab-content');
  const decisionCard = document.getElementById('decision-card');
  const decisionHeadline = document.getElementById('decision-headline');
  const riskScore = document.getElementById('risk-score');
  const decisionMemo = document.getElementById('decision-memo');
  const errorBanner = document.getElementById('error-banner');

  const agentOutputs = {};
  const currentState = { agent_outputs: agentOutputs, decision: null, risk_score: null, memo: null, cost: null };
  const tokenBuffer = {};
  let abortController = null;
  let elapsedTimer = null;
  let startTime = null;

  function $(name) {
    return form.querySelector(`[name="${name}"]`).value;
  }
  function $n(name) {
    const v = form.querySelector(`[name="${name}"]`).value;
    if (v === '') return null;
    const stripped = v.replace(/,/g, '');
    return stripped === '' ? null : Number(stripped);
  }

  function buildPayload() {
    return {
      api_key: $('api_key'),
      model: 'gpt-4o',
      applicant: {
        name: $('name'),
        credit_score: $n('credit_score'),
        credit_history: {
          bankruptcies: $n('bankruptcies') || 0,
          foreclosures: $n('foreclosures') || 0,
          late_payments_12mo: $n('late_payments_12mo') || 0,
          late_payments_24mo: $n('late_payments_24mo') || 0,
          oldest_tradeline_years: $n('oldest_tradeline_years') || 0,
          notes: $('credit_notes'),
        },
        employment: {
          employer: $('employer'),
          position: $('position'),
          years: $n('years'),
          monthly_income: $n('monthly_income'),
          type: $('emp_type'),
          notes: $('employment_notes'),
        },
        debts: {
          car_loan: $n('car_loan') || 0,
          student_loan: $n('student_loan') || 0,
          credit_cards: $n('credit_cards') || 0,
          other: $n('debt_other') || 0,
          notes: $('debts_notes'),
        },
        assets: {
          checking: $n('checking') || 0,
          savings: $n('savings') || 0,
          investments: $n('investments') || 0,
          retirement: $n('retirement') || 0,
          notes: $('assets_notes'),
        },
        property_info: {
          purchase_price: $n('purchase_price'),
          property_type: $('property_type'),
          occupancy: $('occupancy'),
          notes: $('property_notes'),
        },
        loan: {
          loan_amount: $n('loan_amount'),
          down_payment: $n('down_payment') || 0,
          term_years: $n('term_years') || 30,
        },
      },
    };
  }

  function recomputeDtiLtv() {
    const monthly = $n('monthly_income') || 0;
    const debts = ($n('car_loan')||0) + ($n('student_loan')||0) + ($n('credit_cards')||0) + ($n('debt_other')||0);
    document.getElementById('computed-dti').textContent =
      monthly > 0 ? (debts / monthly * 100).toFixed(1) + '%' : '—';

    const purchase = $n('purchase_price') || 0;
    const loan = $n('loan_amount') || 0;
    document.getElementById('computed-ltv').textContent =
      purchase > 0 ? (loan / purchase * 100).toFixed(1) + '%' : '—';
  }
  form.addEventListener('input', recomputeDtiLtv);
  form.addEventListener('input', (e) => {
    if (e.target.tagName === 'TEXTAREA' && e.target.name && e.target.name.endsWith('_notes')) {
      const counter = form.querySelector(`[data-counter="${e.target.name}"]`);
      if (counter) counter.textContent = `${e.target.value.length} / 2000`;
    }
  });

  // Tab switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  let activeTab = 'credit';
  function renderTab() {
    tabBtns.forEach(b => b.classList.toggle('active', b.dataset.tab === activeTab));
    const data = agentOutputs[activeTab];
    const tokens = tokenBuffer[activeTab];
    if (data) {
      tabContent.textContent = JSON.stringify(data, null, 2);
    } else if (tokens) {
      tabContent.textContent = tokens;
    } else {
      tabContent.textContent = 'No output yet.';
    }
  }
  tabBtns.forEach(b => b.addEventListener('click', () => { activeTab = b.dataset.tab; renderTab(); }));

  function setRunning(running) {
    runBtn.classList.toggle('hidden', running);
    cancelBtn.classList.toggle('hidden', !running);
    form.querySelectorAll('input, select').forEach(el => el.disabled = running);
  }

  function startElapsed() {
    startTime = Date.now();
    elapsedTimer = setInterval(() => {
      elapsedEl.textContent = ((Date.now() - startTime) / 1000).toFixed(1) + 's';
    }, 100);
  }
  function stopElapsed() {
    if (elapsedTimer) clearInterval(elapsedTimer);
    elapsedTimer = null;
  }

  function showError(codeOrMsg) {
    const t = (window.UnderwriterI18n && window.UnderwriterI18n.t) || (k => k);
    const key = 'error.' + codeOrMsg;
    const translated = t(key);
    errorBanner.textContent = translated !== key ? translated : codeOrMsg;
    errorBanner.classList.remove('hidden');
  }
  function hideError() {
    errorBanner.classList.add('hidden');
  }

  function showDecision(payload) {
    const d = payload.decision;
    decisionCard.classList.remove('hidden', 'decision-approved', 'decision-conditional', 'decision-denied');
    if (d === 'APPROVED') decisionCard.classList.add('decision-approved');
    else if (d === 'CONDITIONAL_APPROVAL') decisionCard.classList.add('decision-conditional');
    else decisionCard.classList.add('decision-denied');
    decisionHeadline.textContent = d.replace('_', ' ');
    riskScore.textContent = payload.risk_score ?? '—';
    decisionMemo.textContent = payload.memo ?? '';
  }

  function showCost(payload) {
    const card = document.getElementById('cost-breakdown');
    const tbody = document.querySelector('#cost-table tbody');
    if (!card || !tbody) return;
    tbody.innerHTML = '';
    const order = ['credit', 'income', 'asset', 'collateral', 'critic', 'decision'];
    for (const name of order) {
      const u = payload.per_agent[name];
      if (!u) continue;
      const row = document.createElement('tr');
      row.innerHTML = `
        <td class="py-0.5 text-clay-600 dark:text-clay-400">${name}</td>
        <td class="py-0.5 text-right">${u.input_tokens.toLocaleString()} in</td>
        <td class="py-0.5 text-right">${u.output_tokens.toLocaleString()} out</td>
        <td class="py-0.5 text-right">$${u.usd.toFixed(4)}</td>`;
      tbody.appendChild(row);
    }
    const total = document.createElement('tr');
    total.className = 'border-t border-clay-200 dark:border-clay-700 font-semibold';
    total.innerHTML = `
      <td class="pt-1 text-clay-700 dark:text-clay-200">Total</td>
      <td class="pt-1 text-right">${(payload.total_tokens || 0).toLocaleString()} tokens</td>
      <td></td>
      <td class="pt-1 text-right">$${payload.total_usd.toFixed(4)}</td>`;
    tbody.appendChild(total);
    card.classList.remove('hidden');
  }

  function reset() {
    Object.keys(agentOutputs).forEach(k => delete agentOutputs[k]);
    currentState.decision = null;
    currentState.risk_score = null;
    currentState.memo = null;
    currentState.cost = null;
    Object.keys(tokenBuffer).forEach(k => delete tokenBuffer[k]);
    const costCard = document.getElementById('cost-breakdown');
    if (costCard) costCard.classList.add('hidden');
    decisionCard.classList.add('hidden');
    hideError();
    elapsedEl.textContent = '0.0s';
    activeTab = 'credit';
    renderTab();
    if (window.UnderwriterGraph) window.UnderwriterGraph.reset();
  }

  async function consumeStream(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sep;
      while ((sep = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);

        let eventType = null;
        let data = null;
        for (const line of block.split('\n')) {
          if (line.startsWith('event: ')) eventType = line.slice(7);
          else if (line.startsWith('data: ')) data = line.slice(6);
        }
        if (!eventType || data === null) continue;

        let payload;
        try { payload = JSON.parse(data); } catch { continue; }
        const evt = { type: payload.type || eventType, payload: payload.payload || {}, ts: payload.ts };
        handleEvent(evt);
      }
    }
  }

  function handleEvent(evt) {
    if (evt.type === 'token' && evt.payload.agent) {
      const a = evt.payload.agent;
      tokenBuffer[a] = (tokenBuffer[a] || '') + evt.payload.token;
      if (activeTab === a) tabContent.textContent = tokenBuffer[a];
      return;
    }
    if (window.UnderwriterGraph) window.UnderwriterGraph.onEvent(evt);
    if (evt.type === 'agent_complete' && evt.payload.agent) {
      const a = evt.payload.agent;
      const key = a === 'critic' ? 'critic' : a;
      agentOutputs[key] = evt.payload.output;
      delete tokenBuffer[key];
      renderTab();
    } else if (evt.type === 'decision') {
      currentState.decision = evt.payload.decision;
      currentState.risk_score = evt.payload.risk_score;
      currentState.memo = evt.payload.memo;
      showDecision(evt.payload);
    } else if (evt.type === 'cost') {
      currentState.cost = evt.payload;
      showCost(evt.payload);
    } else if (evt.type === 'error') {
      showError(evt.payload.code || evt.payload.message || 'unknown');
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    reset();
    if (window.UnderwriterGraph) window.UnderwriterGraph.render();

    let payload;
    try {
      payload = buildPayload();
      if (!payload.api_key || !payload.api_key.startsWith('sk-')) {
        showError('invalid_key');
        return;
      }
    } catch (err) {
      showError('Invalid form: ' + err.message);
      return;
    }

    setRunning(true);
    startElapsed();
    abortController = new AbortController();

    try {
      const r = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: abortController.signal,
      });
      if (!r.ok) {
        const body = await r.text();
        showError(`HTTP ${r.status}: ${body.slice(0, 200)}`);
        return;
      }
      await consumeStream(r);
    } catch (err) {
      if (err.name === 'AbortError') {
        showError('cancelled');
      } else {
        showError('NETWORK');
      }
    } finally {
      setRunning(false);
      stopElapsed();
      abortController = null;
    }
  });

  cancelBtn.addEventListener('click', () => {
    if (abortController) abortController.abort();
  });

  document.getElementById('export-pdf-btn')?.addEventListener('click', () => {
    if (window.UnderwriterPDF) window.UnderwriterPDF.exportDecisionPDF(currentState);
  });

  // initial graph render
  if (window.UnderwriterGraph) window.UnderwriterGraph.render();
})();
