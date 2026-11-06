document.addEventListener('DOMContentLoaded', function () {
  const usuario = exigirLogin();
  if (!usuario) return;

  document.getElementById('btnMarcarTodasLidas').addEventListener('click', marcarTodasComoLidas);
  carregarNotificacoes();
});

function formatarDataHora(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('pt-BR');
}

async function carregarNotificacoes() {
  const lista = document.getElementById('listaNotificacoes');
  try {
    const resposta = await api('/notificacoes');
    if (!resposta.ok) {
      lista.innerHTML = '<p class="estado-vazio">Não foi possível carregar as notificações.</p>';
      return;
    }
    renderizarNotificacoes(await resposta.json());
  } catch (erro) {
    lista.innerHTML = '';
    mostrarFalhaDeCarregamento(carregarNotificacoes);
  }
}

function renderizarNotificacoes(notificacoes) {
  const lista = document.getElementById('listaNotificacoes');
  if (notificacoes.length === 0) {
    lista.innerHTML = '<p class="estado-vazio">Você ainda não tem notificações.</p>';
    return;
  }
  lista.innerHTML = notificacoes.map(function (notificacao) {
    return '<div class="notificacao-card' + (notificacao.lida ? '' : ' notificacao-card--nao-lida') +
      '" data-id="' + notificacao.id + '" data-tipo-alvo="' + (notificacao.tipo_alvo || '') +
      '" data-id-alvo="' + (notificacao.id_alvo || '') + '">' +
      '<p>' + esc(notificacao.mensagem) + '</p>' +
      '<span class="rotulo-mini">' + formatarDataHora(notificacao.data_envio) + '</span>' +
      '</div>';
  }).join('');
  lista.querySelectorAll('.notificacao-card').forEach(function (card) {
    card.addEventListener('click', function () { abrirNotificacao(card); });
  });
}

async function abrirNotificacao(card) {
  const id = card.getAttribute('data-id');
  try {
    await api('/notificacoes/' + id + '/lida', { method: 'PUT' });
  } catch (erro) {}
  const tipoAlvo = card.getAttribute('data-tipo-alvo');
  const idAlvo = card.getAttribute('data-id-alvo');
  const destino = destinoDaNotificacao(tipoAlvo, idAlvo);
  if (destino) {
    window.location.href = destino;
  } else {
    carregarNotificacoes();
  }
}

async function marcarTodasComoLidas() {
  try {
    await api('/notificacoes/lidas', { method: 'PUT' });
    carregarNotificacoes();
  } catch (erro) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}
