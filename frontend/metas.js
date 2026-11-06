let usuarioLogado = null;
let todasAsMetas = [];
let abaAtual = 'em_andamento';
let todosOsDesafios = [];
let usuarioEhAdmin = false;
let idDesafioEmEdicao = null;

document.addEventListener('DOMContentLoaded', function () {
  usuarioLogado = exigirLogin();
  if (!usuarioLogado) return;

  document.getElementById('btnCriarMeta').addEventListener('click', function () {
    window.location.href = 'metas-criar.html';
  });
  document.getElementById('btnCriarPrimeiraMeta').addEventListener('click', function () {
    window.location.href = 'metas-criar.html';
  });
  document.getElementById('abaEmAndamento').addEventListener('click', function () { selecionarAba('em_andamento'); });
  document.getElementById('abaConcluidas').addEventListener('click', function () { selecionarAba('concluida'); });

  document.getElementById('abaSecaoMetas').addEventListener('click', function () { selecionarSecao('metas'); });
  document.getElementById('abaSecaoDesafios').addEventListener('click', function () { selecionarSecao('desafios'); });
  document.getElementById('formDesafio').addEventListener('submit', enviarFormDesafio);
  document.getElementById('btnCancelarEdicaoDesafio').addEventListener('click', cancelarEdicaoDesafio);

  carregarMetas();
  carregarDesafios();
  inicializarAdmin();
});

function selecionarSecao(secao) {
  document.getElementById('abaSecaoMetas').classList.toggle('aba--ativa', secao === 'metas');
  document.getElementById('abaSecaoDesafios').classList.toggle('aba--ativa', secao === 'desafios');
  document.getElementById('secaoMetas').hidden = secao !== 'metas';
  document.getElementById('secaoDesafios').hidden = secao !== 'desafios';
}

async function inicializarAdmin() {
  try {
    const usuario = await usuarioAtual();
    usuarioEhAdmin = !!(usuario && usuario.admin);
  } catch (e) {
    usuarioEhAdmin = false;
  }
  document.getElementById('formDesafioContainer').hidden = !usuarioEhAdmin;
  if (todosOsDesafios.length) renderizarDesafios();
}

async function carregarMetas() {
  const grade = document.getElementById('metasGrade');
  grade.innerHTML = '<p class="estado-vazio">Carregando suas metas...</p>';

  try {
    const resposta = await api('/metas');
    const metas = await resposta.json();
    if (!resposta.ok) {
      grade.innerHTML = '<p class="estado-vazio">Não foi possível carregar suas metas.</p>';
      return;
    }
    todasAsMetas = metas;
    atualizarResumo();
    renderizarAba();
    renderizarRecentes();
    atualizarEmAndamentoGeral();
  } catch (e) {
    grade.innerHTML = '';
    mostrarFalhaDeCarregamento(function () { carregarMetas(); carregarDesafios(); });
  }
}

function atualizarResumo() {
  const ativas = todasAsMetas.filter(function (m) { return m.status === 'em_andamento'; });
  const concluidas = todasAsMetas.filter(function (m) { return m.status === 'concluida'; });
  const curtas = ativas.filter(function (m) { return m.tipo === 'curto_prazo'; }).length;
  const longas = ativas.length - curtas;

  document.getElementById('totalAtivas').textContent = ativas.length;
  document.getElementById('detalheAtivas').textContent =
    ativas.length ? curtas + ' curto prazo · ' + longas + ' longo prazo' : 'Nenhuma meta em andamento';
  document.getElementById('contadorEmAndamento').textContent = ativas.length;

  document.getElementById('totalConcluidas').textContent = concluidas.length;
  document.getElementById('contadorConcluidasAba').textContent = concluidas.length;
  if (concluidas.length) {
    const ultima = concluidas.slice().sort(function (a, b) {
      return new Date(b.concluida_em) - new Date(a.concluida_em);
    })[0];
    document.getElementById('detalheConcluidas').textContent = 'Última em ' + formatarData(ultima.concluida_em);
  } else {
    document.getElementById('detalheConcluidas').textContent = 'Nenhuma meta concluída ainda';
  }
}

function selecionarAba(aba) {
  abaAtual = aba;
  document.getElementById('abaEmAndamento').classList.toggle('aba--ativa', aba === 'em_andamento');
  document.getElementById('abaConcluidas').classList.toggle('aba--ativa', aba === 'concluida');
  renderizarAba();
}

