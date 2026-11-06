const HOST_API = window.location.hostname || 'localhost';
const PORTAS_FRONTEND_DEV = new Set(['5500', '5501']);
const API_URL = window.FITBATTLE_API_URL
  ? window.FITBATTLE_API_URL
  : (PORTAS_FRONTEND_DEV.has(window.location.port)
    ? 'http://' + HOST_API + ':5000/api'
    : window.location.origin + '/api');
const ORIGEM_API = API_URL.replace(/\/api\/?$/, '');
const CHAVE_SESSAO = 'fitbattle_sessao';
const PAGINA_LOGIN = 'login.html';
const PAGINA_INICIAL = 'feed.html';

function armazenamentoDaSessao() {
  try {
    return typeof sessionStorage !== 'undefined' ? sessionStorage : null;
  } catch (e) {
    return null;
  }
}

function lerSessao() {
  const armazenamento = armazenamentoDaSessao();
  if (!armazenamento) return null;
  try {
    const sessao = JSON.parse(armazenamento.getItem(CHAVE_SESSAO));
    return sessao && sessao.token && sessao.id ? sessao : null;
  } catch (e) {
    return null;
  }
}

function gravarSessao(sessao) {
  const armazenamento = armazenamentoDaSessao();
  if (!armazenamento) return;
  try {
    armazenamento.setItem(CHAVE_SESSAO, JSON.stringify(sessao));
  } catch (e) {}
}

function salvarSessao(token, id) {
  limparSessao();
  gravarSessao({ token: token, id: id });
}

function atualizarTokenDaSessao(token) {
  const sessao = lerSessao();
  if (sessao) gravarSessao({ token: token, id: sessao.id });
}

function limparSessao() {
  const armazenamento = armazenamentoDaSessao();
  if (!armazenamento) return;
  try {
    armazenamento.removeItem(CHAVE_SESSAO);
  } catch (e) {}
}

function idDaSessao() {
  const sessao = lerSessao();
  return sessao ? sessao.id : null;
}

function exigirLogin() {
  const sessao = lerSessao();
  if (!sessao) {
    window.location.href = PAGINA_LOGIN;
    return null;
  }
  return { id: sessao.id };
}

function encerrarSessao() {
  limparSessao();
  window.location.href = PAGINA_LOGIN;
}

const MENSAGEM_SEM_CONEXAO = 'Não foi possível falar com o servidor. Tente novamente.';

class ErroDeConexao extends Error {
  constructor() {
    super(MENSAGEM_SEM_CONEXAO);
    this.name = 'ErroDeConexao';
  }
}

async function api(caminho, opcoes) {
  const config = Object.assign({}, opcoes);
  const cabecalhos = Object.assign({}, config.headers);
  const sessao = lerSessao();
  if (sessao) cabecalhos['Authorization'] = 'Bearer ' + sessao.token;
  config.headers = cabecalhos;

  let resposta;
  try {
    resposta = await fetch(API_URL + caminho, config);
  } catch (erro) {
    throw new ErroDeConexao();
  }
  if (resposta.status === 401) encerrarSessao();
  if (resposta.status >= 500) throw new ErroDeConexao();
  return resposta;
}

function mostrarFalhaDeCarregamento(aoTentarDeNovo) {
  document.querySelectorAll('body *').forEach(function (elemento) {
    if (elemento.childElementCount === 0 && /^carregando/i.test(elemento.textContent.trim())) {
      elemento.textContent = /^(H[1-6]|SPAN)$/.test(elemento.tagName) ? 'Indisponível no momento' : MENSAGEM_SEM_CONEXAO;
    }
  });
  let bloco = document.getElementById('falhaDeCarregamento');
  if (bloco) bloco.remove();
  bloco = document.createElement('div');
  bloco.id = 'falhaDeCarregamento';
  bloco.className = 'card card--interno estado-falha';
  bloco.setAttribute('role', 'alert');
  const texto = document.createElement('p');
  texto.textContent = MENSAGEM_SEM_CONEXAO;
  const botao = document.createElement('button');
  botao.type = 'button';
  botao.className = 'btn btn--secundario btn--pequeno';
  botao.textContent = 'Tentar de novo';
  botao.addEventListener('click', function () {
    bloco.remove();
    aoTentarDeNovo();
  });
  bloco.append(texto, botao);
  const principal = document.querySelector('main') || document.body;
  principal.insertBefore(bloco, principal.firstChild);
}

let pedidoUsuarioAtual = null;

function usuarioAtual(recarregar) {
  if (recarregar || !pedidoUsuarioAtual) {
    pedidoUsuarioAtual = api('/eu')
      .then(function (resposta) {
        if (!resposta.ok) throw new ErroDeConexao();
        return resposta.json();
      })
      .then(function (dados) {
        return dados.usuario;
      })
      .catch(function (erro) {
        pedidoUsuarioAtual = null;
        throw erro;
      });
  }
  return pedidoUsuarioAtual;
}

async function usuarioAtualOuFalha(aoTentarDeNovo) {
  try {
    return await usuarioAtual();
  } catch (erro) {
    mostrarFalhaDeCarregamento(aoTentarDeNovo);
    return null;
  }
}

const ESCAPES_HTML = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (caractere) {
    return ESCAPES_HTML[caractere];
  });
}
