let usuarioLogado = null;
let meusGruposCarregados = null;

document.addEventListener('DOMContentLoaded', function () {
  usuarioLogado = exigirLogin();
  if (!usuarioLogado) return;

  document.getElementById('abaPerfis').addEventListener('click', function () { selecionarAba('perfis'); });
  document.getElementById('abaGrupos').addEventListener('click', function () { selecionarAba('grupos'); });

  configurarBuscaPerfis();
  configurarBuscaGrupos();
  configurarEntrarPorCodigo();
});

function selecionarAba(aba) {
  const perfis = aba === 'perfis';
  document.getElementById('abaPerfis').classList.toggle('aba--ativa', perfis);
  document.getElementById('abaPerfis').setAttribute('aria-selected', String(perfis));
  document.getElementById('abaGrupos').classList.toggle('aba--ativa', !perfis);
  document.getElementById('abaGrupos').setAttribute('aria-selected', String(!perfis));
  document.getElementById('painelPerfis').hidden = !perfis;
  document.getElementById('painelGrupos').hidden = perfis;

  if (!perfis && meusGruposCarregados === null) {
    carregarMeusGrupos();
  }
}

function configurarBuscaPerfis() {
  const campo = document.getElementById('campoBuscaPerfis');
  const resultados = document.getElementById('resultadosPerfis');
  let temporizador = null;
  let sequencia = 0;

  function mostrarAviso(texto) {
    resultados.innerHTML = '<li class="busca__aviso">' + esc(texto) + '</li>';
  }

  function abrirPerfil(usuario) {
    if (Number(usuario.id) === Number(usuarioLogado.id)) {
      window.location.href = 'perfil.html';
    } else {
      window.location.href = 'perfil-publico.html?id=' + usuario.id;
    }
  }

  function mostrarResultados(usuarios) {
    if (usuarios.length === 0) return mostrarAviso('Nenhum atleta encontrado.');
    resultados.innerHTML = usuarios.map(function (u) {
      const detalhe = [nomeNivel(u), u.cidade].filter(Boolean).join(' • ');
      return '<li><button type="button" class="busca__item" data-id="' + u.id + '">' +
        '<span class="avatar avatar--pequeno">' + esc(iniciais(u.nome)) + '</span>' +
        '<span><span class="busca__nome">' + esc(u.nome) + '</span>' +
        '<span class="busca__detalhe">' + esc(detalhe) + '</span></span>' +
        '</button></li>';
    }).join('');
    resultados.querySelectorAll('[data-id]').forEach(function (botao) {
      const usuario = usuarios.find(function (u) { return String(u.id) === botao.getAttribute('data-id'); });
      botao.addEventListener('click', function () { abrirPerfil(usuario); });
    });
  }

  async function buscar(termo) {
    const minha = ++sequencia;
    try {
      const resposta = await api('/usuarios/busca?nome=' + encodeURIComponent(termo));
      if (minha !== sequencia) return;
      if (!resposta.ok) return mostrarAviso('Não foi possível buscar agora.');
      mostrarResultados(await resposta.json());
    } catch (erro) {
      if (minha === sequencia) mostrarFalhaDeCarregamento(function () { buscar(termo); });
    }
  }

  campo.addEventListener('input', function () {
    clearTimeout(temporizador);
    const termo = campo.value.trim();
    if (termo.length < 2) {
      resultados.innerHTML = '';
      return;
    }
    temporizador = setTimeout(function () { buscar(termo); }, 300);
  });
}

async function carregarMeusGrupos() {
  const lista = document.getElementById('resultadosGrupos');
  lista.innerHTML = '<p class="estado-vazio">Carregando seus grupos...</p>';
  try {
    const resposta = await api('/grupos');
    const grupos = await resposta.json();
    if (!resposta.ok) {
      lista.innerHTML = '<p class="estado-vazio">Não foi possível carregar seus grupos.</p>';
      return;
    }
    meusGruposCarregados = grupos;
    renderizarGrupos(grupos);
  } catch (erro) {
    lista.innerHTML = '';
    mostrarFalhaDeCarregamento(carregarMeusGrupos);
  }
}

function renderizarGrupos(grupos) {
  const lista = document.getElementById('resultadosGrupos');
  if (grupos.length === 0) {
    lista.innerHTML = '<p class="estado-vazio">Você ainda não é membro de nenhum grupo.</p>';
    return;
  }
  lista.innerHTML = grupos.map(function (grupo) {
    return '<article class="card grupo-cartao">' +
      '<span class="grupo-cartao__icone" aria-hidden="true">' + esc(iniciais(grupo.nome)) + '</span>' +
      '<div class="grupo-cartao__corpo">' +
        '<div class="grupo-cartao__nome">' + esc(grupo.nome) + '</div>' +
        (grupo.descricao ? '<div class="grupo-cartao__descricao">' + esc(grupo.descricao) + '</div>' : '') +
        '<div class="grupo-cartao__rodape">' +
          '<span></span>' +
          '<a class="btn btn--secundario btn--pequeno" href="grupo-detalhes.html?id=' + grupo.id + '">Acessar Grupo</a>' +
        '</div>' +
      '</div>' +
    '</article>';
  }).join('');
}

function configurarBuscaGrupos() {
  document.getElementById('campoBuscaGrupos').addEventListener('input', function () {
    if (meusGruposCarregados === null) return;
    const termo = this.value.trim().toLowerCase();
    const filtrados = termo
      ? meusGruposCarregados.filter(function (g) { return g.nome.toLowerCase().includes(termo); })
      : meusGruposCarregados;
    renderizarGrupos(filtrados);
  });
}

function configurarEntrarPorCodigo() {
  document.getElementById('formEntrarCodigo').addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const erro = document.getElementById('erroEntrarCodigo');
    const codigo = document.getElementById('campoCodigoConvite').value.trim();
    erro.textContent = '';
    try {
      const resposta = await api('/grupos/entrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo: codigo })
      });
      const dados = await resposta.json();
      if (!resposta.ok) {
        erro.textContent = dados.erro || 'Não foi possível entrar no grupo.';
        return;
      }
      window.location.href = 'grupo-detalhes.html?id=' + dados.grupo.id;
    } catch (e) {
      erro.textContent = 'Não foi possível falar com o servidor. Tente novamente.';
    }
  });
}
