const TAMANHO_MAX_FOTO = 3 * 1024 * 1024;

const ICONE_TIPO = {
  musculacao: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6v12M18 6v12M3 9v6M21 9v6M6 12h12"/></svg>',
  cardio: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 5.6a5 5 0 0 0-7.1 0L12 7.3l-1.7-1.7a5 5 0 0 0-7.1 7.1L12 21.5l8.8-8.8a5 5 0 0 0 0-7.1z"/></svg>',
  yoga: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="5" r="2"/><path d="M12 8v5M7 13h10M9 21l3-8 3 8"/></svg>',
  outro: '<svg viewBox="0 0 24 24" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
};
const ICONE_EDITAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>';
const ICONE_FECHAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
const ICONE_COMPARTILHAR = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>';
const ICONE_LIXEIRA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';
const NOME_TIPO = {
  musculacao: 'Musculação',
  cardio: 'Cardio',
  yoga: 'Yoga',
  outro: 'Outro'
};

let usuarioLogado = null;
let fotoSelecionada = null;

function dataDeHoje() {
  const hoje = new Date();
  const mes = String(hoje.getMonth() + 1).padStart(2, '0');
  const dia = String(hoje.getDate()).padStart(2, '0');
  return hoje.getFullYear() + '-' + mes + '-' + dia;
}

function calcularIdade(dataStr) {
  if (!dataStr) return null;
  const [ano, mes, dia] = dataStr.split('-').map(Number);
  const hoje = new Date();
  let idade = hoje.getFullYear() - ano;
  const aniversarioJaPassou =
    hoje.getMonth() + 1 > mes || (hoje.getMonth() + 1 === mes && hoje.getDate() >= dia);
  if (!aniversarioJaPassou) idade--;
  return idade;
}

function emailFoiAlterado() {
  return document.getElementById('editEmail').value.trim() !== (usuarioLogado.email || '');
}

function atualizarCampoSenhaAtual() {
  const alterado = emailFoiAlterado();
  document.getElementById('campoSenhaAtual').hidden = !alterado;
  if (!alterado) document.getElementById('editSenhaAtual').value = '';
}

function atualizarIdadeNoPerfil() {
  const dataNascimento = document.getElementById('editDataNascimento');
  const idadeCalculada = calcularIdade(dataNascimento.value);
  const dica = document.getElementById('editIdadeAtual');
  dica.textContent = idadeCalculada != null ? 'Idade: ' + idadeCalculada + ' anos' : '';
}

document.addEventListener('DOMContentLoaded', function () {
  usuarioLogado = exigirLogin();
  if (!usuarioLogado) return;

  configurarModais();
  configurarAvatar();
  configurarRanking();
  configurarAlterarSenha();

  carregarTudo();
});

function configurarAlterarSenha() {
  const formulario = document.getElementById('formSenha');
  const erro = document.getElementById('erroSenha');
  const botao = document.getElementById('btnAlterarSenha');

  formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    erro.textContent = '';
    erro.classList.remove('mensagem-form--ok');

    const senhaNova = document.getElementById('senhaNova').value;
    if (senhaNova !== document.getElementById('senhaConfirmacao').value) {
      erro.textContent = 'A confirmação não confere com a nova senha.';
      return;
    }

    botao.disabled = true;
    try {
      const resposta = await api('/usuarios/' + usuarioLogado.id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          senha: senhaNova,
          senha_atual: document.getElementById('senhaAtual').value
        })
      });
      const dados = await resposta.json().catch(function () { return {}; });
      if (!resposta.ok) {
        erro.textContent = dados.erro || 'Não foi possível alterar a senha.';
        return;
      }
      atualizarTokenDaSessao(dados.token);
      formulario.reset();
      erro.textContent = 'Senha alterada.';
      erro.classList.add('mensagem-form--ok');
    } catch (e) {
      erro.textContent = 'Não foi possível falar com o servidor. Tente novamente.';
    } finally {
      botao.disabled = false;
    }
  });
}

