import unittest
from unittest import mock

from tests.test_seguranca import SENHA, BaseTeste


class BaseNotificacao(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Notifica")
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Notifica")

    def postar(self, token):
        resposta = self.cli.post(
            "/api/postagens", data={"texto": "Postagem de teste"}, headers=self.auth(token)
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["postagem"]

    def notificacoes(self, token):
        resposta = self.cli.get("/api/notificacoes", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_json()

    def desativar_notificacoes(self, token, usuario):
        self.cli.put(
            f"/api/usuarios/{usuario['id']}/consentimentos/notificacoes",
            json={"aceito": False}, headers=self.auth(token),
        )


class TestNotificacaoDeCurtidaEComentario(BaseNotificacao):

    def test_curtir_postagem_de_outro_gera_notificacao(self):
        postagem = self.postar(self.token_ana)
        resposta = self.cli.post(
            f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_bia)
        )
        self.assertEqual(resposta.status_code, 200)

        notificacoes = self.notificacoes(self.token_ana)
        self.assertEqual(len(notificacoes), 1)
        self.assertEqual(notificacoes[0]["tipo"], "curtida")
        self.assertIn("Bia Notifica", notificacoes[0]["mensagem"])
        self.assertFalse(notificacoes[0]["lida"])

    def test_curtir_a_propria_postagem_nunca_notifica(self):
        postagem = self.postar(self.token_ana)
        self.cli.post(f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_ana))
        self.assertEqual(self.notificacoes(self.token_ana), [])

    def test_curtir_e_descurtir_nao_duplica_notificacao(self):
        postagem = self.postar(self.token_ana)
        alvo = f"/api/feed/postagem/{postagem['id']}/curtir"
        self.cli.post(alvo, headers=self.auth(self.token_bia))
        self.cli.post(alvo, headers=self.auth(self.token_bia))
        self.assertEqual(len(self.notificacoes(self.token_ana)), 1)

    def test_comentar_em_postagem_de_outro_gera_notificacao(self):
        postagem = self.postar(self.token_ana)
        resposta = self.cli.post(
            f"/api/feed/postagem/{postagem['id']}/comentarios",
            json={"texto": "Muito bom!"}, headers=self.auth(self.token_bia),
        )
        self.assertEqual(resposta.status_code, 201)
        notificacoes = self.notificacoes(self.token_ana)
        self.assertEqual(len(notificacoes), 1)
        self.assertEqual(notificacoes[0]["tipo"], "comentario")

    def test_comentar_na_propria_postagem_nao_notifica(self):
        postagem = self.postar(self.token_ana)
        self.cli.post(
            f"/api/feed/postagem/{postagem['id']}/comentarios",
            json={"texto": "Comentando em mim mesma"}, headers=self.auth(self.token_ana),
        )
        self.assertEqual(self.notificacoes(self.token_ana), [])

    def test_sem_consentimento_notificacoes_nao_gera_nada(self):
        self.desativar_notificacoes(self.token_ana, self.ana)
        postagem = self.postar(self.token_ana)
        self.cli.post(f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_bia))
        self.assertEqual(self.notificacoes(self.token_ana), [])


class TestNotificacaoDeConvite(BaseNotificacao):

    def test_convite_recebido_e_aceito_geram_notificacao_para_cada_lado(self):
        grupo = self.cli.post(
            "/api/grupos", json={"nome": "Grupo Notifica"}, headers=self.auth(self.token_ana)
        ).get_json()["grupo"]

        self.cli.post(
            f"/api/grupos/{grupo['id']}/convites", json={"id_usuario": self.bia["id"]},
            headers=self.auth(self.token_ana),
        )
        notificacoes_bia = self.notificacoes(self.token_bia)
        self.assertEqual(len(notificacoes_bia), 1)
        self.assertEqual(notificacoes_bia[0]["tipo"], "convite_recebido")

        id_convite = self.cli.get("/api/convites", headers=self.auth(self.token_bia)).get_json()["pendentes"][0]["id"]
        self.cli.put(f"/api/convites/{id_convite}", json={"aceito": True}, headers=self.auth(self.token_bia))

        notificacoes_ana = self.notificacoes(self.token_ana)
        self.assertEqual(len(notificacoes_ana), 1)
        self.assertEqual(notificacoes_ana[0]["tipo"], "convite_aceito")


