/* Dark mode toggle. Persists to localStorage, respects prefers-color-scheme on first load. */

(function () {
  const root = document.documentElement;

  function apply(theme) {
    if (theme === 'dark') root.classList.add('dark');
    else root.classList.remove('dark');
    if (window.UnderwriterGraph && window.UnderwriterGraph.setTheme) {
      window.UnderwriterGraph.setTheme(theme);
    }
  }

  function initial() {
    const saved = localStorage.getItem('uw-theme');
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function toggle() {
    const current = root.classList.contains('dark') ? 'dark' : 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('uw-theme', next);
    apply(next);
  }

  apply(initial());

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('dark-toggle');
    if (btn) btn.addEventListener('click', toggle);
  });

  window.UnderwriterDark = { apply, toggle };
})();
