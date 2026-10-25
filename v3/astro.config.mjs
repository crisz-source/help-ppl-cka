// Layout 3: landing desenhada no Figma ("Landing — Estudo CKA em público"). Só a página inicial;
// os links levam às páginas do layout 2 (/v2/), que tem o mesmo visual escuro. Os números e a
// lista de domínios vêm de ../mkdocs.yml e ../docs (ver src/dados.ts).
import { defineConfig } from 'astro/config';

export default defineConfig({
	site: 'https://crisz-source.github.io',
	base: '/help-ppl-cka/v3', // o CI publica este build em site/v3
	trailingSlash: 'always',
});
