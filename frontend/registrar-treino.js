const ATRASO_PREVIA_MS = 300;

let usuarioLogado = null;
let passoAtual = 1;
let exercicioSelecionado = null;
let pesoAtual = 40;
let repeticoesAtual = 6;
let duracaoAtual = 40;
let previaAtual = null;
let erroPrevia = false;
let temporizadorPrevia = null;
let sequenciaPrevia = 0;

document.addEventListener('DOMContentLoaded', function () {
  usuarioLogado = exigirLogin();
  if (!usuarioLogado) return;

  carregarDesafioAtivo();
  configurarExercicios();
  configurarPeso();
  configurarContadores();
  configurarNavegacao();
  configurarSubmissao();

  atualizarPeso();
});

function configurarExercicios() {
  document.querySelectorAll('.rt-exercicio').forEach(function (botao) {
    botao.addEventListener('click', function () { selecionarExercicio(botao); });
  });

  document.getElementById('exercicioCustom').addEventListener('input', function () {
    exercicioSelecionado = this.value.trim();
    agendarPrevia();
  });
}

function selecionarExercicio(botao) {
  document.querySelectorAll('.rt-exercicio').forEach(function (b) { b.classList.remove('rt-exercicio--ativa'); });
  botao.classList.add('rt-exercicio--ativa');

  const valor = botao.getAttribute('data-exercicio');
  const campoOutro = document.getElementById('campoOutroExercicio');

  if (valor === '') {
    campoOutro.hidden = false;
    const custom = document.getElementById('exercicioCustom');
    custom.focus();
    exercicioSelecionado = custom.value.trim();
  } else {
    campoOutro.hidden = true;
    exercicioSelecionado = valor;
  }

  document.getElementById('erroEtapa1').textContent = '';
  agendarPrevia();
}

function configurarPeso() {
  document.querySelectorAll('[data-ajuste]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      const delta = parseInt(botao.getAttribute('data-ajuste'), 10);
      pesoAtual = Math.max(0, pesoAtual + delta);
      atualizarPeso();
    });
  });
}

function atualizarPeso() {
  document.getElementById('pesoValor').textContent = formatarNumero(pesoAtual);
  agendarPrevia();
  document.getElementById('lateralCargaAtual').textContent = formatarNumero(pesoAtual) + ' kg';
}

function configurarContadores() {
  document.querySelectorAll('[data-contador]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      const alvo = botao.getAttribute('data-contador');
      const delta = parseInt(botao.getAttribute('data-delta'), 10);
      if (alvo === 'repeticoes') {
        repeticoesAtual = Math.max(1, repeticoesAtual + delta);
        document.getElementById('repeticoesValor').textContent = repeticoesAtual;
      } else {
        duracaoAtual = Math.max(5, duracaoAtual + delta);
        document.getElementById('duracaoValor').textContent = duracaoAtual;
      }
      agendarPrevia();
    });
  });
}

function agendarPrevia() {
  clearTimeout(temporizadorPrevia);
  temporizadorPrevia = setTimeout(pedirPrevia, ATRASO_PREVIA_MS);
}

