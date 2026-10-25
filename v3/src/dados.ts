// Dados da landing v3, lidos na hora do build das mesmas fontes dos outros dois layouts:
// o nav do mkdocs.yml (domínios, páginas, trilhas) e os .md de docs/ (versão, contagens).
// Nada de número escrito à mão: se entrar uma página ou um cenário novo, a landing acompanha.
import fs from 'node:fs';
import path from 'node:path';
import YAML from 'yaml';

const RAIZ = path.resolve(process.cwd(), '..');
const DOCS = path.join(RAIZ, 'docs');

/** As páginas de conteúdo ficam no layout 2 (Astro/Starlight), que tem o mesmo visual escuro. */
export const BASE_PAGINAS = '/help-ppl-cka/v2';
export const REPO = 'https://github.com/crisz-source/help-ppl-cka';

function falha(msg: string): never {
	throw new Error(`v3/dados: ${msg}`);
}

const lerDoc = (rel: string) => fs.readFileSync(path.join(DOCS, rel), 'utf8').replace(/\r\n/g, '\n');

/** docs/03-x/ingress.md → "03-x/ingress"; docs/03-x/index.md → "03-x" (mesma regra do sync do v2) */
const slugDe = (rel: string) => rel.replace(/\.md$/, '').replace(/(^|\/)index$/, '');
export const urlDe = (slug: string) => `${BASE_PAGINAS}/${slug}/`;

type EntradaNav = string | Record<string, string | EntradaNav[]>;
export type Pagina = { label: string; slug: string; grupo: string };
export type Dominio = { numero: number; nome: string; peso: number; indice: string; paginas: Pagina[] };

const cfg = YAML.parse(fs.readFileSync(path.join(RAIZ, 'mkdocs.yml'), 'utf8'), { logLevel: 'silent' });
const nav: EntradaNav[] = cfg.nav;

/** Todas as páginas do nav, na ordem do menu, com o grupo de origem (para a busca). */
function achatar(itens: EntradaNav[], grupo: string): Pagina[] {
	return itens.flatMap((item) => {
		if (typeof item === 'string') return [{ label: 'Visão geral', slug: slugDe(item), grupo }];
		const [label, valor] = Object.entries(item)[0];
		if (typeof valor === 'string') return [{ label, slug: slugDe(valor), grupo }];
		return achatar(valor, label);
	});
}

export const todasPaginas = achatar(nav, 'Início').filter((p) => p.slug !== '');

export const dominios: Dominio[] = nav
	.filter((e): e is Record<string, EntradaNav[]> => typeof e !== 'string' && /^\d/.test(Object.keys(e)[0]))
	.map((e) => {
		const [rotulo, itens] = Object.entries(e)[0];
		const m = rotulo.match(/^(\d+)\.\s*(.+?)\s*\((\d+)%\)$/) ?? falha(`rótulo de domínio fora do padrão: ${rotulo}`);
		const paginas = achatar(itens, rotulo);
		const indice = paginas.find((p) => p.label === 'Visão geral') ?? falha(`domínio sem index.md: ${rotulo}`);
		return {
			numero: Number(m[1]),
			nome: m[2],
			peso: Number(m[3]),
			indice: indice.slug,
			paginas: paginas.filter((p) => p !== indice),
		};
	});

export const totalTopicos = dominios.reduce((s, d) => s + d.paginas.length, 0);
export const maiorPeso = Math.max(...dominios.map((d) => d.peso));

// "Kubernetes nos laboratórios: **v1.37**" e "Currículo conferido em **outubro de 2026**" da home
const home = lerDoc('index.md');
export const versaoLab = home.match(/laboratórios: \*\*(v[\d.]+)\*\*/)?.[1] ?? falha('versão do lab não encontrada em docs/index.md');
const mesConferido = home.match(/Currículo conferido em \*\*(\w+) de (\d{4})\*\*/) ?? falha('data do currículo não encontrada em docs/index.md');
const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
const mes = MESES.indexOf(mesConferido[1]);
if (mes < 0) falha(`mês desconhecido em docs/index.md: ${mesConferido[1]}`);
/** "out/2026" */
export const conferidoEm = `${MESES[mes].slice(0, 3)}/${mesConferido[2]}`;

// passos da trilha "Começar do zero" ("## 1. ...") e cenários de troubleshooting ("1. **Sintoma:**")
export const passosIniciante = (lerDoc('trilhas/iniciante.md').match(/^## \d+\./gm) ?? []).length;
export const totalCenarios = fs
	.readdirSync(path.join(DOCS, 'trilhas', 'troubleshooting'))
	.filter((f) => f.endsWith('.md') && f !== 'index.md')
	.reduce((s, f) => s + (lerDoc(`trilhas/troubleshooting/${f}`).match(/^1\. \*\*Sintoma:\*\*/gm) ?? []).length, 0);
if (!passosIniciante || !totalCenarios) falha('contagem de passos ou cenários deu zero: o formato das trilhas mudou?');

/** Confere que um slug usado à mão na landing existe no nav (link quebrado falha o build). */
export function link(slug: string): string {
	if (!todasPaginas.some((p) => p.slug === slug)) falha(`página inexistente no nav do mkdocs.yml: ${slug}`);
	return urlDe(slug);
}
