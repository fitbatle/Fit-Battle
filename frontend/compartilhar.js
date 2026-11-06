function abrirAvisoCompartilhar() {
  const overlay = document.createElement('div');
  overlay.className = 'overlay aberto';
  overlay.innerHTML =
    '<div class="modal-termo modal-termo--estreito">' +
      '<button type="button" class="modal-close" aria-label="Fechar"><span data-icone="fechar"></span></button>' +
      '<h2 class="modal-title">Compartilhamento desativado</h2>' +
      '<p>Para compartilhar conquistas, ative o consentimento de compartilhamento na página de Privacidade.</p>' +
      '<div class="modal-actions">' +
        '<a class="btn btn--primario" href="privacidade.html">Ir para Privacidade</a>' +
      '</div>' +
    '</div>';
  document.body.appendChild(overlay);
  ativarIcones(overlay);
  function fechar() { overlay.remove(); }
  overlay.querySelector('.modal-close').addEventListener('click', fechar);
  overlay.addEventListener('click', function (evento) { if (evento.target === overlay) fechar(); });
}

function abrirMenuCompartilhar(opcoes) {
  const texto = opcoes.texto;
  const url = opcoes.url || new URL('feed.html', window.location.href).href;
  const overlay = document.createElement('div');
  overlay.className = 'overlay aberto';
  overlay.innerHTML =
    '<div class="modal-termo modal-termo--estreito">' +
      '<button type="button" class="modal-close" aria-label="Fechar"><span data-icone="fechar"></span></button>' +
      '<h2 class="modal-title">Compartilhar</h2>' +
      '<div class="modal-actions">' +
        (typeof navigator.share === 'function'
          ? '<button type="button" class="btn btn--primario" data-rede="web_share">Compartilhar</button>'
          : '') +
        '<a class="btn btn--fantasma" data-rede="whatsapp" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(texto) + '">WhatsApp</a>' +
        '<a class="btn btn--fantasma" data-rede="x" target="_blank" rel="noopener" href="https://twitter.com/intent/tweet?text=' + encodeURIComponent(texto) + '">X</a>' +
        '<a class="btn btn--fantasma" data-rede="telegram" target="_blank" rel="noopener" href="https://t.me/share/url?url=' + encodeURIComponent(url) + '&text=' + encodeURIComponent(texto) + '">Telegram</a>' +
        '<button type="button" class="btn btn--fantasma" data-rede="copiar">Copiar texto</button>' +
      '</div>' +
    '</div>';
  document.body.appendChild(overlay);
  ativarIcones(overlay);

  function fechar() { overlay.remove(); }
  overlay.querySelector('.modal-close').addEventListener('click', fechar);
  overlay.addEventListener('click', function (evento) { if (evento.target === overlay) fechar(); });

  overlay.querySelectorAll('[data-rede]').forEach(function (elemento) {
    elemento.addEventListener('click', function (evento) {
      const rede = elemento.getAttribute('data-rede');
      if (rede === 'web_share') {
        evento.preventDefault();
        navigator.share({ text: texto, url: url }).catch(function () {});
      } else if (rede === 'copiar') {
        evento.preventDefault();
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(texto).catch(function () {});
        }
        mostrarToast('Texto copiado.');
      }
      registrarCompartilhamento(opcoes.tipoConteudo, opcoes.idAtividade, opcoes.idMeta, rede, opcoes.chaveMedalha);
      fechar();
    });
  });
}

async function registrarCompartilhamento(tipoConteudo, idAtividade, idMeta, redeSocial, chaveMedalha) {
  try {
    await api('/compartilhamentos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tipo_conteudo: tipoConteudo,
        id_atividade: idAtividade || null,
        id_meta: idMeta || null,
        chave_medalha: chaveMedalha || null,
        rede_social: redeSocial
      })
    });
  } catch (erro) {}
}

async function abrirCompartilhar(opcoes) {
  const idUsuario = idDaSessao();
  if (!idUsuario) return;
  try {
    const resposta = await api('/usuarios/' + idUsuario + '/consentimentos');
    if (!resposta.ok) return mostrarToast('Não foi possível verificar o consentimento de compartilhamento.');
    const consentimentos = await resposta.json();
    const compartilhamento = consentimentos.find(function (c) { return c.chave === 'compartilhamento'; });
    if (!compartilhamento || !compartilhamento.aceito) return abrirAvisoCompartilhar();
    abrirMenuCompartilhar(opcoes);
  } catch (erro) {
    mostrarToast('Não foi possível falar com o servidor. Tente novamente.');
  }
}
