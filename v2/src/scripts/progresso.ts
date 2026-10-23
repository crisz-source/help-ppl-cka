// Progresso de estudo: quais páginas foram marcadas como estudadas. Fica só neste navegador
// (localStorage); se o armazenamento estiver bloqueado, o site funciona igual, sem lembrar.
const CHAVE = 'cka-v2:estudadas';

export function lerEstudadas(): Set<string> {
	try {
		const bruto = localStorage.getItem(CHAVE);
		return new Set(bruto ? (JSON.parse(bruto) as string[]) : []);
	} catch {
		return new Set();
	}
}

function gravar(estudadas: Set<string>) {
	try {
		localStorage.setItem(CHAVE, JSON.stringify([...estudadas]));
	} catch {
		// armazenamento indisponível (aba anônima, bloqueio): a marcação vale só nesta visita
	}
}

function pintar(botao: HTMLButtonElement, marcada: boolean) {
	botao.setAttribute('aria-pressed', String(marcada));
	const rotulo = botao.querySelector('.rotulo');
	if (rotulo) rotulo.textContent = marcada ? 'estudada' : 'marcar como estudada';
}

function iniciar() {
	const estudadas = lerEstudadas();
	document.querySelectorAll<HTMLButtonElement>('button.estudei[data-pagina]').forEach((botao) => {
		const pagina = botao.dataset.pagina!;
		pintar(botao, estudadas.has(pagina));
		botao.addEventListener('click', () => {
			const atual = lerEstudadas();
			if (atual.has(pagina)) atual.delete(pagina);
			else atual.add(pagina);
			gravar(atual);
			pintar(botao, atual.has(pagina));
		});
	});
}

iniciar();
