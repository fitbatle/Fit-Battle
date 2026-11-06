const ICONE_NS = 'http://www.w3.org/2000/svg';

const TRACADOS_ICONES = {
  check: ['M5 12.5l4.5 4.5L19 7.5'],
  fechar: ['M6 6l12 12', 'M18 6L6 18'],
  editar: ['M4 20h4L18.5 9.5l-4-4L4 16v4', 'M13.5 6.5l4 4'],
  excluir: ['M4 7h16', 'M9.5 7V4.5h5V7', 'M6 7l1 13h10l1-13', 'M10 11v5.5', 'M14 11v5.5'],
  compartilhar: ['M12 15V3.5', 'M7.5 8L12 3.5 16.5 8', 'M5 13.5V19a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19v-5.5'],
  convite: ['M3.5 6.5h17v11h-17z', 'M3.5 6.5l8.5 7 8.5-7'],
  sequencia: ['M12 3.5c.5 3.2 5 5.2 5 10a5 5 0 0 1-10 0c0-2.6 1.6-4.2 2.6-5.4.2 1.7 1 2.7 2.1 3.1-.4-3.4.6-5.4.3-7.7z'],
  meta: ['M5 21V4', 'M5 4h12.5l-2.2 4 2.2 4H5'],
  musculacao: ['M2.5 9.5v5', 'M5.5 7v10', 'M5.5 12h13', 'M18.5 7v10', 'M21.5 9.5v5'],
  cardio: ['M2.5 12h4l2.2-4.5 4.3 9 2.5-4.5h6'],
  yoga: ['M10 4.5a2 2 0 1 0 4 0a2 2 0 1 0-4 0', 'M5 9.5l7 1.5 7-1.5', 'M12 11v4', 'M8.5 21.5l3.5-6.5 3.5 6.5'],
  generico: ['M3.5 12a8.5 8.5 0 1 0 17 0a8.5 8.5 0 1 0-17 0', 'M12 8v8', 'M8 12h8'],
};

const ICONE_POR_TIPO = {
  musculacao: 'musculacao',
  cardio: 'cardio',
  yoga: 'yoga',
  outro: 'generico',
};

function criarIcone(nome, opcoes) {
  const formas = TRACADOS_ICONES[nome] || TRACADOS_ICONES.generico;
  const svg = document.createElementNS(ICONE_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '1.75');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  svg.classList.add('icone');
  if (opcoes && opcoes.classe) svg.classList.add(opcoes.classe);
  formas.forEach(function (d) {
    const caminho = document.createElementNS(ICONE_NS, 'path');
    caminho.setAttribute('d', d);
    svg.appendChild(caminho);
  });
  return svg;
}

function nomeIconeDoTipo(tipo) {
  return ICONE_POR_TIPO[tipo] || 'generico';
}

function montarComIcone(nome, texto) {
  return [criarIcone(nome), document.createTextNode(' ' + texto)];
}

function ativarIcones(raiz) {
  (raiz || document).querySelectorAll('[data-icone]').forEach(function (marcador) {
    marcador.replaceChildren(criarIcone(marcador.getAttribute('data-icone')));
  });
}

document.addEventListener('DOMContentLoaded', function () {
  ativarIcones(document);
});
