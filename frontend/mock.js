/* Mock data loader. Fetches bundled cases on init, button fills form with random pick. */

(function () {
  let cases = [];

  async function loadCases() {
    try {
      const r = await fetch('/api/cases');
      if (!r.ok) return;
      const data = await r.json();
      cases = data.cases || [];
    } catch (e) {
      console.warn('Failed to load mock cases:', e);
    }
  }

  function setField(name, value) {
    const el = document.querySelector(`[name="${name}"]`);
    if (!el) return;
    el.value = value == null ? '' : String(value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  function fillForm(applicant) {
    const ch = applicant.credit_history || {};
    const emp = applicant.employment || {};
    const debts = applicant.debts || {};
    const assets = applicant.assets || {};
    const prop = applicant.property_info || {};
    const loan = applicant.loan || {};

    setField('name', applicant.name);
    setField('credit_score', applicant.credit_score);
    setField('oldest_tradeline_years', ch.oldest_tradeline_years);
    setField('bankruptcies', ch.bankruptcies);
    setField('foreclosures', ch.foreclosures);
    setField('late_payments_12mo', ch.late_payments_12mo);
    setField('late_payments_24mo', ch.late_payments_24mo);
    setField('credit_notes', ch.notes || ch.credit_notes || '');

    setField('employer', emp.employer);
    setField('position', emp.position);
    setField('years', emp.years);
    setField('monthly_income', emp.monthly_income);
    setField('emp_type', emp.type || 'W2');
    setField('employment_notes', emp.notes || '');

    setField('car_loan', debts.car_loan);
    setField('student_loan', debts.student_loan);
    setField('credit_cards', debts.credit_cards);
    setField('debt_other', debts.other);
    setField('debts_notes', debts.notes || '');

    setField('checking', assets.checking);
    setField('savings', assets.savings);
    setField('investments', assets.investments);
    setField('retirement', assets.retirement);
    setField('assets_notes', assets.notes || '');

    setField('purchase_price', prop.purchase_price);
    setField('property_type', prop.property_type || 'single_family');
    setField('occupancy', prop.occupancy || 'primary');
    setField('property_notes', prop.notes || '');

    setField('down_payment', loan.down_payment);
    setField('loan_amount', loan.loan_amount);
    setField('term_years', loan.term_years || 30);
  }

  function loadRandom() {
    if (cases.length === 0) {
      alert('Sample cases not loaded yet. Try again in a moment.');
      return;
    }
    const pick = cases[Math.floor(Math.random() * cases.length)];
    if (pick && pick.applicant) fillForm(pick.applicant);
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadCases();
    const btn = document.getElementById('mock-btn');
    if (btn) btn.addEventListener('click', loadRandom);
  });

  window.UnderwriterMock = { loadRandom };
})();