async function carregarTudo() {
  await carregarPerfil(false);
  carregarTreinos();
  carregarRankingLocal();
  carregarMedalhas();
}

async function carregarMedalhas() {
  const lista = document.getElementById('listaMedalhas');
  try {
    const resposta = await api(`/usuarios/${usuarioLogado.id}/medalhas`);
    if (!resposta.ok) throw new Error('falha');
    renderizarMedalhas(lista, await resposta.json(), { compartilhavel: true });
  } catch (e) {
    mostrarFalhaDeCarregamento(carregarTudo);
  }
}

function configurarAvatar() {
  ligar('avatarLarge', 'click', function () {
    if (usuarioLogado && usuarioLogado.foto) {
      document.getElementById('fotoAmpliada').src = urlFoto(usuarioLogado.foto);
      abrirOverlay('overlayFoto');
    } else {
      abrirEditarPerfil();
    }
  });

  ligar('closeFoto', 'click', function () { fecharOverlay('overlayFoto'); });
  ligar('btnTrocarFoto', 'click', function () {
    fecharOverlay('overlayFoto');
    abrirEditarPerfil();
  });
}

async function carregarPerfil(recarregar) {
  try {
    usuarioLogado = await usuarioAtual(recarregar);
    preencherPerfil(usuarioLogado);
  } catch (e) {
    mostrarFalhaDeCarregamento(carregarTudo);
  }
}

function preencherPerfil(u) {
  texto('pNome', u.nome);
  texto('pHandle', '@' + (u.email ? u.email.split('@')[0] : 'usuario'));
  texto('pLocal', u.cidade || 'Localização não informada');
  texto('pBio', u.descricao || '');
  texto('pPeso', u.peso ? formatarNumero(u.peso) + ' kg' : '—');
  texto('pAltura', u.altura ? formatarNumero(u.altura) + ' m' : '—');
  texto('pIdade', u.idade != null ? u.idade : '—');

  aplicarFotoOuIniciais('avatarLarge', u);

  const progresso = u.progresso_nivel;
  texto('levelNome', NOMES_NIVEL[progresso.nivel] || progresso.nivel);
  document.getElementById('levelBar').style.width = progresso.percentual + '%';
  document.getElementById('levelFooter').textContent = progresso.xp_faltante > 0
    ? `Faltam ${progresso.xp_faltante} xp para o próximo nível.`
    : 'Nível máximo alcançado.';
}

async function carregarTreinos() {
  try {
    const resposta = await api(`/usuarios/${usuarioLogado.id}/atividades`);
    if (!resposta.ok) throw new Error('falha');
    const treinos = await resposta.json();
    renderizarTreinos(treinos);

    document.getElementById('statTreinos').textContent = treinos.length;
    const respostaDashboard = await api('/dashboard');
    if (!respostaDashboard.ok) throw new Error('falha');
    const dashboard = await respostaDashboard.json();
    document.getElementById('statSequencia').textContent = dashboard.sequencia_atual + 'd';
  } catch (e) {
    mostrarFalhaDeCarregamento(carregarTudo);
  }
}

async function carregarRankingLocal() {
  try {
    const resposta = await api(`/usuarios/${usuarioLogado.id}/ranking`);
    if (!resposta.ok) return;
    const dados = await resposta.json();
    const pos = dados.regional && dados.regional.posicao;
    document.getElementById('statRanking').textContent = pos ? pos + 'º' : '—';
  } catch (e) {
    mostrarFalhaDeCarregamento(carregarTudo);
  }
}

function renderizarTreinos(treinos) {
  const lista = document.getElementById('listaTreinos');
  const vazia = document.getElementById('listaVazia');

  lista.querySelectorAll('.activity-card').forEach(function (el) { el.remove(); });

  if (treinos.length === 0) {
    vazia.hidden = false;
    return;
  }
  vazia.hidden = true;

  treinos.forEach(function (t) {
    lista.insertAdjacentHTML('beforeend', htmlCardTreino(t));
  });

  lista.querySelectorAll('[data-excluir]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      excluirTreino(botao.getAttribute('data-excluir'));
    });
  });

  lista.querySelectorAll('[data-compartilhar]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      abrirCompartilhar({
        tipoConteudo: 'atividade',
        idAtividade: botao.getAttribute('data-compartilhar-id'),
        texto: botao.getAttribute('data-compartilhar')
      });
    });
  });
}

