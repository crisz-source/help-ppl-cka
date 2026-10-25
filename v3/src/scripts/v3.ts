// Interação da landing v3: busca de tópicos no menu (atalho "/"), menu do celular e botão "copiar".

type Item = { label: string; grupo: string; href: string };

const MAX_RESULTADOS = 8;

// sem acento e minúsculo, para "nó" achar "No NotReady" e "rotulo" achar "rótulo"
const normalizar = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

const indice: Item[] = JSON.parse(document.getElementById('indice-busca')?.textContent ?? '[]');
const campo = document.getElementById('busca') as HTMLInputElement | null;
const lista = document.getElementById('busca-lista') as HTMLUListElement | null;
let selecionado = -1;

/** Todas as palavras digitadas precisam aparecer no nome ou no grupo; nome que começa com o termo vem antes. */
function buscar(termo: string): Item[] {
	const palavras = normalizar(termo).split(/\s+/).filter(Boolean);
	if (palavras.length === 0) return [];
	return indice
		.map((item) => ({ item, texto: normalizar(`${item.label} ${item.grupo}`), nome: normalizar(item.label) }))
		.filter(({ texto }) => palavras.every((p) => texto.includes(p)))
		.sort((a, b) => Number(b.nome.startsWith(palavras[0])) - Number(a.nome.startsWith(palavras[0])))
		.slice(0, MAX_RESULTADOS)
		.map(({ item }) => item);
}

function mostrar(itens: Item[], termo: string) {
	if (!campo || !lista) return;
	lista.replaceChildren();
	selecionado = -1;
	if (!termo.trim()) {
		lista.hidden = true;
		campo.setAttribute('aria-expanded', 'false');
		return;
	}
	if (itens.length === 0) {
		const li = document.createElement('li');
		li.className = 'vazio';
		li.textContent = `Nada para "${termo}"`;
		lista.append(li);
	}
	itens.forEach((item, i) => {
		const li = document.createElement('li');
		li.role = 'option';
		li.id = `busca-op-${i}`;
		const a = document.createElement('a');
		a.href = item.href;
		const nome = document.createElement('strong');
		nome.textContent = item.label;
		const grupo = document.createElement('small');
		grupo.textContent = item.grupo;
		a.append(nome, grupo);
		li.append(a);
		lista.append(li);
	});
	lista.hidden = false;
	campo.setAttribute('aria-expanded', 'true');
}

function marcar(novo: number) {
	if (!lista || !campo) return;
	const opcoes = [...lista.querySelectorAll<HTMLLIElement>('[role="option"]')];
	if (opcoes.length === 0) return;
	selecionado = (novo + opcoes.length) % opcoes.length;
	opcoes.forEach((op, i) => op.setAttribute('aria-selected', String(i === selecionado)));
	campo.setAttribute('aria-activedescendant', opcoes[selecionado].id);
	opcoes[selecionado].scrollIntoView({ block: 'nearest' });
}

campo?.addEventListener('input', () => mostrar(buscar(campo.value), campo.value));

campo?.addEventListener('keydown', (e) => {
	if (e.key === 'ArrowDown') {
		e.preventDefault();
		marcar(selecionado + 1);
	} else if (e.key === 'ArrowUp') {
		e.preventDefault();
		marcar(selecionado - 1);
	} else if (e.key === 'Enter') {
		const alvo = lista?.querySelectorAll<HTMLAnchorElement>('[role="option"] a')[Math.max(selecionado, 0)];
		if (alvo) window.location.href = alvo.href;
	} else if (e.key === 'Escape') {
		campo.value = '';
		mostrar([], '');
		campo.blur();
	}
});

// fecha a lista ao sair da busca (o atraso deixa o clique no resultado acontecer antes)
campo?.addEventListener('blur', () => setTimeout(() => campo && mostrar([], document.activeElement === campo ? campo.value : ''), 150));

document.addEventListener('keydown', (e) => {
	const digitando = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;
	if (e.key === '/' && !digitando && !e.ctrlKey && !e.metaKey) {
		e.preventDefault();
		campo?.focus();
	}
});

// menu do celular
const botaoMenu = document.querySelector<HTMLButtonElement>('.menu-btn');
const menu = document.getElementById('menu-movel');

function abrirMenu(aberto: boolean) {
	if (!botaoMenu || !menu) return;
	menu.hidden = !aberto;
	botaoMenu.setAttribute('aria-expanded', String(aberto));
	botaoMenu.setAttribute('aria-label', aberto ? 'Fechar menu' : 'Abrir menu');
}

botaoMenu?.addEventListener('click', () => abrirMenu(menu?.hidden ?? false));
menu?.addEventListener('click', (e) => {
	if (e.target instanceof HTMLAnchorElement) abrirMenu(false);
});

// botão "copiar" do YAML de exemplo
document.querySelectorAll<HTMLButtonElement>('[data-copiar]').forEach((botao) => {
	botao.addEventListener('click', async () => {
		const texto = document.getElementById(botao.dataset.copiar!)?.textContent ?? '';
		try {
			await navigator.clipboard.writeText(texto);
			botao.textContent = 'copiado';
		} catch {
			botao.textContent = 'erro ao copiar';
		}
		setTimeout(() => (botao.textContent = 'copiar'), 1500);
	});
});
