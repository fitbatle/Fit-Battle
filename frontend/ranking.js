const LIMITE_TABELA = 100;

let usuarioLogado = null;
let escopoAtual = 'global';
let situacaoRanking = null;
let exercicioAtual = null;

document.addEventListener('DOMContentLoaded', iniciarRanking);

async function iniciarRanking() {
  if (!exigirLogin()) return;
  usuarioLogado = await usuarioAtualOuFalha(iniciarRanking);
  if (!usuarioLogado) return;
  if (usuarioLogado.perfil_publico === false) {
    document.getElementById('avisoPerfilOculto').hidden = false;
  }
  situacaoRanking = await carregarSituacaoRanking(iniciarRanking);
  if (!situacaoRanking) return;

  ligarAbas();
  ligarAbasExercicio();
  configurarBotaoRegional();
  atualizarRanking();
}

async function carregarSituacaoRanking(aoTentarDeNovo) {
  try {
    const resposta = await api(`/usuarios/${usuarioLogado.id}/ranking`);
    if (!resposta.ok) throw new ErroDeConexao();
    return await resposta.json();
  } catch (erro) {
    mostrarFalhaDeCarregamento(aoTentarDeNovo);
    return null;
  }
}

function configurarBotaoRegional() {
  const semCidade = !usuarioLogado.cidade;
  document.getElementById('notaRegional').hidden = !semCidade;
}

function ligarAbas() {
  document.getElementById('abaGlobal').addEventListener('click', function () {
    selecionarEscopo('global');
  });
  document.getElementById('abaRegional').addEventListener('click', function () {
    if (!usuarioLogado.cidade) {
      mostrarToast('Informe sua cidade em "Editar perfil" para ver o ranking da sua região.');
      return;
    }
    selecionarEscopo('regional');
  });
  document.getElementById('abaEstado').addEventListener('click', function () {
    if (!usuarioLogado.estado) {
      mostrarToast('Informe seu estado em "Editar perfil" para ver o ranking do seu estado.');
      return;
    }
    selecionarEscopo('estado');
  });
}

function selecionarEscopo(escopo) {
  if (escopo === escopoAtual) return;
  escopoAtual = escopo;

  const global = document.getElementById('abaGlobal');
  const regional = document.getElementById('abaRegional');
  const estado = document.getElementById('abaEstado');
  global.classList.toggle('aba--ativa', escopo === 'global');
  global.setAttribute('aria-selected', String(escopo === 'global'));
  regional.classList.toggle('aba--ativa', escopo === 'regional');
  regional.setAttribute('aria-selected', String(escopo === 'regional'));
  estado.classList.toggle('aba--ativa', escopo === 'estado');
  estado.setAttribute('aria-selected', String(escopo === 'estado'));

  document.getElementById('tabelaRanking').classList.toggle('ranking-tabela--sem-local', escopo !== 'global');

  atualizarRanking();
}

function ligarAbasExercicio() {
  document.getElementById('abaTodosExercicios').addEventListener('click', function () {
    selecionarExercicio(null);
  });
  document.querySelectorAll('.aba-exercicio').forEach(function (botao) {
    botao.addEventListener('click', function () {
      selecionarExercicio(botao.getAttribute('data-titulo'));
    });
  });
}

function selecionarExercicio(titulo) {
  if (titulo === exercicioAtual) return;
  exercicioAtual = titulo;

  document.getElementById('abaTodosExercicios').classList.toggle('aba--ativa', !titulo);
  document.querySelectorAll('.aba-exercicio').forEach(function (botao) {
    botao.classList.toggle('aba--ativa', botao.getAttribute('data-titulo') === titulo);
  });

  const cabecalho = document.getElementById('colunaMetrica');
  const tituloQuadro = document.getElementById('tituloQuadro');
  const descricao = document.getElementById('rankingDescricao');

  if (titulo) {
    cabecalho.textContent = 'Carga Máxima';
    tituloQuadro.textContent = 'Quadro de ' + titulo;
    descricao.textContent = 'Veja quem levanta mais peso em ' + titulo + '. Carga bruta levantada, sem ajuste por repetições.';
  } else {
    cabecalho.textContent = 'Pontuação';
    tituloQuadro.textContent = 'Quadro geral';
    descricao.textContent = 'Veja quem está na frente e suba no placar. A pontuação soma todo o XP já conquistado nos treinos.';
  }

  atualizarRanking();
}