function htmlCardTreino(t) {
  const icone = ICONE_TIPO[t.tipo] || ICONE_TIPO.outro;
  const nomeTipo = NOME_TIPO[t.tipo] || capitalizar(t.tipo);
  const titulo = nomeTipo + (t.titulo ? ': ' + esc(t.titulo).toUpperCase() : '');

  const metricas = [];
  if (t.tempo_min != null) {
    const dur = partesDuracao(t.tempo_min);
    metricas.push(metrica(dur.v, dur.u, 'Duração'));
  }
  if (t.carga_kg != null) metricas.push(metrica(formatarNumero(t.carga_kg), 'kg', 'Carga máx.'));
  if (t.repeticoes != null) metricas.push(metrica(t.repeticoes, '', 'Séries / reps'));
  if (t.distancia_km != null) {
    const dist = partesDistancia(t.distancia_km);
    metricas.push(metrica(dist.v, dist.u, 'Distância'));
  }

  return `
    <div class="activity-card">
      <div class="activity-title"><span class="perfil-icone">${icone}</span>${titulo}
        <span class="activity-time">${dataRelativa(t.data_registro)}</span>
      </div>
      <div class="activity-desc">${esc(t.descricao || '')}</div>
      <div class="activity-metrics">${metricas.join('')}</div>
      <div class="card-actions">
        <button class="btn btn--fantasma btn--pequeno" data-compartilhar="${esc('Registrei um treino de ' + nomeTipo + (t.titulo ? ' (' + t.titulo + ')' : '') + ' no FitBattle! #FitBattle')}" data-compartilhar-id="${t.id}"><span class="perfil-icone">${ICONE_COMPARTILHAR}</span>Compartilhar</button>
        <button class="btn btn--fantasma btn--pequeno perfil-acao-excluir" data-excluir="${t.id}"><span class="perfil-icone">${ICONE_LIXEIRA}</span>Excluir</button>
      </div>
    </div>`;
}

function metrica(valor, unidade, rotulo) {
  return `<div class="metric-box">
    <div class="m-val">${valor} <span>${unidade}</span></div>
    <div class="m-lbl">${rotulo}</div>
  </div>`;
}

async function excluirTreino(id) {
  if (!confirm('Excluir este treino? A pontuação dele será descontada.')) return;
  try {
    const resposta = await api(`/atividades/${id}`, { method: 'DELETE' });
    if (!resposta.ok) throw new Error('falha');
    mostrarToast('Treino excluído.');
    carregarPerfil(true);
    carregarTreinos();
    carregarRankingLocal();
  } catch (e) {
    mostrarToast('Não foi possível excluir o treino.');
  }
}

function abrirNovoTreino() {
  document.getElementById('formTreino').reset();
  document.getElementById('erroTreino').textContent = '';
  ajustarCamposTreino();
  abrirOverlay('overlayTreino');
}

function ajustarCamposTreino() {
  const tipo = document.getElementById('treinoTipo').value;
  const mostraForca = (tipo === 'musculacao' || tipo === 'outro');
  const mostraDist = (tipo === 'cardio' || tipo === 'outro');
  document.getElementById('linhaForca').hidden = !mostraForca;
  document.getElementById('campoDist').hidden = !mostraDist;
}

