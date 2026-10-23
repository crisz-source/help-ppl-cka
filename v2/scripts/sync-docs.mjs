// Copia ../docs (fonte única do conteúdo) para src/content/docs, convertendo o que é
// sintaxe do MkDocs Material para o que o Starlight entende. Também gera o menu lateral
// a partir do nav do mkdocs.yml, para os dois layouts terem o mesmo índice.
//
// Uso: node scripts/sync-docs.mjs   (roda sozinho antes de `npm run dev` e `npm run build`)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import YAML from 'yaml';

const V2 = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const RAIZ = path.resolve(V2, '..');
const DOCS = path.join(RAIZ, 'docs');
const SAIDA = path.join(V2, 'src', 'content', 'docs');
const GERADO = path.join(V2, 'src', 'generated');
export const BASE = '/help-ppl-cka/v2';

// tipos de aviso do Material → asides do Starlight (note, tip, caution, danger)
const ASIDE = { note: 'note', info: 'note', abstract: 'note', tip: 'tip', success: 'tip', question: 'note',
  warning: 'caution', failure: 'danger', danger: 'danger', bug: 'danger', example: 'note', quote: 'note' };

function falha(msg) {
  console.error(`sync-docs: ${msg}`);
  process.exit(1);
}

function listarMd(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) return listarMd(p);
    return e.name.endsWith('.md') ? [p] : [];
  });
}

/** docs/03-x/ingress.md → "03-x/ingress"; docs/03-x/index.md → "03-x"; docs/index.md → "" */
function slugDe(relMd) {
  const semExt = relMd.replace(/\\/g, '/').replace(/\.md$/, '');
  if (semExt === 'index') return '';
  return semExt.replace(/\/index$/, '');
}

const rota = (slug) => (slug ? `${BASE}/${slug}/` : `${BASE}/`);

const escaparHtml = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** Blocos "!!! tipo "Título"" e "??? tipo "Título"" (corpo indentado 4 espaços). */
function converterAvisos(linhas, arquivo) {
  const out = [];
  for (let i = 0; i < linhas.length; i++) {
    const m = linhas[i].match(/^( *)(!!!|\?\?\?\+?) +([a-z]+)(?: +"(.*)")? *$/);
    if (!m) {
      out.push(linhas[i]);
      continue;
    }
    const [, ind, marca, tipo, titulo] = m;
    const corpoInd = ind + '    ';
    const corpo = [];
    while (i + 1 < linhas.length && (linhas[i + 1].startsWith(corpoInd) || linhas[i + 1].trim() === '')) {
      corpo.push(linhas[++i]);
    }
    while (corpo.length && corpo.at(-1).trim() === '') corpo.pop(); // linha em branco final pertence ao texto seguinte
    const corpoConv = converterAvisos(corpo.map((l) => l.slice(corpoInd.length)), arquivo).map((l) => (l ? ind + l : l));
    if (marca === '!!!') {
      const t = ASIDE[tipo] ?? falha(`${arquivo}: tipo de aviso desconhecido "${tipo}"`);
      out.push(`${ind}:::${t}${titulo ? `[${titulo}]` : ''}`, ...corpoConv, `${ind}:::`, '');
    } else {
      const aberto = marca.endsWith('+') ? ' open' : '';
      out.push(`${ind}<details class="recolhivel ${tipo}"${aberto}>`, `${ind}<summary>${escaparHtml(titulo ?? tipo)}</summary>`, '',
        ...corpoConv, '', `${ind}</details>`, '');
    }
  }
  return out;
}

/** ```mermaid vira <pre class="mermaid"> (renderizado no navegador por src/scripts/mermaid.ts). */
function converterMermaid(texto) {
  return texto.replace(/^```mermaid\n([\s\S]*?)^```$/gm, (_, codigo) => `<pre class="mermaid">${escaparHtml(codigo.trimEnd())}</pre>`);
}

/** Links relativos para .md viram rotas absolutas do v2. Links externos e âncoras ficam como estão. */
function converterLinks(texto, relMd, slugsExistentes, arquivo) {
  const dir = path.posix.dirname(relMd.replace(/\\/g, '/'));
  return texto.replace(/\]\(([^)\s]+?\.md)(#[^)\s]*)?\)/g, (todo, alvo, ancora = '') => {
    if (/^[a-z]+:\/\//i.test(alvo)) return todo;
    const relAlvo = path.posix.normalize(path.posix.join(dir, alvo));
    const slug = slugDe(relAlvo);
    if (!slugsExistentes.has(slug)) falha(`${arquivo}: link para página inexistente "${alvo}"`);
    return `](${rota(slug)}${ancora})`;
  });
}

