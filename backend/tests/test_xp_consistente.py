from datetime import date, timedelta
from unittest import mock

from tests.test_seguranca import BaseTeste

ADMIN_EMAIL = "admin@teste.com"


class TestXpConsistenteEntreTelas(BaseTeste):

    def setUp(self):
        super().setUp()
        self._patch_admin = mock.patch.dict("os.environ", {"ADMIN_EMAILS": ADMIN_EMAIL})
        self._patch_admin.start()
        self.addCleanup(self._patch_admin.stop)
        self.admin, self.token_admin = self.criar_usuario_logado("Admin Xp", email=ADMIN_EMAIL)
        self.usuario, self.token = self.criar_usuario_logado(
            "Xp Principal", consentimentos={"ranking_publico": True}
        )
        self.cli.put(
            f"/api/usuarios/{self.usuario['id']}",
            json={"cidade": "Belo Horizonte", "estado": "MG"},
            headers=self.auth(self.token),
        )

    def treinar(self, tempo=40, carga=100, reps=5):
        resposta = self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/atividades",
            json={"tipo": "musculacao", "titulo": "Supino Reto", "tempo_min": tempo, "carga_kg": carga, "repeticoes": reps},
            headers=self.auth(self.token),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))

    def criar_desafio(self, recompensa):
        hoje = date.today()
        resposta = self.cli.post(
            "/api/desafios",
            json={
                "nome": "Desafio de consistencia",
                "descricao": "Teste.",
                "exercicio": "livre",
                "tipo_metrica": "treinos",
                "valor_objetivo": 3,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=7)).isoformat(),
                "recompensa_xp": recompensa,
            },
            headers=self.auth(self.token_admin),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["desafio"]["id"]

    def xp_em_cada_tela(self):
        uid = self.usuario["id"]
        h = self.auth(self.token)
        eu = self.cli.get("/api/eu", headers=h).get_json()["usuario"]["xp"]
        perfil = self.cli.get(f"/api/usuarios/{uid}", headers=h).get_json()["xp"]
        dashboard = self.cli.get("/api/dashboard", headers=h).get_json()["totais"]["xp"]

        def linha(corpo):
            return next(item["pontuacao_total"] for item in corpo if item["id_usuario"] == uid)

        ranking_global = linha(self.cli.get("/api/ranking/global", headers=h).get_json())
        ranking_regional = linha(
            self.cli.get("/api/ranking/regional", query_string={"cidade": "Belo Horizonte"}, headers=h).get_json()
        )
        return {
            "eu": eu,
            "perfil": perfil,
            "dashboard": dashboard,
            "ranking_global": ranking_global,
            "ranking_regional": ranking_regional,
        }

    def test_recompensa_de_desafio_entra_no_xp_de_todas_as_telas(self):
        self.treinar()
        self.treinar()
        id_desafio = self.criar_desafio(recompensa=100)
        self.cli.post(f"/api/desafios/{id_desafio}/participar", headers=self.auth(self.token))
        self.treinar()
        self.treinar()
        self.treinar()

        grupo = self.cli.post(
            "/api/grupos",
            json={"nome": "Grupo Xp", "descricao": "Teste de XP."},
            headers=self.auth(self.token),
        )
        self.assertEqual(grupo.status_code, 201, grupo.get_data(as_text=True))
        id_grupo = grupo.get_json()["grupo"]["id"]

        desafios = self.cli.get("/api/desafios", headers=self.auth(self.token)).get_json()
        concluido = next(d for d in desafios if d["id"] == id_desafio)
        self.assertEqual(concluido["minha_inscricao"]["status"], "concluido")

        historico = self.cli.get(
            f"/api/usuarios/{self.usuario['id']}/atividades", headers=self.auth(self.token)
        ).get_json()
        soma_treinos = sum(t["pontuacao"] for t in historico)

        xp = self.xp_em_cada_tela()
        grupo_ranking = self.cli.get(f"/api/grupos/{id_grupo}/ranking", headers=self.auth(self.token)).get_json()
        xp["ranking_grupo"] = next(
            item["pontuacao_total"] for item in grupo_ranking if item["id_usuario"] == self.usuario["id"]
        )

        self.assertEqual(set(xp.values()), {soma_treinos + 100})
