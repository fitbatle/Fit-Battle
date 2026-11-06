let idDesafio = null;
let desafioAtual = null;
let usuarioEhAdminDetalhe = false;

document.addEventListener('DOMContentLoaded', function () {
  const usuarioLogado = exigirLogin();
  if (!usuarioLogado) return;

  idDesafio = new URLSearchParams(window.location.search).get('id');
  if (!idDesafio) {
    window.location.href = 'metas.html';
    return;
  }

  document.getElementById('btnParticiparDetalhe').addEventListener('click', participar);
  document.getElementById('btnDesistirDetalhe').addEventListener('click', desistir);
  document.getElementById('btnEncerrarDetalhe').addEventListener('click', encerrar);

  inicializarAdmin();
  carregarDesafio();
});

async function inicializarAdmin() {
  try {
    const usuario = await usuarioAtual();
    usuarioEhAdminDetalhe = !!(usuario && usuario.admin);
    document.getElementById('btnEncerrarDetalhe').hidden = !usuarioEhAdminDetalhe;
  } catch (e) {}
}

async function carregarDesafio() {
  try {
    const resposta = await api('/desafios/' + idDesafio);
    const desafio = await resposta.json();
    if (!resposta.ok) {
      mostrarToast(desafio.erro || 'Não foi possível carregar o desafio.');
      window.location.href = 'metas.html';
      return;
    }
    desafioAtual = desafio;
    renderizar(desafio);
  } catch (e) {
    mostrarFalhaDeCarregamento(carregarDesafio);
  }
}

function unidade(desafio) {
  return desafio.tipo_metrica === 'carga_maxima' ? 'kg' : 'treinos';
}

function rotuloStatus(status) {
  if (status === 'concluido') return montarComIcone('check', 'Concluído');
  if (status === 'desistiu') return [document.createTextNode('Você desistiu')];
  if (status === 'inscrito') return [document.createTextNode('● Em Andamento')];
  return [document.createTextNode('Não inscrito')];
}

function renderizar(desafio) {
  document.title = 'FitBattle - ' + desafio.nome;
  const un = unidade(desafio);
  const inscricao = desafio.minha_inscricao;
  const status = inscricao.status;

  const tags = [`<span class="badge">${desafio.tipo_metrica === 'carga_maxima' ? 'Carga Máxima' : 'Treinos'}</span>`];
  if (desafio.exercicio) tags.push(`<span class="badge">${esc(desafio.exercicio)}</span>`);
  document.getElementById('desafioTags').innerHTML = tags.join('');

  document.getElementById('desafioTitulo').textContent = desafio.nome;
  document.getElementById('desafioInfo').textContent =
    'De ' + formatarData(desafio.data_inicio) + ' até ' + formatarData(desafio.data_fim);
  document.getElementById('desafioDescricao').textContent = desafio.descricao || '';

  document.getElementById('btnParticiparDetalhe').hidden = !(status === null || status === 'desistiu');
  document.getElementById('btnParticiparDetalhe').textContent = status === 'desistiu' ? 'Participar de novo' : 'Participar';
  document.getElementById('btnDesistirDetalhe').hidden = status !== 'inscrito';

  document.getElementById('statAtualRotuloDesafio').textContent =
    desafio.tipo_metrica === 'carga_maxima' ? 'Carga Atual' : 'Treinos Realizados';
  document.getElementById('statAtualDesafio').textContent = formatarNumero(inscricao.valor_atual) + ' ' + un;
  document.getElementById('statObjetivoDesafio').textContent = formatarNumero(desafio.valor_objetivo) + ' ' + un;
  document.getElementById('statRecompensaDesafio').textContent = desafio.recompensa_xp ? '+' + desafio.recompensa_xp + ' XP' : 'Sem recompensa';
  document.getElementById('statStatusDesafio').replaceChildren(...rotuloStatus(status));

  document.getElementById('progressoPercentualTextoDesafio').textContent = inscricao.percentual + '% concluído';
  document.getElementById('barraProgressoDesafio').style.width = inscricao.percentual + '%';
  document.getElementById('calloutProgressoDesafio').textContent = status === null
    ? 'Participe para começar a acompanhar seu progresso neste desafio.'
    : (formatarNumero(inscricao.valor_atual) + ' de ' + formatarNumero(desafio.valor_objetivo) + ' ' + un + ' até agora.');
}

async function participar() {
  try {
    const resposta = await api('/desafios/' + idDesafio + '/participar', { method: 'POST' });
    const dados = await resposta.json();
    if (!resposta.ok) { mostrarToast(dados.erro || 'Não foi possível participar.'); return; }
    mostrarToast('Inscrição confirmada!');
    carregarDesafio();
  } catch (e) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}

async function desistir() {
  try {
    const resposta = await api('/desafios/' + idDesafio + '/participar', { method: 'DELETE' });
    const dados = await resposta.json();
    if (!resposta.ok) { mostrarToast(dados.erro || 'Não foi possível desistir.'); return; }
    mostrarToast('Você desistiu do desafio.');
    carregarDesafio();
  } catch (e) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}

async function encerrar() {
  if (!window.confirm('Encerrar este desafio agora?')) return;
  try {
    const resposta = await api('/desafios/' + idDesafio + '/encerrar', { method: 'PUT' });
    if (!resposta.ok) { mostrarToast('Não foi possível encerrar.'); return; }
    mostrarToast('Desafio encerrado.');
    carregarDesafio();
  } catch (e) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}

function formatarData(iso) {
  if (!iso) return '—';
  return new Date(iso + (iso.length === 10 ? 'T00:00:00' : '')).toLocaleDateString('pt-BR');
}

function formatarNumero(n) {
  return Number(n).toString().replace('.', ',');
}
