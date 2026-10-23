// Renderiza os <pre class="mermaid"> gerados por scripts/sync-docs.mjs. O pacote só é baixado
// nas páginas que têm diagrama.
async function renderizar() {
	const blocos = document.querySelectorAll<HTMLElement>('pre.mermaid');
	if (blocos.length === 0) return;
	const { default: mermaid } = await import('mermaid');
	const escuro = document.documentElement.dataset.theme !== 'light';
	mermaid.initialize({
		startOnLoad: false,
		theme: 'base',
		fontFamily: 'JetBrains Mono, monospace',
		themeVariables: escuro
			? { primaryColor: '#0d2a1f', primaryTextColor: '#e6edf3', primaryBorderColor: '#3fd68f', lineColor: '#5eead4', secondaryColor: '#11233a', tertiaryColor: '#161b22', clusterBkg: '#0f1720', clusterBorder: '#30363d' }
			: { primaryColor: '#e8fbf1', primaryTextColor: '#0b1f17', primaryBorderColor: '#0f9d63', lineColor: '#0e7490', secondaryColor: '#e0f2fe', tertiaryColor: '#f6f8fa', clusterBkg: '#f6f8fa', clusterBorder: '#d0d7de' },
	});
	await mermaid.run({ nodes: [...blocos] });
}

renderizar().catch((erro) => console.error('mermaid: falha ao renderizar diagrama', erro));
