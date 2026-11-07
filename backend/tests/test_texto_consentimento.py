import os
import re
import unittest

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")

TEXTO_RANKING = "Sem marcar 'Aparecer nos rankings regional e global', seu perfil não entra nos rankings."
TEXTO_BUSCA = "Sem marcar 'Permitir que outros usuários me encontrem pela busca', ninguém te encontra pela busca."
TEXTO_PRIVACIDADE = "Você pode mudar isso depois em Privacidade e Consentimentos."


def _ler(nome):
    with open(os.path.join(FRONTEND, nome), "r", encoding="utf-8") as arquivo:
        return arquivo.read()


def _secao_opcionais(html):
    inicio = html.index('consent-group-title">Opcionais')
    fim = html.index('class="consent-accept"', inicio)
    return html[inicio:fim]


class TestTextoConsentimento(unittest.TestCase):

    def test_paragrafo_em_opcionais_e_caixas_de_ranking_e_busca_desmarcadas(self):
        html = _ler("index.html")
        secao = _secao_opcionais(html)
        self.assertIn('class="consent-intro"', secao)
        self.assertIn(TEXTO_RANKING, secao)
        self.assertIn(TEXTO_BUSCA, secao)
        self.assertIn(TEXTO_PRIVACIDADE, secao)
        self.assertNotIn("já vêm marcadas", html)
        for chave in ("ranking_publico", "busca_perfil"):
            with self.subTest(chave=chave):
                linha = re.search(r'<input type="checkbox" name="consent" value="%s"[^>]*>' % chave, html)
                self.assertIsNotNone(linha)
                self.assertNotIn("checked", linha.group(0))


if __name__ == "__main__":
    unittest.main()