function configurarModais() {
  ligar('btnNovoTreino', 'click', abrirNovoTreino);
  ligar('treinoTipo', 'change', ajustarCamposTreino);
  ligar('closeTreino', 'click', function () { fecharOverlay('overlayTreino'); });
  ligar('btnEditarPerfil', 'click', abrirEditarPerfil);
  document.getElementById('iconeEditar').innerHTML = ICONE_EDITAR;
  document.querySelectorAll('.modal-close').forEach(function (botao) { botao.innerHTML = ICONE_FECHAR; });
  ligar('closePerfil', 'click', function () { fecharOverlay('overlayPerfil'); });
  document.getElementById('editDataNascimento').max = dataDeHoje();
  ligar('editDataNascimento', 'input', atualizarIdadeNoPerfil);
  ligar('editEmail', 'input', atualizarCampoSenhaAtual);

  ligar('fotoBtn', 'click', function () { document.getElementById('fotoInput').click(); });
  ligar('fotoInput', 'change', function () {
    const arquivo = this.files && this.files[0];
    if (!arquivo) return;
    if (arquivo.size > TAMANHO_MAX_FOTO) {
      document.getElementById('erroPerfil').textContent = 'A imagem deve ter no máximo 3 MB.';
      this.value = '';
      return;
    }
    fotoSelecionada = arquivo;
    document.getElementById('erroPerfil').textContent = '';
    document.getElementById('fotoNome').textContent = arquivo.name;
    document.getElementById('avatarPreview').style.backgroundImage =
      'url("' + URL.createObjectURL(arquivo) + '")';
  });

  document.querySelectorAll('.overlay').forEach(function (ov) {
    ov.addEventListener('click', function (e) {
      if (e.target === ov) ov.classList.remove('aberto');
    });
  });

  document.getElementById('formTreino').addEventListener('submit', async function (e) {
    e.preventDefault();
    const erro = document.getElementById('erroTreino');
    erro.textContent = '';

    const titulo = document.getElementById('treinoTitulo').value.trim();

    const horas = numero(document.getElementById('treinoHoras').value) || 0;
    const minutos = numero(document.getElementById('treinoMinutos').value) || 0;
    if (minutos < 0 || minutos > 59) {
      erro.textContent = 'Os minutos devem ser de 0 a 59.';
      return;
    }
    if (horas < 0) { erro.textContent = 'Duração inválida.'; return; }
    const tempoMin = (horas * 60 + minutos) || null;

    const km = numero(document.getElementById('treinoKm').value) || 0;
    const metros = numero(document.getElementById('treinoMetros').value) || 0;
    if (metros < 0 || metros > 999) {
      erro.textContent = 'Os metros devem ser de 0 a 999.';
      return;
    }
    if (km < 0) { erro.textContent = 'Distância inválida.'; return; }
    const distanciaKm = (km + metros / 1000) || null;

    if (titulo === '') { erro.textContent = 'Informe o título do treino.'; return; }
    if (!tempoMin && !distanciaKm) {
      erro.textContent = 'Informe ao menos a duração ou a distância.';
      return;
    }

    const corpo = {
      tipo: document.getElementById('treinoTipo').value,
      titulo: titulo,
      descricao: document.getElementById('treinoDesc').value.trim(),
      tempo_min: tempoMin,
      carga_kg: numero(document.getElementById('treinoCarga').value),
      repeticoes: numero(document.getElementById('treinoReps').value),
      distancia_km: distanciaKm
    };

    try {
      const resposta = await api(`/usuarios/${usuarioLogado.id}/atividades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(corpo)
      });
      const dados = await resposta.json();
      if (!resposta.ok) { erro.textContent = dados.erro || 'Não foi possível registrar.'; return; }

      fecharOverlay('overlayTreino');
      e.target.reset();
      mostrarToast('Treino registrado! +' + dados.pontuacao_ganha + ' xp');
      carregarPerfil(true);
      carregarTreinos();
      carregarRankingLocal();
    } catch (err) {
      erro.textContent = 'Não foi possível falar com o servidor. Tente novamente.';
    }
  });

  document.getElementById('formPerfil').addEventListener('submit', async function (e) {
    e.preventDefault();
    const erro = document.getElementById('erroPerfil');
    erro.textContent = '';

    const dataNascimento = document.getElementById('editDataNascimento').value || null;
    const corpo = {
      nome: document.getElementById('editNome').value.trim(),
      email: document.getElementById('editEmail').value.trim(),
      descricao: document.getElementById('editBio').value.trim(),
      data_nascimento: dataNascimento,
      cidade: document.getElementById('editCidade').value.trim() || null,
      peso: document.getElementById('editPeso').value || null,
      altura: document.getElementById('editAltura').value || null
    };
    if (emailFoiAlterado()) corpo.senha_atual = document.getElementById('editSenhaAtual').value;

    try {
      const resposta = await api(`/usuarios/${usuarioLogado.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(corpo)
      });
      const dados = await resposta.json();
      if (!resposta.ok) { erro.textContent = dados.erro || 'Não foi possível salvar.'; return; }
      document.getElementById('editSenhaAtual').value = '';

      if (fotoSelecionada) {
        const fd = new FormData();
        fd.append('foto', fotoSelecionada);
        const rFoto = await api(`/usuarios/${usuarioLogado.id}/foto`, {
          method: 'POST',
          body: fd
        });
        const dFoto = await rFoto.json().catch(function () { return {}; });
        if (!rFoto.ok) {
          erro.textContent = dFoto.erro || 'Os dados foram salvos, mas a foto não pôde ser enviada.';
          return;
        }
      }

      carregarPerfil(true);
      carregarRankingLocal();
      fotoSelecionada = null;
      fecharOverlay('overlayPerfil');
      mostrarToast('Perfil atualizado.');
    } catch (err) {
      erro.textContent = 'Não foi possível falar com o servidor. Tente novamente.';
    }
  });
}