function converterPagina(fonte, relMd, slugsExistentes) {
  const arquivo = `docs/${relMd.replace(/\\/g, '/')}`;
  const texto = fonte.replace(/\r\n/g, '\n');
  const h1 = texto.match(/^# (.+)$/m) ?? falha(`${arquivo}: página sem título "# ..."`);
  let corpo = texto.replace(h1[0] + '\n', '');
  corpo = converterAvisos(corpo.split('\n'), arquivo).join('\n');
  corpo = converterMermaid(corpo);
  corpo = converterLinks(corpo, relMd, slugsExistentes, arquivo);
  return { titulo: h1[1].trim(), corpo };
}

/** nav do mkdocs.yml → sidebar do Starlight + lista de domínios (para os cards da página inicial). */
function lerNav() {
  // logLevel silent: a tag !!python/name do pymdownx não importa aqui
  const cfg = YAML.parse(fs.readFileSync(path.join(RAIZ, 'mkdocs.yml'), 'utf8'), { logLevel: 'silent' });
  const item = (entrada) => {
    if (typeof entrada === 'string') return { label: 'Visão geral', slug: slugDe(entrada) };
    const [label, valor] = Object.entries(entrada)[0];
    if (typeof valor === 'string') return slugDe(valor) ? { label, slug: slugDe(valor) } : { label, link: '/' };
    return { label, collapsed: false, items: valor.map(item) };
  };
  const sidebar = cfg.nav.map(item);
  const dominios = sidebar.filter((g) => g.items).map((g) => {
    const m = g.label.match(/^(\d+)\.\s*(.+?)\s*\((\d+)%\)$/) ?? falha(`mkdocs.yml: rótulo de domínio fora do padrão "N. Nome (P%)": ${g.label}`);
    const paginas = g.items.filter((i) => i.slug && i.label !== 'Visão geral').map((i) => ({ label: i.label, slug: i.slug }));
    return { numero: Number(m[1]), nome: m[2], peso: Number(m[3]), indice: g.items.find((i) => i.label === 'Visão geral')?.slug, paginas };
  });
  return { sidebar, dominios };
}

/** Tabela de domínios de docs/index.md: todos os domínios do currículo, inclusive os que ainda não têm página. */
function lerDominiosDaHome(dominiosNav) {
  const home = fs.readFileSync(path.join(DOCS, 'index.md'), 'utf8');
  const linhas = [...home.matchAll(/^\| *(\d) *\| *(.+?) *\| *(\d+)% *\|$/gm)];
  if (linhas.length === 0) falha('docs/index.md: tabela de domínios não encontrada');
  return linhas.map(([, n, nomeCel, peso]) => {
    const nome = nomeCel.replace(/^\[(.+)\]\(.+\)$/, '$1');
    const nav = dominiosNav.find((d) => d.numero === Number(n));
    return { numero: Number(n), nome, peso: Number(peso), indice: nav?.indice ?? null, paginas: nav?.paginas ?? [] };
  });
}

function main() {
  const arquivos = listarMd(DOCS).map((p) => path.relative(DOCS, p));
  const slugs = new Set(arquivos.map(slugDe));
  fs.rmSync(SAIDA, { recursive: true, force: true });
  fs.mkdirSync(GERADO, { recursive: true });

  for (const rel of arquivos) {
    const { titulo, corpo } = converterPagina(fs.readFileSync(path.join(DOCS, rel), 'utf8'), rel, slugs);
    const ehHome = slugDe(rel) === '';
    const fm = ehHome
      ? { title: titulo, template: 'splash', hero: { title: titulo, tagline: 'Preparação para a CKA em português, do jeito que a prova cobra: comando, YAML e pegadinha.' } }
      : { title: titulo };
    const destino = path.join(SAIDA, rel);
    fs.mkdirSync(path.dirname(destino), { recursive: true });
    fs.writeFileSync(destino, `---\n${YAML.stringify(fm)}---\n${corpo}`);
  }

  const { sidebar, dominios } = lerNav();
  const todosDominios = lerDominiosDaHome(dominios);
  fs.writeFileSync(path.join(GERADO, 'nav.json'), JSON.stringify({ sidebar, dominios: todosDominios }, null, 2));
  console.log(`sync-docs: ${arquivos.length} páginas, ${todosDominios.length} domínios (${dominios.length} com conteúdo)`);
}

main();
