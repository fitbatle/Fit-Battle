const PADRAO_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const IDADE_MINIMA = 13;
const IDADE_MAIORIDADE = 18;
const ATRASO_REDIRECIONAR_MS = 1500;

document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('registerForm');
  const nome = document.getElementById('usuario');
  const email = document.getElementById('email');
  const dataNascimento = document.getElementById('dataNascimento');
  const senha = document.getElementById('senha');
  const aceitePagina = document.getElementById('aceitePagina');
  const mensagem = document.getElementById('errorMessage');
  const botaoCadastrar = document.getElementById('btnCadastrar');

  const responsavelBox = document.getElementById('responsavelBox');
  const responsavelNome = document.getElementById('responsavelNome');
  const responsavelEmail = document.getElementById('responsavelEmail');
  const autorizacaoResponsavel = document.getElementById('autorizacaoResponsavel');

  const overlay = document.getElementById('overlayTermo');
  const painelConsentimento = document.getElementById('painelConsentimento');
  const painelLeitura = document.getElementById('painelLeitura');
  const iframeTermo = document.getElementById('iframeTermo');
  const btnVoltar = document.getElementById('btnVoltarConsentimento');
  const btnConfirmar = document.getElementById('btnConfirmarCadastro');
  const aceiteTermos = document.getElementById('aceiteTermos');
  const erroModal = document.getElementById('erroModalTermo');

  let dadosPendentes = null;

  limparErroAoEditar(form, mensagem);

  function erro(texto, campo) {
    mostrarMensagemForm(mensagem, texto, false);
    if (campo) campo.focus();
  }

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

  dataNascimento.max = dataDeHoje();

  function atualizarResponsavel() {
    const idadeCalculada = calcularIdade(dataNascimento.value);
    const menor = idadeCalculada !== null && idadeCalculada >= IDADE_MINIMA && idadeCalculada < IDADE_MAIORIDADE;
    responsavelBox.hidden = !menor;
  }
  dataNascimento.addEventListener('input', atualizarResponsavel);
  atualizarResponsavel();

  function abrirModal() {
    overlay.classList.add('aberto');
  }

  function abrirConsentimento() {
    painelLeitura.hidden = true;
    painelConsentimento.hidden = false;
    erroModal.textContent = '';
    abrirModal();
    document.getElementById('closeTermo').focus();
  }

  function abrirLeitura(ancora, vindoDoConsentimento) {
    iframeTermo.src = 'termos.html#' + ancora;
    painelConsentimento.hidden = true;
    painelLeitura.hidden = false;
    btnVoltar.hidden = !vindoDoConsentimento;
    abrirModal();
    document.getElementById('closeTermo').focus();
  }

  function fecharModal() {
    overlay.classList.remove('aberto');
    dadosPendentes = null;
  }

  document.querySelectorAll('[data-abrir-termo]').forEach(function (link) {
    link.addEventListener('click', function (evento) {
      evento.preventDefault();
      abrirLeitura(link.getAttribute('data-abrir-termo'), false);
    });
  });

  document.getElementById('linkLerTermoCompleto').addEventListener('click', function (evento) {
    evento.preventDefault();
    abrirLeitura('termo-uso', true);
  });

  btnVoltar.addEventListener('click', function () {
    painelLeitura.hidden = true;
    painelConsentimento.hidden = false;
  });

  document.getElementById('closeTermo').addEventListener('click', fecharModal);
  document.getElementById('btnCancelarTermo').addEventListener('click', fecharModal);
  overlay.addEventListener('click', function (evento) {
    if (evento.target === overlay) fecharModal();
  });
  document.addEventListener('keydown', function (evento) {
    if (evento.key === 'Escape' && overlay.classList.contains('aberto')) fecharModal();
  });

  form.addEventListener('submit', function (evento) {
    evento.preventDefault();
    mostrarMensagemForm(mensagem, '', false);

    if (nome.value.trim().length < 3) {
      return erro('Informe um nome com pelo menos 3 caracteres.', nome);
    }
    if (!PADRAO_EMAIL.test(email.value.trim())) {
      return erro('Por favor, informe um e-mail válido.', email);
    }

    if (!dataNascimento.value) {
      return erro('Informe sua data de nascimento.', dataNascimento);
    }
    if (dataNascimento.value > dataDeHoje()) {
      return erro('A data de nascimento não pode ser no futuro.', dataNascimento);
    }
    const idadeNum = calcularIdade(dataNascimento.value);
    if (idadeNum > 120) {
      return erro('Data de nascimento inválida.', dataNascimento);
    }
    if (idadeNum < IDADE_MINIMA) {
      return erro('O cadastro não é permitido para menores de 13 anos (art. 14 da LGPD).', dataNascimento);
    }

    let responsavel = null;
    if (idadeNum < IDADE_MAIORIDADE) {
      if (responsavelNome.value.trim().length < 3) {
        return erro('Informe o nome completo do responsável legal.', responsavelNome);
      }
      if (!PADRAO_EMAIL.test(responsavelEmail.value.trim())) {
        return erro('Informe um e-mail válido do responsável legal.', responsavelEmail);
      }
      if (!autorizacaoResponsavel.checked) {
        return erro('É necessária a autorização do responsável legal.', autorizacaoResponsavel);
      }
      responsavel = { nome: responsavelNome.value.trim(), email: responsavelEmail.value.trim() };
    }

    if (senha.value.length < 8) {
      return erro('A senha deve ter no mínimo 8 caracteres.', senha);
    }
    if (!aceitePagina.checked) {
      return erro('Marque a caixa para concordar com os Termos de Uso e a Política de Privacidade.', aceitePagina);
    }

    dadosPendentes = {
      nome: nome.value.trim(),
      email: email.value.trim(),
      data_nascimento: dataNascimento.value,
      senha: senha.value,
      responsavel: responsavel
    };
    abrirConsentimento();
  });

  btnConfirmar.addEventListener('click', async function () {
    if (!dadosPendentes) return;

    if (!aceiteTermos.checked) {
      erroModal.textContent = 'Você precisa ler e aceitar o Termo de Uso e o Termo de Consentimento.';
      return;
    }

    const consentimentos = {};
    document.querySelectorAll('input[name="consent"]').forEach(function (caixa) {
      consentimentos[caixa.value] = caixa.checked;
    });

    btnConfirmar.disabled = true;
    btnConfirmar.textContent = 'Enviando...';
    erroModal.textContent = '';

    try {
      const resposta = await fetch(API_URL + '/usuarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: dadosPendentes.nome,
          email: dadosPendentes.email,
          data_nascimento: dadosPendentes.data_nascimento,
          senha: dadosPendentes.senha,
          aceite_termos: true,
          consentimentos: consentimentos,
          responsavel: dadosPendentes.responsavel,
          autorizacao_responsavel: dadosPendentes.responsavel !== null
        })
      });
      const dados = await resposta.json().catch(function () { return {}; });

      if (!resposta.ok) {
        erroModal.textContent = dados.erro || 'Não foi possível concluir o cadastro.';
        return;
      }

      fecharModal();
      mostrarMensagemForm(mensagem, (dados.mensagem || 'Cadastro realizado com sucesso!') + ' Redirecionando para o login...', true);
      form.reset();
      atualizarResponsavel();
      botaoCadastrar.disabled = true;
      setTimeout(function () { window.location.href = PAGINA_LOGIN; }, ATRASO_REDIRECIONAR_MS);
    } catch (e) {
      erroModal.textContent = 'Não foi possível falar com o servidor. Tente novamente.';
    } finally {
      btnConfirmar.disabled = false;
      btnConfirmar.textContent = 'Confirmar cadastro';
    }
  });
});
