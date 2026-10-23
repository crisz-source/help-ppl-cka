// Terminal animado: os blocos de código de shell (bash, console...) que o Expressive Code
// desenha como janela de terminal passam a "rodar" quando aparecem na tela.
//   - linha de comando: é digitada letra a letra;
//   - comentário, linha em branco e saída (em ```console, tudo que não começa com "$ "): aparece de uma vez.
// Sem JavaScript ou com "reduzir movimento" ligado, o bloco fica estático, como no layout 1.

const MS_POR_LETRA = 22;
const MAX_MS_POR_LINHA = 1100;
const MAX_MS_POR_BLOCO = 7000;

type Passo = { linha: HTMLElement; tipo: 'comando' | 'saida'; letras: number };

const reduzirMovimento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function classificar(frame: HTMLElement): Passo[] {
	const pre = frame.querySelector('pre');
	const ehConsole = pre?.dataset.language === 'console' || pre?.dataset.language === 'shellsession';
	const linhas = [...frame.querySelectorAll<HTMLElement>('.ec-line')];
	let continuacao = false; // linha anterior terminou com "\" (comando quebrado em várias linhas)
	return linhas.map((linha) => {
		const texto = linha.querySelector('.code')?.textContent?.replace(/\n$/, '') ?? '';
		const t = texto.trim();
		let comando: boolean;
		if (ehConsole) comando = texto.startsWith('$ ') || continuacao;
		else comando = continuacao || (t !== '' && !t.startsWith('#'));
		continuacao = comando && t.endsWith('\\');
		if (ehConsole && !comando) linha.classList.add('term-saida'); // saída em cinza, comando em cor
		return { linha, tipo: comando ? 'comando' : 'saida', letras: texto.length };
	});
}

const esperar = (ms: number) => new Promise((ok) => setTimeout(ok, ms));

async function rodar(frame: HTMLElement) {
	if (frame.dataset.rodando === '1') return;
	frame.dataset.rodando = '1';
	const passos = classificar(frame);
	passos.forEach((p) => p.linha.classList.remove('visivel', 'digitando'));
	frame.classList.add('term-anim');

	const custo = (p: Passo) => (p.tipo === 'comando' ? Math.min(p.letras * MS_POR_LETRA, MAX_MS_POR_LINHA) + 150 : 70);
	const total = passos.reduce((s, p) => s + custo(p), 0);
	const escala = Math.min(1, MAX_MS_POR_BLOCO / total);

	for (const p of passos) {
		if (p.tipo === 'comando' && p.letras > 0) {
			const ms = Math.max(120, Math.min(p.letras * MS_POR_LETRA, MAX_MS_POR_LINHA) * escala);
			p.linha.style.setProperty('--letras', String(p.letras));
			p.linha.style.setProperty('--ms', `${ms}ms`);
			p.linha.classList.add('visivel', 'digitando');
			await esperar(ms + 150 * escala);
			p.linha.classList.remove('digitando');
		} else {
			p.linha.classList.add('visivel');
			await esperar(70 * escala);
		}
	}
	frame.classList.remove('term-anim');
	frame.dataset.rodando = '0';
}

function preparar(frame: HTMLElement) {
	classificar(frame); // marca as linhas de saída já no carregamento, mesmo sem animação
	const header = frame.querySelector('figcaption.header');
	if (!header || header.querySelector('.term-rodar')) return;
	const botao = document.createElement('button');
	botao.type = 'button';
	botao.className = 'term-rodar';
	botao.textContent = '↻ repetir'; // "▶" vira emoji colorido no Windows
	botao.title = 'Rodar a animação do terminal de novo';
	botao.addEventListener('click', () => rodar(frame));
	header.append(botao);
}

function iniciar() {
	const frames = [...document.querySelectorAll<HTMLElement>('.sl-markdown-content figure.frame.is-terminal')];
	frames.forEach(preparar);
	if (reduzirMovimento || !('IntersectionObserver' in window)) return;

	// esconde antes de entrar na tela, para a animação começar do zero; roda uma vez sozinho
	frames.forEach((f) => f.classList.add('term-anim'));
	const observador = new IntersectionObserver(
		(entradas) => {
			for (const e of entradas) {
				if (!e.isIntersecting) continue;
				observador.unobserve(e.target);
				rodar(e.target as HTMLElement);
			}
		},
		{ threshold: 0.35 },
	);
	frames.forEach((f) => observador.observe(f));
}

iniciar();