class TestNotificacaoDeMeta(BaseNotificacao):

    def test_meta_concluida_gera_notificacao_uma_vez(self):
        self.cli.post(
            f"/api/usuarios/{self.ana['id']}/atividades",
            json={"tipo": "musculacao", "titulo": "Supino Reto", "tempo_min": 40, "carga_kg": 100, "repeticoes": 5},
            headers=self.auth(self.token_ana),
        )
        meta = self.cli.post(
            "/api/metas",
            json={"titulo": "Bater 100kg", "tipo": "curto_prazo", "tipo_metrica": "carga_maxima",
                  "exercicio": "Supino Reto", "valor_objetivo": 100},
            headers=self.auth(self.token_ana),
        ).get_json()["meta"]
        self.assertEqual(meta["status"], "concluida")

        self.cli.get(f"/api/metas/{meta['id']}", headers=self.auth(self.token_ana))
        self.cli.get(f"/api/metas/{meta['id']}", headers=self.auth(self.token_ana))

        notificacoes = [n for n in self.notificacoes(self.token_ana) if n["tipo"] == "meta_concluida"]
        self.assertEqual(len(notificacoes), 1)


class TestNotificacaoDeRanking(BaseNotificacao):

    def test_subir_no_ranking_global_notifica_so_quem_subiu(self):
        self.cli.post(
            f"/api/usuarios/{self.bia['id']}/atividades",
            json={"tipo": "musculacao", "titulo": "Supino Reto", "tempo_min": 60, "carga_kg": 100, "repeticoes": 10},
            headers=self.auth(self.token_bia),
        )
        self.cli.post(
            f"/api/usuarios/{self.ana['id']}/atividades",
            json={"tipo": "musculacao", "titulo": "Supino Reto", "tempo_min": 90, "carga_kg": 150, "repeticoes": 10},
            headers=self.auth(self.token_ana),
        )
        notificacoes_ana = [n for n in self.notificacoes(self.token_ana) if n["tipo"] == "subida_ranking"]
        self.assertEqual(len(notificacoes_ana), 1)
        notificacoes_bia = [n for n in self.notificacoes(self.token_bia) if n["tipo"] == "subida_ranking"]
        self.assertEqual(len(notificacoes_bia), 0)


class TestPermissoesDeNotificacao(BaseNotificacao):

    def test_exige_login(self):
        self.assertEqual(self.cli.get("/api/notificacoes").status_code, 401)
        self.assertEqual(self.cli.get("/api/notificacoes/contagem").status_code, 401)

    def test_so_ve_as_proprias_notificacoes(self):
        postagem = self.postar(self.token_ana)
        self.cli.post(f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_bia))
        self.assertEqual(self.notificacoes(self.token_bia), [])

    def test_nao_pode_marcar_notificacao_de_outro_usuario_como_lida(self):
        postagem = self.postar(self.token_ana)
        self.cli.post(f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_bia))
        id_notif = self.notificacoes(self.token_ana)[0]["id"]
        resposta = self.cli.put(f"/api/notificacoes/{id_notif}/lida", headers=self.auth(self.token_bia))
        self.assertEqual(resposta.status_code, 403)

    def test_marcar_lida_e_marcar_todas_lidas(self):
        postagem = self.postar(self.token_ana)
        self.cli.post(f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_bia))
        self.cli.post(
            f"/api/feed/postagem/{postagem['id']}/comentarios",
            json={"texto": "oi"}, headers=self.auth(self.token_bia),
        )

        contagem = self.cli.get("/api/notificacoes/contagem", headers=self.auth(self.token_ana)).get_json()
        self.assertEqual(contagem["nao_lidas"], 2)

        id_notif = self.notificacoes(self.token_ana)[0]["id"]
        self.cli.put(f"/api/notificacoes/{id_notif}/lida", headers=self.auth(self.token_ana))
        contagem = self.cli.get("/api/notificacoes/contagem", headers=self.auth(self.token_ana)).get_json()
        self.assertEqual(contagem["nao_lidas"], 1)

        self.cli.put("/api/notificacoes/lidas", headers=self.auth(self.token_ana))
        contagem = self.cli.get("/api/notificacoes/contagem", headers=self.auth(self.token_ana)).get_json()
        self.assertEqual(contagem["nao_lidas"], 0)


class TestEnvioDeEmail(BaseNotificacao):

    def test_sem_smtp_configurado_nao_tenta_enviar(self):
        with mock.patch("smtplib.SMTP") as smtp_mock:
            postagem = self.postar(self.token_ana)
            self.cli.post(f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_bia))
            smtp_mock.assert_not_called()

    def test_falha_no_smtp_nao_derruba_a_requisicao(self):
        with mock.patch.dict("os.environ", {"SMTP_HOST": "smtp.invalido.teste"}):
            with mock.patch("smtplib.SMTP", side_effect=OSError("timeout")):
                postagem = self.postar(self.token_ana)
                resposta = self.cli.post(
                    f"/api/feed/postagem/{postagem['id']}/curtir", headers=self.auth(self.token_bia)
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(len(self.notificacoes(self.token_ana)), 1)


if __name__ == "__main__":
    unittest.main()
