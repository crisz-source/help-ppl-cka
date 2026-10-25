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
const ASSETS_DOCS = path.join(DOCS, 'assets');
const ASSETS_PUBLIC = path.join(V2, 'public', 'assets'); // public/ é servido como está, sem passar pelo Astro
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

/** Imagens e links relativos para docs/assets (![alt](../assets/x.svg), [texto](../assets/x.svg)) viram
 *  caminhos absolutos do v2; os arquivos vêm de public/assets. */
function converterAssets(texto, relMd, arquivo) {
  const dir = path.posix.dirname(relMd.replace(/\\/g, '/'));
  return texto.replace(/\]\(([^)\s#]+)( +"[^"]*")?\)/g, (todo, alvo, titulo = '') => {
    if (/^[a-z]+:/i.test(alvo) || alvo.startsWith('/') || alvo.endsWith('.md')) return todo;
    const relAlvo = path.posix.normalize(path.posix.join(dir, alvo));
    if (!relAlvo.startsWith('assets/')) return todo;
    if (!fs.existsSync(path.join(DOCS, relAlvo))) falha(`${arquivo}: arquivo inexistente "${alvo}"`);
    return `](${BASE}/${relAlvo}${titulo})`;
  });
}

/** Markdown de uma linha (negrito, código, links já convertidos) → HTML, para o Hero. */
function inlineHtml(md) {
  return escaparHtml(md)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>');
}

const paragrafos = (texto) => texto.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);

/** Topo da home: os parágrafos antes do primeiro "## " (subtítulo, chamada, data do currículo) e
 *  a seção com o bloco "grid cards" (trilhas) saem do corpo e vão para o Hero, acima dos domínios. */
function separarHome(corpo, totalTopicos) {
  const ARQ = 'docs/index.md';
  const inicio = corpo.search(/^## /m);
  if (inicio < 0) falha(`${ARQ}: home sem seções "## "`);
  const [subtitulo, ...intro] = paragrafos(corpo.slice(0, inicio));
  const tagline = subtitulo?.match(/^\*\*(.+)\*\*$/)?.[1] ?? falha(`${ARQ}: o primeiro parágrafo deve ser o subtítulo em **negrito**`);
  const citado = intro.join(' ').match(/(\d+) tópicos/);
  if (citado && Number(citado[1]) !== totalTopicos) {
    falha(`${ARQ}: a chamada fala em ${citado[1]} tópicos, mas os domínios têm ${totalTopicos} páginas no nav do mkdocs.yml`);
  }

  const bloco = corpo.match(/^## (.+)\n+<div class="grid cards" markdown>\n([\s\S]*?)^<\/div>\n*/m)
    ?? falha(`${ARQ}: seção de trilhas (<div class="grid cards" markdown>) não encontrada`);
  const trilhas = bloco[2].split(/^- {3}/m).slice(1).map((item) => {
    const [titulo, descricao, meta] = paragrafos(item);
    const t = titulo?.match(/^\*\*(?:\[(.+?)\]\((.+?)\)|(.+?))\*\*$/) ?? falha(`${ARQ}: card de trilha sem título em **negrito**: ${item.trim()}`);
    if (!descricao || !meta) falha(`${ARQ}: card "${t[1] ?? t[3]}" precisa de título, descrição e uma linha final (ex.: *em breve*)`);
    return { titulo: t[1] ?? t[3], href: t[2] ?? null, descricao: inlineHtml(descricao), meta: meta.replace(/^\*(.+)\*$/, '$1') };
  });

  return {
    tagline: inlineHtml(tagline),
    home: { intro: intro.map(inlineHtml), tituloTrilhas: bloco[1].trim(), trilhas },
    corpo: corpo.slice(inicio).replace(bloco[0], ''),
  };
}

function converterPagina(fonte, relMd, slugsExistentes) {
  const arquivo = `docs/${relMd.replace(/\\/g, '/')}`;
  const texto = fonte.replace(/\r\n/g, '\n');
  const h1 = texto.match(/^# (.+)$/m) ?? falha(`${arquivo}: página sem título "# ..."`);
  let corpo = texto.replace(h1[0] + '\n', '');
  corpo = converterAvisos(corpo.split('\n'), arquivo).join('\n');
  corpo = converterMermaid(corpo);
  corpo = converterLinks(corpo, relMd, slugsExistentes, arquivo);
  corpo = converterAssets(corpo, relMd, arquivo);
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
  // grupos que começam com número são domínios; os outros (ex.: trilhas) só entram no menu
  const dominios = sidebar.filter((g) => g.items && /^\d/.test(g.label)).map((g) => {
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

/** Rótulos de "Anterior"/"Próximo" por slug. "Visão geral" sozinho não diz de qual domínio é, o que
 *  confunde no celular, onde o menu está fechado; aqui ele vira "Domínio 3: visão geral". */
function rotulosDePaginacao(sidebar) {
  const plana = [];
  const percorrer = (itens, grupo) => itens.forEach((i) => {
    if (i.items) return percorrer(i.items, i.label);
    const curto = grupo?.match(/^(\d+)\./) ? `Domínio ${grupo.match(/^(\d+)\./)[1]}` : grupo;
    plana.push({ slug: i.slug, label: i.label === 'Visão geral' && curto ? `${curto}: visão geral` : i.label });
  });
  percorrer(sidebar);
  const rotulos = new Map();
  plana.forEach((e, n) => {
    if (e.slug === undefined) return;
    const prev = plana[n - 1]?.label, next = plana[n + 1]?.label;
    rotulos.set(e.slug, { prev, next });
  });
  return rotulos;
}

function main() {
  const arquivos = listarMd(DOCS).map((p) => path.relative(DOCS, p));
  const slugs = new Set(arquivos.map(slugDe));
  fs.rmSync(SAIDA, { recursive: true, force: true });
  fs.mkdirSync(GERADO, { recursive: true });
  fs.rmSync(ASSETS_PUBLIC, { recursive: true, force: true });
  if (fs.existsSync(ASSETS_DOCS)) fs.cpSync(ASSETS_DOCS, ASSETS_PUBLIC, { recursive: true });

  const { sidebar, dominios } = lerNav();
  const totalTopicos = dominios.reduce((s, d) => s + d.paginas.length, 0);
  const paginacao = rotulosDePaginacao(sidebar);
  let home;
  for (const rel of arquivos) {
    let { titulo, corpo } = converterPagina(fs.readFileSync(path.join(DOCS, rel), 'utf8'), rel, slugs);
    let fm = { title: titulo };
    const vizinhos = paginacao.get(slugDe(rel));
    if (vizinhos?.prev?.endsWith(': visão geral')) fm.prev = vizinhos.prev;
    if (vizinhos?.next?.endsWith(': visão geral')) fm.next = vizinhos.next;
    if (slugDe(rel) === '') {
      const separado = separarHome(corpo, totalTopicos);
      ({ home, corpo } = separado);
      fm = { title: titulo, template: 'splash', hero: { title: titulo, tagline: separado.tagline } };
    }
    const destino = path.join(SAIDA, rel);
    fs.mkdirSync(path.dirname(destino), { recursive: true });
    fs.writeFileSync(destino, `---\n${YAML.stringify(fm)}---\n${corpo}`);
  }

  const todosDominios = lerDominiosDaHome(dominios);
  fs.writeFileSync(path.join(GERADO, 'nav.json'), JSON.stringify({ sidebar, dominios: todosDominios, home }, null, 2));
  console.log(`sync-docs: ${arquivos.length} páginas, ${todosDominios.length} domínios (${dominios.length} com conteúdo)`);
}

main();
