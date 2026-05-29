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
  classDef pending fill:#ece6df,stroke:#a89c8d,color:#3a342d
  classDef running fill:#f7e2c5,stroke:#c9802b,stroke-width:3px,color:#5a3308
  classDef done    fill:#d6e6cb,stroke:#5c8849,color:#2b4220
  classDef error   fill:#ecd2c8,stroke:#9a3a26,color:#4c1810
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
