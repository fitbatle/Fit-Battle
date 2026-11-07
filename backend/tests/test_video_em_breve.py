import os
import re
import unittest

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")
TITULO_VIDEO = "Envio de vídeo previsto para uma próxima versão"


def _ler(nome):
    with open(os.path.join(FRONTEND, nome), "r", encoding="utf-8") as arquivo:
        return arquivo.read()


class TestVideoEmBreve(unittest.TestCase):

    def setUp(self):
        self.html = _ler("registrar-treino.html")

    def _botao(self):
        encontrado = re.search(r'<button[^>]*\bid="btnVideoEmBreve"[^>]*>.*?</button>', self.html, re.S)
        self.assertIsNotNone(encontrado, "botao de video nao encontrado")
        return encontrado.group(0)

    def test_botao_existe_e_esta_desativado(self):
        self.assertIn(" disabled", self._botao())

    def test_botao_tem_a_etiqueta_em_breve_e_o_titulo_previsto(self):
        botao = self._botao()
        self.assertIn("Vídeo do treino", botao)
        self.assertIn('class="badge badge--placeholder">Em breve</span>', botao)
        self.assertIn('title="%s"' % TITULO_VIDEO, botao)

    def test_botao_fica_no_passo_opcional_e_nao_no_obrigatorio(self):
        etapa1 = re.search(r'<section[^>]*id="etapa1".*?</section>', self.html, re.S).group(0)
        etapa2 = re.search(r'<section[^>]*id="etapa2".*?</section>', self.html, re.S).group(0)
        self.assertNotIn("btnVideoEmBreve", etapa1)
        self.assertIn("btnVideoEmBreve", etapa2)
        self.assertIn("Anexo (opcional)", etapa2)

    def test_nenhum_script_chama_rota_nem_envia_o_video(self):
        for nome in ("registrar-treino.js", "api.js", "shell.js"):
            with self.subTest(arquivo=nome):
                self.assertNotIn("btnVideoEmBreve", _ler(nome))


if __name__ == "__main__":
    unittest.main()
