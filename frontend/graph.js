/* Mermaid-based workflow graph. Mutates classDef per agent event and re-renders. */

(function () {
  mermaid.initialize({ startOnLoad: false, theme: 'neutral', flowchart: { useMaxWidth: true } });

  const nodes = ['credit', 'income', 'asset', 'collateral', 'critic', 'decision'];
  const nodeState = Object.fromEntries(nodes.map(n => [n, 'pending']));

  function buildGraph() {
    const stateLines = nodes.map(n => `class ${n} ${nodeState[n]}`).join('\n');
    return `
flowchart TD
  init([Initialize]) --> sup{Supervisor}
  sup --> credit[Credit] --> sup
  sup --> income[Income] --> sup
  sup --> asset[Asset] --> sup
  sup --> collateral[Collateral] --> sup
  sup --> critic[Critic] --> decision[Decision] --> done([Done])
  classDef pending fill:#e5e7eb,stroke:#9ca3af,color:#374151
  classDef running fill:#fef3c7,stroke:#f59e0b,stroke-width:3px,color:#92400e
  classDef done    fill:#d1fae5,stroke:#10b981,color:#065f46
  classDef error   fill:#fee2e2,stroke:#ef4444,color:#991b1b
${stateLines}
`;
  }

  async function render() {
    const container = document.getElementById('graph-container');
    const id = 'graph-svg-' + Date.now();
    try {
      const { svg } = await mermaid.render(id, buildGraph());
      container.innerHTML = svg;
    } catch (e) {
      console.error('Mermaid render failed:', e);
    }
  }

  function reset() {
    nodes.forEach(n => nodeState[n] = 'pending');
    render();
  }

  function onEvent(evt) {
    if (evt.type === 'agent_start' && evt.payload.agent) {
      nodeState[evt.payload.agent] = 'running';
      render();
    } else if (evt.type === 'agent_complete' && evt.payload.agent) {
      nodeState[evt.payload.agent] = 'done';
      render();
    } else if (evt.type === 'error' && evt.payload.agent) {
      nodeState[evt.payload.agent] = 'error';
      render();
    }
  }

  function setTheme(theme) {
    mermaid.initialize({
      startOnLoad: false,
      theme: theme === 'dark' ? 'dark' : 'neutral',
      flowchart: { useMaxWidth: true },
    });
    render();
  }

  window.UnderwriterGraph = { render, reset, onEvent, setTheme };

  document.addEventListener('DOMContentLoaded', () => {
    const theme = document.documentElement.classList.contains('dark') ? 'dark' : 'neutral';
    setTheme(theme);
  });
})();
