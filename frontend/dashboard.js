const NOME_TIPO_DASHBOARD = {
  musculacao: 'Musculação',
  cardio: 'Cardio',
  yoga: 'Yoga',
  outro: 'Outro'
};

document.addEventListener('DOMContentLoaded', function () {
  const usuario = exigirLogin();
  if (!usuario) return;
  carregarDashboardCompleto();
});

async function carregarEmAndamentoDashboard() {
  const container = document.getElementById('listaEmAndamentoDashboard');
  try {
    const [respostaMetas, respostaDesafios] = await Promise.all([api('/metas'), api('/desafios')]);
    const metas = respostaMetas.ok ? await respostaMetas.json() : [];
    const desafios = respostaDesafios.ok ? await respostaDesafios.json() : [];

    const itens = metas
      .filter(function (m) { return m.status === 'em_andamento'; })
      .map(function (m) {
        return { titulo: m.titulo, percentual: m.percentual, link: 'metas-detalhes.html?id=' + m.id, rotulo: 'Meta' };
      })
      .concat(desafios
        .filter(function (d) { return d.minha_inscricao.status === 'inscrito'; })
        .map(function (d) {
          return {
            titulo: d.nome, percentual: d.minha_inscricao.percentual,
            link: 'desafio-detalhes.html?id=' + d.id, rotulo: 'Desafio',
          };
        }));

    if (itens.length === 0) {
      container.innerHTML = '<p class="estado-vazio">Nenhuma meta ou desafio em andamento agora.</p>';
      return;
    }

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
  } catch (e) {
    container.innerHTML = '';
    mostrarFalhaDeCarregamento(carregarDashboardCompleto);
  }
}

function carregarDashboardCompleto() {
  carregarDashboard();
  carregarEmAndamentoDashboard();
}

async function carregarDashboard(exercicio) {
  try {
    const query = exercicio ? '?exercicio=' + encodeURIComponent(exercicio) : '';
    const resposta = await api('/dashboard' + query);
    if (!resposta.ok) {
      mostrarToast('Não foi possível carregar o dashboard.');
      return;
    }
    renderizarDashboard(await resposta.json());
  } catch (erro) {
    mostrarFalhaDeCarregamento(carregarDashboardCompleto);
  }
}

function formatarData(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}

function formatarMinutos(minutos) {
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  if (horas === 0) return resto + ' min';
  return horas + 'h' + (resto ? ' ' + resto + 'min' : '');
}

function rotuloSemana(isoData) {
  const partes = isoData.split('-');
  return partes[2] + '/' + partes[1];
}

function renderizarDashboard(dados) {
  document.getElementById('statTreinos').textContent = dados.totais.treinos;
  document.getElementById('statTempo').textContent = formatarMinutos(dados.totais.tempo_min);
  document.getElementById('statXp').textContent = dados.totais.xp + ' XP';
  document.getElementById('statSequenciaAtual').textContent =
    dados.sequencia_atual + (dados.sequencia_atual === 1 ? ' dia' : ' dias');
  document.getElementById('statMelhorSequencia').textContent =
    dados.melhor_sequencia + (dados.melhor_sequencia === 1 ? ' dia' : ' dias');

  renderizarBarras('graficoXp', dados.xp_por_semana.map(function (s) {
    return { rotulo: rotuloSemana(s.inicio), valor: s.xp };
  }), 'XP', 'Sem XP nas últimas 8 semanas.');

  renderizarBarras('graficoTreinos', dados.treinos_por_semana.map(function (s) {
    return { rotulo: rotuloSemana(s.inicio), valor: s.quantidade };
  }), 'treinos', 'Sem treinos nas últimas 8 semanas.');

  renderizarDistribuicao(dados.distribuicao_por_tipo);
  configurarSeletorExercicio(dados);
  renderizarEvolucaoCarga(dados.evolucao_carga, dados.exercicio_selecionado);
}

function renderizarBarras(idContainer, pontos, unidade, mensagemVazia) {
  const container = document.getElementById(idContainer);
  const semDados = pontos.every(function (p) { return p.valor === 0; });
  if (semDados) {
    container.innerHTML = '<p class="estado-vazio">' + esc(mensagemVazia) + '</p>';
    return;
  }

  const largura = 320;
  const altura = 140;
  const margemBaixo = 20;
  const maximo = Math.max(1, Math.max.apply(null, pontos.map(function (p) { return p.valor; })));
  const larguraBarra = largura / pontos.length;

  let svg = '<svg viewBox="0 0 ' + largura + ' ' + (altura + margemBaixo) +
    '" class="grafico-svg" role="img" aria-label="Gráfico de ' + esc(unidade) + ' por semana">';
  pontos.forEach(function (ponto, indice) {
    const alturaBarra = Math.max((ponto.valor / maximo) * (altura - 10), ponto.valor > 0 ? 2 : 0);
    const x = indice * larguraBarra + larguraBarra * 0.18;
    const larguraReal = larguraBarra * 0.64;
    const y = altura - alturaBarra;
    svg += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + larguraReal.toFixed(1) +
      '" height="' + alturaBarra.toFixed(1) + '" rx="2" class="grafico-barra">' +
      '<title>' + ponto.valor + ' ' + esc(unidade) + '</title></rect>';
    svg += '<text x="' + (x + larguraReal / 2).toFixed(1) + '" y="' + (altura + 14) +
      '" class="grafico-rotulo" text-anchor="middle">' + esc(ponto.rotulo) + '</text>';
  });
  svg += '</svg>';
  container.innerHTML = svg;
}