function renderizarAba() {
  const grade = document.getElementById('metasGrade');
  const vazio = document.getElementById('estadoVazioMetas');
  const filtradas = todasAsMetas.filter(function (m) { return m.status === abaAtual; });

  if (todasAsMetas.length === 0) {
    grade.hidden = true;
    vazio.hidden = false;
    return;
  }
  vazio.hidden = true;
  grade.hidden = false;

  if (filtradas.length === 0) {
    grade.innerHTML = '<p class="estado-vazio">' +
      (abaAtual === 'em_andamento' ? 'Nenhuma meta em andamento.' : 'Nenhuma meta concluída ainda.') +
      '</p>';
    return;
  }

  grade.innerHTML = filtradas.map(htmlCartaoMeta).join('');
}

function unidade(meta) {
  return meta.tipo_metrica === 'carga_maxima' ? 'kg' : 'treinos';
}

function htmlCartaoMeta(meta) {
  const un = unidade(meta);
  const tipoLabel = meta.tipo === 'curto_prazo' ? 'Curto Prazo' : 'Longo Prazo';
  const metricaLabel = meta.tipo_metrica === 'carga_maxima' ? 'Carga Máxima' : 'Frequência';
  const prazo = meta.data_final ? 'Prazo: ' + formatarData(meta.data_final) : 'Sem prazo definido';

  return `<article class="card meta-cartao">
    <div class="meta-cartao__tags">
      <span class="badge">${esc(tipoLabel)}</span>
      <span class="meta-cartao__exercicio">${esc(metricaLabel)}</span>
    </div>
    ${meta.exercicio ? `<span class="rotulo-mini">${esc(meta.exercicio.toUpperCase())}</span>` : ''}
    <div class="meta-cartao__titulo">${esc(meta.titulo)}</div>
    <div class="meta-cartao__linha">
      <span class="rotulo-mini">Atual</span>
      <span class="rotulo-mini">Objetivo</span>
    </div>
    <div class="meta-cartao__linha">
      <strong>${formatarNumero(meta.valor_atual)} ${un}</strong>
      <strong>${formatarNumero(meta.valor_objetivo)} ${un}</strong>
    </div>
    <div class="barra"><div class="barra__preenchimento" style="width:${meta.percentual}%"></div></div>
    <div class="meta-cartao__progresso-topo">
      <span>${meta.status === 'concluida' ? 'Meta concluída' : 'Faltam ' + formatarNumero(meta.faltam) + ' ' + un}</span>
      <span>${meta.percentual}%</span>
    </div>
    <div class="meta-cartao__rodape">
      <span class="meta-cartao__prazo">${esc(prazo)}</span>
    </div>
    <a class="btn btn--secundario btn--pequeno btn--bloco" href="metas-detalhes.html?id=${meta.id}">Ver Detalhes</a>
  </article>`;
}

function renderizarRecentes() {
  const secao = document.getElementById('secaoRecentes');
  const lista = document.getElementById('listaRecentes');
  const concluidas = todasAsMetas
    .filter(function (m) { return m.status === 'concluida'; })
    .sort(function (a, b) { return new Date(b.concluida_em) - new Date(a.concluida_em); })
    .slice(0, 5);

  if (concluidas.length === 0) {
    secao.hidden = true;
    return;
  }
  secao.hidden = false;

  lista.innerHTML = concluidas.map(function (meta) {
    const un = unidade(meta);
    return `<li class="card meta-recente-item">
      <div class="meta-recente-item__texto">
        <span class="meta-recente-item__titulo">${esc(meta.titulo)}</span>
        <span class="meta-recente-item__detalhe">Concluída em ${formatarData(meta.concluida_em)} · 100% atingido (${formatarNumero(meta.valor_atual)} ${un} de ${formatarNumero(meta.valor_objetivo)} ${un})</span>
      </div>
      <a class="btn btn--secundario btn--pequeno" href="metas-detalhes.html?id=${meta.id}">Ver</a>
    </li>`;
  }).join('');
}

function formatarData(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}

function formatarNumero(n) {
  return Number(n).toString().replace('.', ',');
}

async function carregarDesafios() {
  const grade = document.getElementById('desafiosGrade');
  try {
    const resposta = await api('/desafios');
    const desafios = await resposta.json();
    if (!resposta.ok) {
      grade.innerHTML = '<p class="estado-vazio">Não foi possível carregar os desafios.</p>';
      return;
    }
    todosOsDesafios = desafios;
    renderizarDesafios();
    atualizarEmAndamentoGeral();
  } catch (e) {
    grade.innerHTML = '';
    mostrarFalhaDeCarregamento(function () { carregarMetas(); carregarDesafios(); });
  }
}

