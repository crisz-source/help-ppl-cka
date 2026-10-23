// Renderiza os <pre class="mermaid"> gerados por scripts/sync-docs.mjs. O pacote só é baixado
// nas páginas que têm diagrama.
async function renderizar() {
	const blocos = document.querySelectorAll<HTMLElement>('pre.mermaid');
	if (blocos.length === 0) return;
	const { default: mermaid } = await import('mermaid');
	const escuro = document.documentElement.dataset.theme !== 'light';
	mermaid.initialize({
		startOnLoad: false,
		theme: escuro ? 'dark' : 'neutral', // temas padrão do Mermaid, sem cores próprias
	});
	await mermaid.run({ nodes: [...blocos] });
}

renderizar().catch((erro) => console.error('mermaid: falha ao renderizar diagrama', erro));