function renderizarDistribuicao(distribuicao) {
  const container = document.getElementById('graficoDistribuicao');
  const tipos = Object.keys(distribuicao);
  if (tipos.length === 0) {
    container.innerHTML = '<p class="estado-vazio">Nenhum treino registrado ainda.</p>';
    return;
  }
  const total = tipos.reduce(function (soma, tipo) { return soma + distribuicao[tipo]; }, 0);
  const cores = ['destaque', 'sucesso', 'aviso', 'ouro', 'perigo'];
  let html = '<div class="grafico-distribuicao">';
  tipos.forEach(function (tipo, indice) {
    const quantidade = distribuicao[tipo];
    const percentual = Math.round((quantidade / total) * 100);
    html += '<div class="grafico-distribuicao__linha">' +
      '<span class="grafico-distribuicao__rotulo">' + esc(NOME_TIPO_DASHBOARD[tipo] || tipo) + '</span>' +
      '<div class="grafico-distribuicao__fundo"><div class="grafico-distribuicao__barra grafico-distribuicao__barra--' +
      cores[indice % cores.length] + '" style="width:' + percentual + '%"></div></div>' +
      '<span class="grafico-distribuicao__valor">' + quantidade + '</span>' +
      '</div>';
  });
  html += '</div>';
  container.innerHTML = html;
}

function configurarSeletorExercicio(dados) {
  const seletor = document.getElementById('seletorExercicio');
  if (dados.exercicios_disponiveis.length === 0) {
    seletor.hidden = true;
    return;
  }
  seletor.hidden = false;
  seletor.innerHTML = dados.exercicios_disponiveis.map(function (exercicio) {
    const selecionado = exercicio === dados.exercicio_selecionado ? ' selected' : '';
    return '<option value="' + esc(exercicio) + '"' + selecionado + '>' + esc(exercicio) + '</option>';
  }).join('');
  seletor.onchange = function () { carregarDashboard(seletor.value); };
}

function renderizarEvolucaoCarga(pontos, exercicioSelecionado) {
  const container = document.getElementById('graficoCarga');
  if (pontos.length === 0) {
    const mensagem = exercicioSelecionado
      ? 'Sem registros de carga para este exercício.'
      : 'Nenhum treino de musculação com carga registrada ainda.';
    container.innerHTML = '<p class="estado-vazio">' + mensagem + '</p>';
    return;
  }

  const largura = 320;
  const altura = 140;
  const margemBaixo = 20;
  const valores = pontos.map(function (p) { return p.carga_maxima; });
  const minimo = Math.min.apply(null, valores);
  const maximo = Math.max.apply(null, valores);
  const amplitude = (maximo - minimo) || 1;

  function coordX(indice) {
    const margem = 8;
    return pontos.length === 1 ? largura / 2 : margem + (indice / (pontos.length - 1)) * (largura - 2 * margem);
  }
  function coordY(valor) {
    return altura - ((valor - minimo) / amplitude) * (altura - 16) - 8;
  }

  const caminho = pontos.map(function (ponto, indice) {
    return (indice === 0 ? 'M' : 'L') + coordX(indice).toFixed(1) + ',' + coordY(ponto.carga_maxima).toFixed(1);
  }).join(' ');

  let svg = '<svg viewBox="0 0 ' + largura + ' ' + (altura + margemBaixo) +
    '" class="grafico-svg" role="img" aria-label="Evolução da carga máxima">';
  svg += '<path d="' + caminho + '" class="grafico-linha"></path>';
  pontos.forEach(function (ponto, indice) {
    svg += '<circle cx="' + coordX(indice).toFixed(1) + '" cy="' + coordY(ponto.carga_maxima).toFixed(1) +
      '" r="3.5" class="grafico-ponto"><title>' + formatarData(ponto.data) + ': ' +
      ponto.carga_maxima + ' kg</title></circle>';
  });
  svg += '</svg>';
  container.innerHTML = svg;
}