function renderizarDesafios() {
  const grade = document.getElementById('desafiosGrade');
  const vazio = document.getElementById('estadoVazioDesafios');
  const contador = document.getElementById('contadorDesafios');
  contador.textContent = todosOsDesafios.length || '';

  if (todosOsDesafios.length === 0) {
    grade.hidden = true;
    vazio.hidden = false;
    return;
  }
  vazio.hidden = true;
  grade.hidden = false;
  grade.innerHTML = todosOsDesafios.map(htmlCartaoDesafio).join('');

  todosOsDesafios.forEach(function (desafio) {
    const btnParticipar = document.getElementById('btnParticipar' + desafio.id);
    if (btnParticipar) btnParticipar.addEventListener('click', function () { participarDesafio(desafio.id); });
    const btnDesistir = document.getElementById('btnDesistir' + desafio.id);
    if (btnDesistir) btnDesistir.addEventListener('click', function () { desistirDesafio(desafio.id); });
    const btnEncerrar = document.getElementById('btnEncerrar' + desafio.id);
    if (btnEncerrar) btnEncerrar.addEventListener('click', function () { encerrarDesafio(desafio.id); });
    const btnEditar = document.getElementById('btnEditar' + desafio.id);
    if (btnEditar) btnEditar.addEventListener('click', function () { editarDesafio(desafio); });
  });
}

function unidadeDesafio(desafio) {
  return desafio.tipo_metrica === 'carga_maxima' ? 'kg' : 'treinos';
}

function htmlCartaoDesafio(desafio) {
  const un = unidadeDesafio(desafio);
  const metricaLabel = desafio.tipo_metrica === 'carga_maxima' ? 'Carga Máxima' : 'Treinos';
  const inscricao = desafio.minha_inscricao;
  const status = inscricao.status;

  let acao = `<button type="button" class="btn btn--primario btn--pequeno btn--bloco" id="btnParticipar${desafio.id}">Participar</button>`;
  if (status === 'inscrito') {
    acao = `<button type="button" class="btn btn--secundario btn--pequeno btn--bloco" id="btnDesistir${desafio.id}">Desistir</button>`;
  } else if (status === 'concluido') {
    acao = '<span class="badge badge--sucesso">Concluído</span>';
  } else if (status === 'desistiu') {
    acao = `<button type="button" class="btn btn--primario btn--pequeno btn--bloco" id="btnParticipar${desafio.id}">Participar de novo</button>`;
  }

  let acoesAdmin = '';
  if (usuarioEhAdmin) {
    acoesAdmin = `<div class="meta-cartao__rodape">
      <button type="button" class="btn btn--secundario btn--pequeno" id="btnEditar${desafio.id}">Editar</button>
      <button type="button" class="btn btn--secundario btn--pequeno" id="btnEncerrar${desafio.id}">Encerrar</button>
    </div>`;
  }

  return `<article class="card meta-cartao">
    <div class="meta-cartao__tags">
      <span class="badge">${esc(metricaLabel)}</span>
      <span class="meta-cartao__exercicio">${esc((desafio.exercicio || 'livre').toUpperCase())}</span>
    </div>
    <div class="meta-cartao__titulo">${esc(desafio.nome)}</div>
    ${desafio.descricao ? `<p class="rotulo-mini">${esc(desafio.descricao)}</p>` : ''}
    <div class="meta-cartao__linha">
      <span class="rotulo-mini">Atual</span>
      <span class="rotulo-mini">Objetivo</span>
    </div>
    <div class="meta-cartao__linha">
      <strong>${formatarNumero(inscricao.valor_atual)} ${un}</strong>
      <strong>${formatarNumero(desafio.valor_objetivo)} ${un}</strong>
    </div>
    <div class="barra"><div class="barra__preenchimento" style="width:${inscricao.percentual}%"></div></div>
    <div class="meta-cartao__progresso-topo">
      <span>${desafio.recompensa_xp ? '+' + desafio.recompensa_xp + ' XP' : 'Sem recompensa em XP'}</span>
      <span>${inscricao.percentual}%</span>
    </div>
    <div class="meta-cartao__rodape">
      <span class="meta-cartao__prazo">Até ${formatarData(desafio.data_fim)}</span>
    </div>
    <a class="btn btn--secundario btn--pequeno btn--bloco" href="desafio-detalhes.html?id=${desafio.id}">Ver Detalhes</a>
    ${acao}
    ${acoesAdmin}
  </article>`;
}

async function participarDesafio(id) {
  try {
    const resposta = await api('/desafios/' + id + '/participar', { method: 'POST' });
    const dados = await resposta.json();
    if (!resposta.ok) { mostrarToast(dados.erro || 'Não foi possível participar.'); return; }
    mostrarToast('Inscrição confirmada!');
    carregarDesafios();
  } catch (e) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}

async function desistirDesafio(id) {
  try {
    const resposta = await api('/desafios/' + id + '/participar', { method: 'DELETE' });
    const dados = await resposta.json();
    if (!resposta.ok) { mostrarToast(dados.erro || 'Não foi possível desistir.'); return; }
    mostrarToast('Você desistiu do desafio.');
    carregarDesafios();
  } catch (e) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}

