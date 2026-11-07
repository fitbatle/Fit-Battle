import os
import re
import unittest

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")


def _ler(nome):
    with open(os.path.join(FRONTEND, nome), "r", encoding="utf-8") as arquivo:
        return arquivo.read()


def _tag(html, id_elemento):
    encontrado = re.search(r'<[^>]*\bid="%s"[^>]*>' % id_elemento, html)
    return encontrado.group(0) if encontrado else ""


class TestPaginaExclusaoConta(unittest.TestCase):

    def setUp(self):
        self.html = _ler("perfil.html")
        self.js = _ler("perfil.js")

    def test_botao_de_excluir_fica_no_cartao_de_zona_de_exclusao(self):
        cartao = re.search(r'<section[^>]*perfil-zona-exclusao[^>]*>.*?</section>', self.html, re.S)
        self.assertIsNotNone(cartao)
        self.assertIn('id="btnExcluirConta"', cartao.group(0))
        self.assertIn("Excluir minha conta", cartao.group(0))

    def test_texto_da_zona_nao_usa_caixa_alta_por_classe(self):
        cartao = re.search(r'<section[^>]*perfil-zona-exclusao[^>]*>.*?</section>', self.html, re.S).group(0)
        self.assertNotIn("rotulo-mini", cartao)
        self.assertIn("perfil-zona-texto", cartao)
        self.assertIn("termos.html#termo-consentimento", cartao)

    def test_modal_tem_campo_de_confirmacao_e_botoes(self):
        self.assertIn('id="overlayExcluirConta"', self.html)
        self.assertIn('id="confirmacaoExclusao"', self.html)
        self.assertIn('id="btnCancelarExclusao"', self.html)
        self.assertIn('id="btnConfirmarExclusao"', self.html)
        self.assertIn("Digite EXCLUIR para confirmar", self.html)
        self.assertIn("Excluir definitivamente", self.html)

    def test_botao_de_confirmacao_comeca_desabilitado(self):
        self.assertIn("disabled", _tag(self.html, "btnConfirmarExclusao"))

    def test_palavra_de_confirmacao_e_exata_no_script(self):
        self.assertIn("PALAVRA_CONFIRMACAO_EXCLUSAO = 'EXCLUIR'", self.js)
        self.assertIn("digitado !== PALAVRA_CONFIRMACAO_EXCLUSAO", self.js)

    def test_script_apaga_a_conta_pela_rota_existente_e_avisa_no_login(self):
        self.assertIn("method: 'DELETE'", self.js)
        self.assertIn("`/usuarios/${usuarioLogado.id}`", self.js)
        self.assertIn("limparSessao()", self.js)
        self.assertIn("avisarNoLogin('Sua conta foi excluída.')", self.js)

    def test_mostrar_mais_comeca_oculto(self):
        self.assertIn("hidden", _tag(self.html, "btnMostrarMais"))
        self.assertIn("TAMANHO_PAGINA_TREINOS = 5", self.js)


if __name__ == "__main__":
    unittest.main()
