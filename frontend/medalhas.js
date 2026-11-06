const ICONE_MEDALHA = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="9" r="6"/><path d="M8.5 14.5 7 22l5-2.5 5 2.5-1.5-7.5"/></svg>';

function formatarDataMedalha(iso) {
  const partes = String(iso || '').split('-');
  return partes.length === 3 ? partes[2] + '/' + partes[1] + '/' + partes[0] : '';
}

function textoProgressoMedalha(medalha) {
  if (medalha.conquistada) {
    const data = formatarDataMedalha(medalha.data_conquista);
    return data ? 'Conquistada em ' + data : 'Conquistada';
  }
  return medalha.progresso.valor + ' de ' + medalha.progresso.meta;
}

function botaoCompartilharMedalha(medalha) {
  const botao = criarElemento('button', { type: 'button', classe: 'btn btn--secundario btn--pequeno', texto: 'Compartilhar' });
  botao.addEventListener('click', function () {
    abrirCompartilhar({
      tipoConteudo: 'medalha',
      chaveMedalha: medalha.chave,
      texto: 'Conquistei a medalha "' + medalha.nome + '" no FitBattle! #FitBattle'
    });
  });
  return botao;
}

function criarCartaoMedalha(medalha, opcoes) {
  const item = criarElemento('li', {
    classe: 'medalha ' + (medalha.conquistada ? 'medalha--conquistada' : 'medalha--bloqueada')
  });
  const textos = criarElemento('div', { classe: 'medalha__texto' }, [
    criarElemento('strong', { classe: 'medalha__nome', texto: medalha.nome }),
    criarElemento('span', { classe: 'medalha__criterio', texto: medalha.criterio }),
    criarElemento('span', { classe: 'medalha__progresso', texto: textoProgressoMedalha(medalha) })
  ]);
  item.appendChild(criarElemento('span', { classe: 'medalha__icone', 'aria-hidden': 'true', html: ICONE_MEDALHA }));
  item.appendChild(textos);
  if (opcoes.compartilhavel && medalha.conquistada) {
    item.appendChild(botaoCompartilharMedalha(medalha));
  }
  return item;
}

function renderizarMedalhas(lista, medalhas, opcoes) {
  lista.replaceChildren.apply(lista, medalhas.map(function (medalha) {
    return criarCartaoMedalha(medalha, opcoes);
  }));
}