function atualizarRanking() {
  if (exercicioAtual) {
    carregarRankingPorExercicio(exercicioAtual, escopoAtual === 'regional' ? usuarioLogado.cidade : null);
  } else {
    carregarRanking(escopoAtual);
  }
}

async function carregarRanking(escopo) {
  mostrarCarregando();
  try {
    const url = escopo === 'regional'
      ? '/ranking/regional?cidade=' + encodeURIComponent(usuarioLogado.cidade) + '&limite=' + LIMITE_TABELA
      : escopo === 'estado'
        ? '/ranking/regional?estado=' + encodeURIComponent(usuarioLogado.estado) + '&limite=' + LIMITE_TABELA
        : '/ranking/global?limite=' + LIMITE_TABELA;

    const resposta = await api(url);
    const dados = await resposta.json();
    if (!resposta.ok) {
      mostrarErro(dados.erro || 'Não foi possível carregar o ranking.');
      return;
    }

    renderizarPodio(dados, 'xp');
    renderizarTabela(dados, 'xp');
    renderizarMinhaPosicao(dados, 'xp', { escopo: escopo });
  } catch (e) {
    mostrarFalhaDeCarregamento(function () { carregarRanking(escopo); });
  }
}

async function carregarRankingPorExercicio(titulo, cidade) {
  mostrarCarregando();
  try {
    let url = '/ranking/exercicio?titulo=' + encodeURIComponent(titulo) + '&limite=' + LIMITE_TABELA;
    if (cidade) url += '&cidade=' + encodeURIComponent(cidade);

    const resposta = await api(url);
    const dados = await resposta.json();
    if (!resposta.ok) {
      mostrarErro(dados.erro || 'Não foi possível carregar o ranking.');
      return;
    }

    renderizarPodio(dados, 'exercicio');
    renderizarTabela(dados, 'exercicio', { vazio: 'Ninguém registrou este exercício ainda.' });
    renderizarMinhaPosicao(dados, 'exercicio', { titulo: titulo });
  } catch (e) {
    mostrarFalhaDeCarregamento(function () { carregarRankingPorExercicio(titulo, cidade); });
  }
}

function mostrarCarregando() {
  document.getElementById('podio').innerHTML = '<p class="estado-vazio">Carregando o pódio...</p>';
  document.getElementById('tabelaRankingCorpo').innerHTML = '<tr><td colspan="4" class="estado-vazio">Carregando...</td></tr>';
  document.getElementById('rankingContagem').textContent = '';
  document.getElementById('minhaPosicao').hidden = true;
}

function mostrarErro(mensagem) {
  document.getElementById('podio').innerHTML = '<p class="estado-vazio">' + esc(mensagem) + '</p>';
  document.getElementById('tabelaRankingCorpo').innerHTML = '<tr><td colspan="4" class="estado-vazio">' + esc(mensagem) + '</td></tr>';
}

function valorMetrica(item, modo) {
  return modo === 'exercicio' ? item.carga_maxima : item.pontuacao_total;
}

function textoMetrica(item, modo) {
  return modo === 'exercicio' ? formatarNumero(item.carga_maxima) + ' kg' : item.pontuacao_total + ' xp';
}

function renderizarPodio(dados, modo) {
  const podio = document.getElementById('podio');
  if (dados.length === 0) {
    podio.innerHTML = '<p class="estado-vazio">' + (modo === 'exercicio' ? 'Ninguém registrou este exercício ainda.' : 'Ninguém no ranking ainda.') + '</p>';
    return;
  }
  const vagas = ordenarVagasPodio(dados.slice(0, 3));
  podio.className = 'podio podio--' + vagas.length;
  podio.innerHTML = vagas.map(function (item) { return htmlVagaPodio(item, modo); }).join('');
}

function htmlVagaPodio(item, modo) {
  const eu = usuarioLogado && item.id_usuario === usuarioLogado.id;
  const rodape = modo === 'exercicio'
    ? ''
    : `<span class="podio-vaga__nivel">${esc(nomeNivel(item))}</span>`;

  return `<div class="podio-vaga podio-vaga--${item.posicao}${eu ? ' podio-vaga--eu' : ''}">
    <span class="podio-vaga__pos">${item.posicao}º</span>
    <span class="avatar" aria-hidden="true">${esc(iniciais(item.nome))}</span>
    <span class="podio-vaga__nome">${esc(item.nome)}${eu ? ' (você)' : ''}</span>
    <span class="podio-vaga__pontos">${textoMetrica(item, modo)}</span>
    ${rodape}
  </div>`;
}

