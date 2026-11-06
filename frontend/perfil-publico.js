document.addEventListener('DOMContentLoaded', function () {
  const eu = exigirLogin();
  if (!eu) return;

  const idPerfil = new URLSearchParams(window.location.search).get('id');
  if (!idPerfil) {
    window.location.href = 'busca.html';
    return;
  }
  if (Number(idPerfil) === Number(eu.id)) {
    window.location.href = 'perfil.html';
    return;
  }

  carregarPerfilPublico(idPerfil);
});

async function carregarPerfilPublico(idPerfil) {
  try {
    const resposta = await api('/usuarios/' + idPerfil);
    if (!resposta.ok) {
      document.getElementById('cartaoNaoEncontrado').hidden = false;
      return;
    }
    const usuario = await resposta.json();
    renderizarPerfilPublico(usuario);
    carregarPosicaoNoRanking(idPerfil);
    carregarMedalhas(idPerfil);
  } catch (erro) {
    mostrarFalhaDeCarregamento(function () { carregarPerfilPublico(idPerfil); });
  }
}

function renderizarPerfilPublico(usuario) {
  document.title = 'FitBattle - ' + usuario.nome;
  document.getElementById('cartaoPerfilPublico').hidden = false;

  const novoAvatar = criarAvatar(usuario, { tamanho: 'grande' });
  novoAvatar.id = 'avatarPublico';
  document.getElementById('avatarPublico').replaceWith(novoAvatar);

  document.getElementById('nomePublico').textContent = usuario.nome;
  document.getElementById('cidadePublica').textContent = [usuario.cidade, usuario.estado].filter(Boolean).join(' - ');
  document.getElementById('nivelPublico').textContent = NOMES_NIVEL[usuario.nivel] || usuario.nivel;
  document.getElementById('xpPublico').textContent = usuario.xp + ' XP';
  document.getElementById('descricaoPublica').textContent = usuario.descricao || '';
}

async function carregarMedalhas(idPerfil) {
  const secao = document.getElementById('cartaoMedalhas');
  try {
    const resposta = await api('/usuarios/' + idPerfil + '/medalhas');
    if (!resposta.ok) {
      secao.hidden = true;
      return;
    }
    renderizarMedalhas(document.getElementById('listaMedalhasPublicas'), await resposta.json(), { compartilhavel: false });
    secao.hidden = false;
  } catch (erro) {
    mostrarFalhaDeCarregamento(function () { carregarPerfilPublico(idPerfil); });
  }
}

async function carregarPosicaoNoRanking(idPerfil) {
  try {
    const resposta = await api('/usuarios/' + idPerfil + '/ranking');
    if (!resposta.ok) return;
    const dados = await resposta.json();
    if (dados.global) {
      document.getElementById('posicaoGlobalPublica').textContent = '#' + dados.global.posicao;
    }
    if (dados.regional) {
      document.getElementById('posicaoRegionalPublica').textContent = '#' + dados.regional.posicao;
    }
  } catch (erro) {}
}