function abrirEditarPerfil() {
  const u = usuarioLogado;
  document.getElementById('editNome').value = u.nome || '';
  document.getElementById('editEmail').value = u.email || '';
  atualizarCampoSenhaAtual();
  document.getElementById('editBio').value = u.descricao || '';
  document.getElementById('editDataNascimento').value = u.data_nascimento || '';
  atualizarIdadeNoPerfil();
  document.getElementById('editCidade').value = u.cidade || '';
  document.getElementById('editPeso').value = u.peso != null ? u.peso : '';
  document.getElementById('editAltura').value = u.altura != null ? u.altura : '';
  document.getElementById('erroPerfil').textContent = '';

  fotoSelecionada = null;
  document.getElementById('fotoInput').value = '';
  document.getElementById('fotoNome').textContent = 'JPG, PNG ou WEBP (até 3 MB)';
  aplicarFotoOuIniciais('avatarPreview', u);

  abrirOverlay('overlayPerfil');
}

function sair() {
  encerrarSessao();
}

function configurarRanking() {
  ligar('btnVerRanking', 'click', abrirRanking);
  ligar('closeRanking', 'click', function () { fecharOverlay('overlayRanking'); });

  document.querySelectorAll('.ranking-aba').forEach(function (aba) {
    aba.addEventListener('click', function () {
      document.querySelectorAll('.ranking-aba').forEach(function (a) {
        a.classList.remove('ativa');
      });
      aba.classList.add('ativa');
      carregarRanking(aba.getAttribute('data-escopo'));
    });
  });
}

function abrirRanking() {
  abrirOverlay('overlayRanking');
  const ativa = document.querySelector('.ranking-aba.ativa');
  carregarRanking(ativa ? ativa.getAttribute('data-escopo') : 'regional');
}

