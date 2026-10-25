// Menu no celular: o Starlight abre o menu lateral sempre no topo, e com todos os grupos abertos a
// página atual fica a mais de uma tela de distância. Ao abrir, o menu rola até ela.

const menu = document.getElementById('starlight__sidebar');

menu?.addEventListener('toggle', (e) => {
	if ((e as ToggleEvent).newState !== 'open') return;
	menu.querySelector('[aria-current="page"]')?.scrollIntoView({ block: 'center' });
});
