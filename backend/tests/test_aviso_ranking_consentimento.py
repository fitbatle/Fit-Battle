import os
import unittest

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")


def _ler(nome):
    with open(os.path.join(FRONTEND, nome), "r", encoding="utf-8") as arquivo:
        return arquivo.read()


class TestAvisoRankingConsentimento(unittest.TestCase):

    def test_pagina_do_ranking_tem_o_aviso_escondido_por_padrao(self):
        html = _ler("ranking.html")
        self.assertIn('id="avisoPerfilOculto" hidden', html)
        self.assertIn("consentimento para exibi-lo não foi dado", html)
        self.assertIn('href="privacidade.html"', html)

    def test_script_mostra_o_aviso_so_quando_o_perfil_nao_e_publico(self):
        script = _ler("ranking.js")
        self.assertIn("usuarioLogado.perfil_publico === false", script)
        self.assertIn("document.getElementById('avisoPerfilOculto').hidden = false;", script)


if __name__ == "__main__":
    unittest.main()
