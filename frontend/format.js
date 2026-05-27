/* Money input formatter. Format on blur, unformat on focus. */

(function () {
  const fmt = new Intl.NumberFormat('en-US');

  function parse(raw) {
    if (raw === '' || raw == null) return null;
    const digits = String(raw).replace(/[^\d.-]/g, '');
    if (digits === '' || digits === '-') return null;
    const n = Number(digits);
    return Number.isFinite(n) ? n : null;
  }

  function formatBlur(e) {
    const n = parse(e.target.value);
    e.target.value = n == null ? '' : fmt.format(n);
  }

  function unformatFocus(e) {
    const n = parse(e.target.value);
    e.target.value = n == null ? '' : String(n);
  }

  function init() {
    document.querySelectorAll('input[data-format="money"]').forEach(el => {
      el.addEventListener('blur', formatBlur);
      el.addEventListener('focus', unformatFocus);
      if (el.value !== '') formatBlur({ target: el });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.UnderwriterFormat = { parse };
})();