async function carregarRanking(escopo) {
  const lista = document.getElementById('rankingLista');
  lista.innerHTML = '<p class="rank-vazio">Carregando...</p>';

  let url;
  if (escopo === 'regional') {
    if (!usuarioLogado.cidade) {
      lista.innerHTML = '<p class="rank-vazio">Informe sua cidade em "Editar perfil" para ver o ranking da sua região.</p>';
      return;
    }
    url = `/ranking/regional?cidade=${encodeURIComponent(usuarioLogado.cidade)}`;
  } else {
    url = '/ranking/global';
  }

  try {
    const resposta = await api(url);
    const dados = await resposta.json();
    if (!resposta.ok) {
      lista.innerHTML = '<p class="rank-vazio">' + esc(dados.erro || 'Não foi possível carregar o ranking.') + '</p>';
      return;
    }
    if (dados.length === 0) {
      lista.innerHTML = '<p class="rank-vazio">Ninguém no ranking ainda.</p>';
      return;
    }
    lista.innerHTML = dados.map(function (r) {
      const eu = r.id_usuario === usuarioLogado.id;
      const cidade = (escopo === 'global' && r.cidade)
        ? '<span class="rank-cidade">' + esc(r.cidade) + '</span>' : '';
      return '<div class="rank-linha' + (eu ? ' eu' : '') + '">' +
        '<span class="rank-pos">' + r.posicao + 'º</span>' +
        '<span class="rank-nome">' + esc(r.nome) + (eu ? ' (você)' : '') + '</span>' +
        cidade +
        '<span class="rank-pts">' + r.pontuacao_total + ' xp</span>' +
        '</div>';
    }).join('');
  } catch (e) {
    lista.innerHTML = '<p class="rank-vazio">Não foi possível falar com o servidor. Tente novamente.</p>';
  }
}

function texto(id, valor) {
  document.getElementById(id).textContent = valor;
}

function ligar(id, evento, fn) {
  const el = document.getElementById(id);
  if (el) el.addEventListener(evento, fn);
}


function aplicarFotoOuIniciais(id, usuario) {
  const el = document.getElementById(id);
  if (!el) return;
  if (usuario.foto) {
    aplicarFoto(id, usuario.foto);
    el.textContent = '';
  } else {
    el.style.backgroundImage = 'none';
    el.textContent = iniciais(usuario.nome);
  }
}

function aplicarFoto(id, url) {
  const el = document.getElementById(id);
  if (!el) return;
  const src = urlFoto(url);
  el.style.backgroundImage = src ? `url("${src}")` : 'none';
}

function abrirOverlay(id) { document.getElementById(id).classList.add('aberto'); }
function fecharOverlay(id) { document.getElementById(id).classList.remove('aberto'); }


function capitalizar(s) {
  if (!s) return '';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function formatarNumero(n) {
  return Number(n).toString().replace('.', ',');
}

function numero(valor) {
  if (valor === null || valor === undefined || String(valor).trim() === '') return null;
  const n = parseFloat(String(valor).replace(',', '.'));
  return isNaN(n) ? null : n;
}

function partesDuracao(min) {
  min = Number(min);
  if (min < 60) return { v: String(min), u: 'min' };
  const horas = Math.floor(min / 60);
  const resto = min % 60;
  return { v: resto === 0 ? horas + 'h' : horas + 'h' + String(resto).padStart(2, '0'), u: '' };
}

function partesDistancia(km) {
  const n = Number(km);
  if (n >= 1) return { v: formatarNumero(n), u: 'km' };
  return { v: String(Math.round(n * 1000)), u: 'm' };
}

function diaLocal(data) {
  const ano = data.getFullYear();
  const mes = String(data.getMonth() + 1).padStart(2, '0');
  const dia = String(data.getDate()).padStart(2, '0');
  return `${ano}-${mes}-${dia}`;
}

function dataRelativa(iso) {
  if (!iso) return '';
  const data = new Date(iso);
  const agora = new Date();
  const hora = data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

  if (diaLocal(data) === diaLocal(agora)) return 'Hoje, ' + hora;

  const ontem = new Date();
  ontem.setDate(agora.getDate() - 1);
  if (diaLocal(data) === diaLocal(ontem)) return 'Ontem, ' + hora;

  const dias = Math.floor((agora - data) / (1000 * 60 * 60 * 24));
  if (dias < 30) return `${dias} dias atrás`;
  return data.toLocaleDateString('pt-BR');
}