async function encerrarDesafio(id) {
  if (!window.confirm('Encerrar este desafio agora?')) return;
  try {
    const resposta = await api('/desafios/' + id + '/encerrar', { method: 'PUT' });
    if (!resposta.ok) { mostrarToast('Não foi possível encerrar.'); return; }
    mostrarToast('Desafio encerrado.');
    carregarDesafios();
  } catch (e) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}

function editarDesafio(desafio) {
  idDesafioEmEdicao = desafio.id;
  document.getElementById('tituloFormDesafio').textContent = 'Editar desafio';
  document.getElementById('btnSalvarDesafio').replaceChildren(...montarComIcone('check', 'Salvar alterações'));
  document.getElementById('btnCancelarEdicaoDesafio').hidden = false;
  document.getElementById('desafioNome').value = desafio.nome;
  document.getElementById('desafioDescricao').value = desafio.descricao || '';
  document.getElementById('desafioTipoMetrica').value = desafio.tipo_metrica;
  document.getElementById('desafioExercicio').value = desafio.exercicio || '';
  document.getElementById('desafioValorObjetivo').value = desafio.valor_objetivo;
  document.getElementById('desafioRecompensaXp').value = desafio.recompensa_xp;
  document.getElementById('desafioDataInicio').value = desafio.data_inicio;
  document.getElementById('desafioDataFim').value = desafio.data_fim;
  document.getElementById('formDesafioContainer').scrollIntoView({ behavior: 'smooth' });
}

function cancelarEdicaoDesafio() {
  idDesafioEmEdicao = null;
  document.getElementById('formDesafio').reset();
  document.getElementById('tituloFormDesafio').textContent = 'Criar novo desafio';
  document.getElementById('btnSalvarDesafio').replaceChildren(...montarComIcone('check', 'Criar desafio'));
  document.getElementById('btnCancelarEdicaoDesafio').hidden = true;
}

async function enviarFormDesafio(evento) {
  evento.preventDefault();
  const erro = document.getElementById('erroFormDesafio');
  erro.textContent = '';
  const dados = {
    nome: document.getElementById('desafioNome').value,
    descricao: document.getElementById('desafioDescricao').value,
    tipo_metrica: document.getElementById('desafioTipoMetrica').value,
    exercicio: document.getElementById('desafioExercicio').value,
    valor_objetivo: document.getElementById('desafioValorObjetivo').value,
    recompensa_xp: document.getElementById('desafioRecompensaXp').value,
    data_inicio: document.getElementById('desafioDataInicio').value,
    data_fim: document.getElementById('desafioDataFim').value,
  };
  try {
    const caminho = idDesafioEmEdicao ? '/desafios/' + idDesafioEmEdicao : '/desafios';
    const metodo = idDesafioEmEdicao ? 'PUT' : 'POST';
    const resposta = await api(caminho, {
      method: metodo,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.json();
    if (!resposta.ok) { erro.textContent = corpo.erro || 'Não foi possível salvar o desafio.'; return; }
    mostrarToast(idDesafioEmEdicao ? 'Desafio atualizado.' : 'Desafio criado!');
    cancelarEdicaoDesafio();
    carregarDesafios();
  } catch (e) {
    erro.textContent = 'Não foi possível falar com o servidor. Tente novamente.';
  }
}

function atualizarEmAndamentoGeral() {
  const container = document.getElementById('listaEmAndamentoGeral');
  if (!container) return;

  const metasAtivas = todasAsMetas.filter(function (m) { return m.status === 'em_andamento'; });
  const desafiosInscritos = todosOsDesafios.filter(function (d) { return d.minha_inscricao.status === 'inscrito'; });

  if (metasAtivas.length === 0 && desafiosInscritos.length === 0) {
    container.innerHTML = '<p class="estado-vazio">Nenhuma meta ou desafio em andamento agora.</p>';
    return;
  }

  const itens = metasAtivas.map(function (m) {
    return { titulo: m.titulo, percentual: m.percentual, link: 'metas-detalhes.html?id=' + m.id, rotulo: 'Meta' };
  }).concat(desafiosInscritos.map(function (d) {
    return {
      titulo: d.nome, percentual: d.minha_inscricao.percentual,
      link: 'desafio-detalhes.html?id=' + d.id, rotulo: 'Desafio',
    };
  }));

  container.innerHTML = itens.map(function (item) {
    return `<div class="card meta-recente-item">
      <div class="meta-recente-item__texto">
        <span class="badge">${esc(item.rotulo)}</span>
        <span class="meta-recente-item__titulo">${esc(item.titulo)}</span>
        <span class="meta-recente-item__detalhe">${item.percentual}% concluído</span>
      </div>
      <a class="btn btn--secundario btn--pequeno" href="${item.link}">Ver</a>
    </div>`;
  }).join('');
}

