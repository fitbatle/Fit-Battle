import unittest

from services.atividade.apoio import progresso_de_nivel
from tests.test_seguranca import BaseTeste


class TestProgressoDeNivel(unittest.TestCase):

    def test_fronteiras_das_faixas(self):
        casos = [
            (0, "iniciante", 0, 1000),
            (999, "iniciante", 100, 1),
            (1000, "intermediario", 0, 2000),
            (1500, "intermediario", 25, 1500),
            (2999, "intermediario", 100, 1),
            (3000, "avancado", 0, 4000),
            (15000, "elite", 100, 0),
            (20000, "elite", 100, 0),
        ]
        for xp, nivel, percentual, faltante in casos:
            with self.subTest(xp=xp):
                self.assertEqual(
                    progresso_de_nivel(xp),
                    {"nivel": nivel, "percentual": percentual, "xp_faltante": faltante},
                )


class TestProgressoNivelNaRota(BaseTeste):

    def test_eu_devolve_o_progresso_do_usuario(self):
        usuario, token = self.criar_usuario_logado("Lia Progresso")
        resposta = self.cli.get("/api/eu", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        progresso = resposta.get_json()["usuario"]["progresso_nivel"]
        self.assertEqual(progresso, {"nivel": "iniciante", "percentual": 0, "xp_faltante": 1000})

    def test_progresso_acompanha_o_xp_registrado(self):
        usuario, token = self.criar_usuario_logado("Teo Progresso")
        self.registrar_treino(usuario, token)
        resposta = self.cli.get("/api/eu", headers=self.auth(token))
        progresso = resposta.get_json()["usuario"]["progresso_nivel"]
        xp = resposta.get_json()["usuario"]["xp"]
        self.assertGreater(xp, 0)
        self.assertEqual(progresso["nivel"], "iniciante")
        self.assertEqual(progresso["xp_faltante"], 1000 - xp)


class TestNivelNosRankings(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Nina Ranking")
        self.registrar_treino(self.usuario, self.token)
        self.cli.put(
            f"/api/usuarios/{self.usuario['id']}",
            json={"cidade": "Belo Horizonte", "estado": "MG"},
            headers=self.auth(self.token),
        )

    def linha_do_usuario(self, corpo):
        return next(item for item in corpo if item["id_usuario"] == self.usuario["id"])

    def test_ranking_global_traz_o_nivel(self):
        resposta = self.cli.get("/api/ranking/global", headers=self.auth(self.token))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.linha_do_usuario(resposta.get_json())["nivel"], "iniciante")

    def test_ranking_regional_traz_o_nivel(self):
        resposta = self.cli.get(
            "/api/ranking/regional", query_string={"estado": "MG"}, headers=self.auth(self.token)
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.linha_do_usuario(resposta.get_json())["nivel"], "iniciante")
