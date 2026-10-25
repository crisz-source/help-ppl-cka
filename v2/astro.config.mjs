// Layout 2 do site. O conteúdo vem de ../docs (o mesmo do layout 1, MkDocs),
// copiado e convertido por scripts/sync-docs.mjs antes de cada build.
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import nav from './src/generated/nav.json' with { type: 'json' };

// O Expressive Code põe um "Janela do terminal" escondido em cada bloco de shell, e o Pagefind
// indexa esse texto: os resultados da busca começavam com "terminal $ ...". Fora do índice.
const buscaSemRotuloDeTerminal = {
	name: 'busca-sem-rotulo-de-terminal',
	hooks: {
		// no nível do grupo: a moldura (com o figcaption) é montada depois dos hooks de bloco
		postprocessRenderedBlockGroup({ renderData }) {
			const visitar = (no) => {
				if (no.tagName === 'figcaption') no.properties['data-pagefind-ignore'] = '';
				no.children?.forEach(visitar);
			};
			visitar(renderData.groupAst);
		},
	},
};

export default defineConfig({
	site: 'https://crisz-source.github.io',
	base: '/help-ppl-cka/v2', // o layout 1 fica na raiz; o CI publica este build em site/v2
	trailingSlash: 'always',
	integrations: [
		starlight({
			title: 'CKA em público',
			description: 'Preparação para a certificação CKA, em português do Brasil.',
			defaultLocale: 'root',
			locales: { root: { label: 'Português', lang: 'pt-BR' } },
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/crisz-source/help-ppl-cka' },
			],
			sidebar: nav.sidebar,
			customCss: [
				'@fontsource/jetbrains-mono/400.css',
				'./src/styles/tema.css',
				'./src/styles/terminal.css',
			],
			components: {
				Head: './src/components/Head.astro',
				Hero: './src/components/Hero.astro',
				PageTitle: './src/components/PageTitle.astro',
				SocialIcons: './src/components/SocialIcons.astro',
			},
			expressiveCode: {
				themes: ['github-dark-default', 'github-light-default'],
				plugins: [buscaSemRotuloDeTerminal],
				styleOverrides: { borderRadius: '0.6rem', codeFontFamily: "'JetBrains Mono', monospace" },
			},
		}),
	],
});