function renderizarTabela(dados, modo, opcoes) {
  opcoes = opcoes || {};
  const corpo = document.getElementById('tabelaRankingCorpo');
  const contagem = document.getElementById('rankingContagem');

  if (dados.length === 0) {
    corpo.innerHTML = '<tr><td colspan="4" class="estado-vazio">' + esc(opcoes.vazio || 'Ninguém no ranking ainda.') + '</td></tr>';
    contagem.textContent = '';
    return;
  }

  contagem.textContent = 'Exibindo ' + dados.length + ' atleta' + (dados.length > 1 ? 's' : '');
  corpo.innerHTML = dados.map(function (item) { return htmlLinhaTabela(item, modo); }).join('');
}

function htmlLinhaTabela(item, modo) {
  const eu = usuarioLogado && item.id_usuario === usuarioLogado.id;
  const local = [item.cidade, item.estado].filter(Boolean).join(' - ') || '—';
  return `<tr class="${eu ? 'linha--eu' : ''}">
    <td class="ranking-tabela__pos">${item.posicao}º</td>
    <td>
      <div class="ranking-tabela__atleta">
        <span class="avatar avatar--pequeno" aria-hidden="true">${esc(iniciais(item.nome))}</span>
        <span>${esc(item.nome)}${eu ? ' (você)' : ''}</span>
      </div>
    </td>
    <td>${esc(local)}</td>
    <td class="ranking-tabela__pontos">${textoMetrica(item, modo)}</td>
  </tr>`;
}

function renderizarMinhaPosicao(dados, modo, contexto) {
  contexto = contexto || {};
  const secao = document.getElementById('minhaPosicao');
  const minhaLinha = dados.find(function (item) { return item.id_usuario === usuarioLogado.id; });
  const rotulo = document.getElementById('minhaPosicaoRotulo');
  const legenda = document.getElementById('minhaPosicaoLegenda');
  const barraWrap = document.getElementById('minhaPosicaoBarraWrap');
  const barra = document.getElementById('minhaPosicaoBarra');

  if (modo === 'exercicio') {
    rotulo.textContent = 'Sua posição em ' + contexto.titulo;
  } else {
    rotulo.textContent = contexto.escopo === 'regional'
      ? 'Sua posição no ranking da sua cidade'
      : contexto.escopo === 'estado'
        ? 'Sua posição no ranking do seu estado'
        : 'Sua posição no ranking geral';
  }

  if (!minhaLinha) {
    if (situacaoRanking && situacaoRanking.restricao === 'menor_de_idade') {
      secao.hidden = false;
      document.getElementById('minhaPosicaoTexto').textContent = '—';
      legenda.textContent = 'O ranking público é só para maiores de 18 anos.';
      barraWrap.hidden = true;
      return;
    }
    if (modo === 'exercicio') {
      secao.hidden = false;
      document.getElementById('minhaPosicaoTexto').textContent = '—';
      legenda.textContent = 'Você ainda não registrou ' + contexto.titulo + '. Registre um treino para entrar no ranking!';
      barraWrap.hidden = true;
    } else {
      secao.hidden = true;
    }
    return;
  }
  secao.hidden = false;
  document.getElementById('minhaPosicaoTexto').textContent = '#' + minhaLinha.posicao;

  const indice = dados.indexOf(minhaLinha);
  const acima = indice > 0 ? dados[indice - 1] : null;
  const unidade = modo === 'exercicio' ? 'kg' : 'xp';

  if (!acima) {
    legenda.textContent = minhaLinha.posicao === 1
      ? 'Você está no topo do ranking!'
      : 'Continue treinando para subir no ranking!';
    barraWrap.hidden = true;
    return;
  }

  const valorAcima = valorMetrica(acima, modo);
  const valorMeu = valorMetrica(minhaLinha, modo);
  const faltam = Math.max(0, valorAcima - valorMeu);
  const percentual = valorAcima > 0
    ? Math.min(100, Math.round((valorMeu / valorAcima) * 100))
    : 100;

  barraWrap.hidden = false;
  barra.style.width = percentual + '%';
  legenda.textContent = faltam > 0
    ? `Faltam ${formatarNumero(faltam)} ${unidade} para ultrapassar ${acima.nome} (#${acima.posicao})`
    : `Você empatou com ${acima.nome} (#${acima.posicao})`;

}

function formatarNumero(n) {
  return Number(n).toString().replace('.', ',');
}