async function pedirPrevia() {
  const minha = ++sequenciaPrevia;
  try {
    const resposta = await api(`/usuarios/${usuarioLogado.id}/atividades/previa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tipo: 'musculacao',
        titulo: exercicioSelecionado,
        tempo_min: duracaoAtual,
        carga_kg: pesoAtual,
        repeticoes: repeticoesAtual,
        distancia_km: null
      })
    });
    const dados = await resposta.json().catch(function () { return {}; });
    if (minha !== sequenciaPrevia) return;
    if (!resposta.ok) {
      previaAtual = null;
      mostrarErroPrevia(dados.erro || 'Não foi possível calcular a prévia deste treino.');
      return;
    }
    previaAtual = dados;
    mostrarPrevia(dados);
  } catch (erro) {
    if (minha === sequenciaPrevia) mostrarFalhaDeCarregamento(pedirPrevia);
  }
}

function mostrarErroPrevia(texto) {
  erroPrevia = true;
  document.getElementById('recompensaEstimada').textContent = '—';
  document.getElementById('erroEtapa2').textContent = texto;
}

function mostrarPrevia(dados) {
  if (erroPrevia) {
    erroPrevia = false;
    document.getElementById('erroEtapa2').textContent = '';
  }
  document.getElementById('recompensaEstimada').textContent = '≈ +' + dados.pontuacao_estimada + ' xp';

  const painel = document.getElementById('painelRecorde');
  const texto = document.getElementById('textoRecorde');
  const lateralRecorde = document.getElementById('lateralRecordeAtual');

  if (!exercicioSelecionado) {
    texto.textContent = 'Selecione um exercício para ver seu recorde pessoal.';
    painel.classList.remove('rt-recorde--pr');
    lateralRecorde.textContent = '—';
    return;
  }

  lateralRecorde.textContent = dados.recorde_atual != null ? formatarNumero(dados.recorde_atual) + ' kg' : 'Ainda sem registro';
  if (dados.recorde_pessoal && dados.recorde_atual == null) {
    texto.textContent = 'Primeira vez registrando ' + exercicioSelecionado + '! Isso já vira seu recorde pessoal.';
  } else if (dados.recorde_pessoal) {
    texto.textContent = 'Novo recorde pessoal! Seu anterior em ' + exercicioSelecionado + ' era ' + formatarNumero(dados.recorde_atual) + ' kg.';
  } else {
    texto.textContent = 'Seu recorde em ' + exercicioSelecionado + ' é ' + formatarNumero(dados.recorde_atual) + ' kg.';
  }
  painel.classList.toggle('rt-recorde--pr', dados.recorde_pessoal);
}

function configurarNavegacao() {
  document.getElementById('btnProximo').addEventListener('click', avancar);
  document.getElementById('btnVoltar').addEventListener('click', function () { irParaPasso(passoAtual - 1); });
}

function avancar() {
  if (passoAtual === 1) {
    if (!exercicioSelecionado) {
      document.getElementById('erroEtapa1').textContent = 'Escolha um exercício ou digite o nome dele.';
      return;
    }
  }
  if (passoAtual === 2) {
    if (!pesoAtual || pesoAtual <= 0) {
      document.getElementById('erroEtapa2').textContent = 'Informe a carga levantada.';
      return;
    }
    if (!duracaoAtual || duracaoAtual <= 0) {
      document.getElementById('erroEtapa2').textContent = 'Informe a duração do treino.';
      return;
    }
    document.getElementById('erroEtapa2').textContent = '';
    preencherResumo();
  }
  irParaPasso(passoAtual + 1);
}

function preencherResumo() {
  document.getElementById('resumoExercicio').textContent = exercicioSelecionado || '—';
  document.getElementById('resumoCarga').textContent = formatarNumero(pesoAtual) + ' kg';
  document.getElementById('resumoReps').textContent = repeticoesAtual;
  document.getElementById('resumoDuracao').textContent = duracaoAtual + ' min';

  const pontos = previaAtual ? ' (+' + previaAtual.pontuacao_estimada + ' Pontos)' : '';
  document.getElementById('textoBotaoSalvar').textContent = 'Salvar e Compartilhar Treino' + pontos;
}

function irParaPasso(numero) {
  passoAtual = numero;

  ['etapa1', 'etapa2', 'etapa3'].forEach(function (id, indice) {
    document.getElementById(id).classList.toggle('rt-etapa--visivel', indice + 1 === numero);
  });

  [1, 2, 3].forEach(function (n) {
    const indicador = document.getElementById('indicadorPasso' + n);
    indicador.classList.toggle('rt-passo--ativo', n === numero);
    indicador.classList.toggle('rt-passo--feito', n < numero);
  });

  document.getElementById('btnVoltar').hidden = numero === 1;
  document.getElementById('btnProximo').hidden = numero === 3;
  document.getElementById('btnSalvar').hidden = numero !== 3;

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function configurarSubmissao() {
  document.getElementById('formRegistrarTreino').addEventListener('submit', async function (evento) {
    evento.preventDefault();

    const erro = document.getElementById('erroEtapa3');
    erro.textContent = '';
    const botao = document.getElementById('btnSalvar');
    botao.disabled = true;

    const corpo = {
      tipo: 'musculacao',
      titulo: exercicioSelecionado,
      descricao: document.getElementById('treinoDescricao').value.trim(),
      tempo_min: duracaoAtual,
      carga_kg: pesoAtual,
      repeticoes: repeticoesAtual,
      distancia_km: null
    };

    try {
      const resposta = await api(`/usuarios/${usuarioLogado.id}/atividades`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(corpo)
      });
      const dados = await resposta.json();
      if (!resposta.ok) {
        erro.textContent = dados.erro || 'Não foi possível registrar o treino.';
        return;
      }

      botao.hidden = true;

      if (dados.recorde_pessoal) {
        const textoRecorde = 'Bati meu recorde pessoal: ' + formatarNumero(pesoAtual) + 'kg no ' + exercicioSelecionado + ' no FitBattle! #FitBattle';
        const botaoRecorde = document.getElementById('btnCompartilharRecorde');
        botaoRecorde.hidden = false;
        botaoRecorde.onclick = function () {
          abrirCompartilhar({
            tipoConteudo: 'recorde',
            idAtividade: dados.atividade.id,
            texto: textoRecorde
          });
        };
        mostrarToast('Treino registrado! +' + dados.pontuacao_ganha + ' xp. Novo recorde pessoal!');
        return;
      }

      mostrarToast('Treino registrado! +' + dados.pontuacao_ganha + ' xp');
      setTimeout(function () { window.location.href = 'feed.html'; }, 1400);
    } catch (e) {
      erro.textContent = 'Não foi possível falar com o servidor. Tente novamente.';
    } finally {
      botao.disabled = false;
    }
  });
}

function formatarNumero(n) {
  return Number(n).toString().replace('.', ',');
}

async function carregarDesafioAtivo() {
  const area = document.getElementById('desafioAtivoConteudo');
  try {
    const resposta = await api('/desafios');
    if (!resposta.ok) return;
    const desafios = await resposta.json();
    const ativo = desafios.find(function (d) {
      return d.minha_inscricao && d.minha_inscricao.status === 'inscrito';
    });
    if (!ativo) return;
    const progresso = ativo.minha_inscricao;
    const unidade = ativo.tipo_metrica === 'carga_maxima' ? 'kg' : 'treinos';
    area.innerHTML = `
      <p class="rt-desafio-nome">${esc(ativo.nome)}</p>
      <div class="barra"><div class="barra__preenchimento" style="width:${progresso.percentual}%"></div></div>
      <p class="rotulo-mini">${formatarNumero(progresso.valor_atual)} de ${formatarNumero(ativo.valor_objetivo)} ${unidade}</p>
      <p><a href="desafio-detalhes.html?id=${ativo.id}">Ver desafio</a></p>`;
  } catch (erro) {
    mostrarFalhaDeCarregamento(carregarDesafioAtivo);
  }
}
