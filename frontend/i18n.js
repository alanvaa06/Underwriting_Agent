/* EN/ES UI strings + applyLang + t() lookup. */

(function () {
  const STRINGS = {
    en: {
      'header.title': 'Underwriter Agent',
      'header.tagline': 'Multi-agent mortgage underwriting demo · LangGraph + GPT-4o',
      'header.github': 'View on GitHub →',
      'banner.demo': 'Demo only. Your OpenAI API key is sent per-request and never stored on the server. Synthetic test data only — do not enter real PII.',
      'fieldset.apikey': 'OpenAI API Key',
      'apikey.hint': 'Required. Used per-request, never stored.',
      'section.borrower': 'Borrower',
      'section.employment': 'Employment',
      'section.debts': 'Debts (monthly)',
      'section.assets': 'Assets',
      'section.property': 'Property & Loan',
      'field.name': 'Full name',
      'field.fico': 'FICO score',
      'field.oldest_tradeline': 'Oldest tradeline (yrs)',
      'field.bankruptcies': 'Bankruptcies',
      'field.foreclosures': 'Foreclosures',
      'field.late_12mo': 'Late payments (12mo)',
      'field.late_24mo': 'Late payments (24mo)',
      'field.employer': 'Employer',
      'field.position': 'Position',
      'field.years': 'Tenure (years)',
      'field.monthly_income': 'Monthly income ($)',
      'field.emp_type': 'Type',
      'field.car_loan': 'Car loan ($)',
      'field.student_loan': 'Student loan ($)',
      'field.credit_cards': 'Credit cards ($)',
      'field.debt_other': 'Other ($)',
      'field.checking': 'Checking ($)',
      'field.savings': 'Savings ($)',
      'field.investments': 'Investments ($)',
      'field.retirement': 'Retirement ($)',
      'field.purchase_price': 'Purchase price ($)',
      'field.down_payment': 'Down payment ($)',
      'field.loan_amount': 'Loan amount ($)',
      'field.term_years': 'Term (years)',
      'field.property_type': 'Property type',
      'field.occupancy': 'Occupancy',
      'field.notes': 'Notes',
      'compute.dti': 'Computed DTI:',
      'compute.ltv': 'Computed LTV:',
      'button.mock': '🎲 Load random sample',
      'button.run': 'Run Underwriting →',
      'button.cancel': 'Cancel',
      'button.download_pdf': 'Download memo (PDF)',
      'panel.workflow': 'Agent Workflow',
      'panel.elapsed': 'Elapsed:',
      'panel.waiting': 'Waiting for run...',
      'panel.outputs': 'Agent Outputs',
      'panel.no_output': 'No output yet.',
      'tab.credit': 'Credit',
      'tab.income': 'Income',
      'tab.asset': 'Asset',
      'tab.collateral': 'Collateral',
      'tab.critic': 'Critic',
      'risk.label': 'Risk:',
      'cost.title': 'Cost breakdown',
      'cost.total': 'Total',
      'error.invalid_key': 'Enter a valid OpenAI API key (starts with sk-).',
      'error.cancelled': 'Cancelled.',
      'error.OPENAI_AUTH': 'Invalid OpenAI key. Check your key + billing.',
      'error.OPENAI_RATE_LIMIT': 'OpenAI rate limit hit. Wait and retry.',
      'error.OPENAI_TIMEOUT': 'OpenAI request timed out.',
      'error.RAG_RETRIEVE': 'Policy retrieval failed. Agent proceeded without it.',
      'error.AGENT_PARSE': 'Agent returned invalid response.',
      'error.INTERNAL': 'Internal error. Check logs.',
      'error.NETWORK': 'Connection lost.',
      'ph.apikey': 'sk-...',
      'ph.credit_notes': "e.g., 'Late payment in March 2024 was due to a banking error, resolved.'",
      'ph.employment_notes': "e.g., 'Promotion to Senior Engineer effective Jan 2025, salary increased 18%.'",
      'ph.debts_notes': "e.g., 'Student loan in deferment until 2026; payment shown is post-deferment estimate.'",
      'ph.assets_notes': "e.g., 'Retirement balance includes vested employer match; vested as of 2024-12-31.'",
      'ph.property_notes': "e.g., 'Appraisal pending; purchase price reflects accepted offer 2025-02-10.'",
      'tip.apikey': 'Your sk-... key. Sent per-request, never stored.',
      'tip.name': "Borrower's full legal name.",
      'tip.fico': 'Credit score, 300–850. Higher is better.',
      'tip.oldest_tradeline': 'Years since oldest credit line opened.',
      'tip.bankruptcies': 'Filings in last 7 years.',
      'tip.foreclosures': 'Lost properties in last 7 years.',
      'tip.late_12mo': 'Payments 30+ days late, last 12 months.',
      'tip.late_24mo': 'Payments 30+ days late, last 24 months.',
      'tip.employer': 'Current employer name.',
      'tip.position': 'Current job title.',
      'tip.years': 'Years at current employer.',
      'tip.monthly_income': 'Gross monthly income before tax.',
      'tip.emp_type': 'W2 = salaried. 1099 = contractor.',
      'tip.car_loan': 'Monthly car payment.',
      'tip.student_loan': 'Monthly student loan payment.',
      'tip.credit_cards': 'Minimum monthly credit card payment.',
      'tip.debt_other': 'Other recurring monthly debt.',
      'tip.checking': 'Checking account balance.',
      'tip.savings': 'Savings account balance.',
      'tip.investments': 'Brokerage / non-retirement holdings.',
      'tip.retirement': '401k / IRA balance.',
      'tip.purchase_price': 'Home sale price.',
      'tip.down_payment': 'Cash paid upfront.',
      'tip.loan_amount': 'Mortgage principal requested.',
      'tip.term_years': 'Loan repayment duration. 30 most common.',
      'tip.property_type': 'Single family, condo, townhouse, multi-family.',
      'tip.occupancy': 'Primary = live in. Secondary = vacation. Investment = rent out.',
      'tip.notes': 'Free-text context for this section. The agent reads it alongside structured fields.',
    },
    es: {
      'header.title': 'Agente de Suscripción',
      'header.tagline': 'Demo de suscripción hipotecaria multi-agente · LangGraph + GPT-4o',
      'header.github': 'Ver en GitHub →',
      'banner.demo': 'Solo demo. Tu API key de OpenAI se envía por solicitud y nunca se guarda en el servidor. Datos sintéticos únicamente — no ingreses PII real.',
      'fieldset.apikey': 'API Key de OpenAI',
      'apikey.hint': 'Requerida. Usada por solicitud, nunca almacenada.',
      'section.borrower': 'Prestatario',
      'section.employment': 'Empleo',
      'section.debts': 'Deudas (mensuales)',
      'section.assets': 'Activos',
      'section.property': 'Propiedad y Préstamo',
      'field.name': 'Nombre completo',
      'field.fico': 'Puntaje FICO',
      'field.oldest_tradeline': 'Línea más antigua (años)',
      'field.bankruptcies': 'Bancarrotas',
      'field.foreclosures': 'Ejecuciones hipotecarias',
      'field.late_12mo': 'Pagos atrasados (12m)',
      'field.late_24mo': 'Pagos atrasados (24m)',
      'field.employer': 'Empleador',
      'field.position': 'Puesto',
      'field.years': 'Antigüedad (años)',
      'field.monthly_income': 'Ingreso mensual ($)',
      'field.emp_type': 'Tipo',
      'field.car_loan': 'Préstamo auto ($)',
      'field.student_loan': 'Préstamo estudiantil ($)',
      'field.credit_cards': 'Tarjetas de crédito ($)',
      'field.debt_other': 'Otros ($)',
      'field.checking': 'Cuenta corriente ($)',
      'field.savings': 'Ahorros ($)',
      'field.investments': 'Inversiones ($)',
      'field.retirement': 'Retiro ($)',
      'field.purchase_price': 'Precio de compra ($)',
      'field.down_payment': 'Enganche ($)',
      'field.loan_amount': 'Monto del préstamo ($)',
      'field.term_years': 'Plazo (años)',
      'field.property_type': 'Tipo de propiedad',
      'field.occupancy': 'Ocupación',
      'field.notes': 'Notas',
      'compute.dti': 'DTI calculado:',
      'compute.ltv': 'LTV calculado:',
      'button.mock': '🎲 Cargar muestra aleatoria',
      'button.run': 'Ejecutar Suscripción →',
      'button.cancel': 'Cancelar',
      'button.download_pdf': 'Descargar memo (PDF)',
      'panel.workflow': 'Flujo de Agentes',
      'panel.elapsed': 'Transcurrido:',
      'panel.waiting': 'Esperando ejecución...',
      'panel.outputs': 'Salida de Agentes',
      'panel.no_output': 'Aún sin salida.',
      'tab.credit': 'Crédito',
      'tab.income': 'Ingresos',
      'tab.asset': 'Activos',
      'tab.collateral': 'Garantía',
      'tab.critic': 'Crítico',
      'risk.label': 'Riesgo:',
      'cost.title': 'Desglose de costo',
      'cost.total': 'Total',
      'error.invalid_key': 'Ingresa una API key válida de OpenAI (empieza con sk-).',
      'error.cancelled': 'Cancelado.',
      'error.OPENAI_AUTH': 'API key inválida. Revisa tu key y facturación.',
      'error.OPENAI_RATE_LIMIT': 'Límite de OpenAI alcanzado. Espera y reintenta.',
      'error.OPENAI_TIMEOUT': 'Tiempo de espera de OpenAI agotado.',
      'error.RAG_RETRIEVE': 'Falló recuperación de política. Agente continuó sin ella.',
      'error.AGENT_PARSE': 'Agente devolvió respuesta inválida.',
      'error.INTERNAL': 'Error interno. Revisa logs.',
      'error.NETWORK': 'Conexión perdida.',
      'ph.apikey': 'sk-...',
      'ph.credit_notes': "ej., 'Pago atrasado en marzo 2024 fue por error bancario, resuelto.'",
      'ph.employment_notes': "ej., 'Promoción a Ingeniero Senior efectiva enero 2025, salario aumentó 18%.'",
      'ph.debts_notes': "ej., 'Préstamo estudiantil en pausa hasta 2026; el pago es estimación post-pausa.'",
      'ph.assets_notes': "ej., 'Balance de retiro incluye aportación patronal consolidada al 2024-12-31.'",
      'ph.property_notes': "ej., 'Avalúo pendiente; precio refleja oferta aceptada 2025-02-10.'",
      'tip.apikey': 'Tu key sk-... Enviada por solicitud, nunca almacenada.',
      'tip.name': 'Nombre legal completo del prestatario.',
      'tip.fico': 'Puntaje crediticio, 300–850. Mayor es mejor.',
      'tip.oldest_tradeline': 'Años desde que abrió la línea de crédito más antigua.',
      'tip.bankruptcies': 'Declaraciones en los últimos 7 años.',
      'tip.foreclosures': 'Propiedades perdidas en los últimos 7 años.',
      'tip.late_12mo': 'Pagos con 30+ días de atraso, últimos 12 meses.',
      'tip.late_24mo': 'Pagos con 30+ días de atraso, últimos 24 meses.',
      'tip.employer': 'Nombre del empleador actual.',
      'tip.position': 'Puesto actual.',
      'tip.years': 'Años en el empleador actual.',
      'tip.monthly_income': 'Ingreso bruto mensual antes de impuestos.',
      'tip.emp_type': 'W2 = asalariado. 1099 = contratista.',
      'tip.car_loan': 'Pago mensual del auto.',
      'tip.student_loan': 'Pago mensual del préstamo estudiantil.',
      'tip.credit_cards': 'Pago mensual mínimo de tarjetas.',
      'tip.debt_other': 'Otra deuda recurrente mensual.',
      'tip.checking': 'Saldo de cuenta corriente.',
      'tip.savings': 'Saldo de cuenta de ahorros.',
      'tip.investments': 'Inversiones / activos no-retiro.',
      'tip.retirement': 'Balance 401k / IRA.',
      'tip.purchase_price': 'Precio de venta del inmueble.',
      'tip.down_payment': 'Efectivo pagado por adelantado.',
      'tip.loan_amount': 'Principal hipotecario solicitado.',
      'tip.term_years': 'Duración del préstamo. 30 más común.',
      'tip.property_type': 'Casa unifamiliar, condo, townhouse, multi-familiar.',
      'tip.occupancy': 'Primaria = vivir en ella. Secundaria = vacaciones. Inversión = rentar.',
      'tip.notes': 'Contexto libre para esta sección. El agente lo lee junto a los campos estructurados.',
    },
  };

  let current = 'en';

  function t(key) {
    return (STRINGS[current] && STRINGS[current][key]) || STRINGS.en[key] || key;
  }

  function applyLang(lang) {
    current = lang in STRINGS ? lang : 'en';
    const table = STRINGS[current];
    document.documentElement.lang = current;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (table[key]) el.textContent = table[key];
    });
    document.querySelectorAll('[data-i18n-tip]').forEach(el => {
      const key = el.dataset.i18nTip;
      if (table[key]) el.dataset.tip = table[key];
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const key = el.dataset.i18nPh;
      if (table[key]) el.placeholder = table[key];
    });
    localStorage.setItem('uw-lang', current);
    document.querySelectorAll('[data-lang-btn]').forEach(btn => {
      btn.classList.toggle('font-bold', btn.dataset.langBtn === current);
      btn.classList.toggle('text-accent-600', btn.dataset.langBtn === current);
    });
  }

  function initial() {
    const saved = localStorage.getItem('uw-lang');
    if (saved === 'en' || saved === 'es') return saved;
    return (navigator.language || 'en').toLowerCase().startsWith('es') ? 'es' : 'en';
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-lang-btn]').forEach(btn => {
      btn.addEventListener('click', () => applyLang(btn.dataset.langBtn));
    });
    applyLang(initial());
  });

  window.UnderwriterI18n = { applyLang, t };
})();
