import unittest

from tests.test_seguranca import BaseTeste


class BaseCompartilhamento(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Compartilha")
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Compartilha")

    def registrar_treino(self, token, carga=140):
        resposta = self.cli.post(
            f"/api/usuarios/{self.ana['id']}/atividades",
            json={"tipo": "musculacao", "titulo": "Supino Reto", "tempo_min": 40, "carga_kg": carga, "repeticoes": 5},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["atividade"]

    def criar_meta(self, token):
        resposta = self.cli.post(
            "/api/metas",
            json={"titulo": "Meta Teste", "tipo": "curto_prazo", "tipo_metrica": "carga_maxima",
                  "exercicio": "Supino Reto", "valor_objetivo": 200},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["meta"]

    def desativar_consentimento(self, token, usuario):
        resposta = self.cli.put(
            f"/api/usuarios/{usuario['id']}/consentimentos/compartilhamento",
            json={"aceito": False},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))


class TestCompartilharAtividade(BaseCompartilhamento):

    def test_compartilha_a_propria_atividade(self):
        atividade = self.registrar_treino(self.token_ana)
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "atividade", "id_atividade": atividade["id"], "rede_social": "whatsapp"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        corpo = resposta.get_json()["compartilhamento"]
        self.assertEqual(corpo["tipo_conteudo"], "atividade")
        self.assertEqual(corpo["id_atividade"], atividade["id"])
        self.assertEqual(corpo["rede_social"], "whatsapp")

    def test_compartilha_recorde_pessoal(self):
        atividade = self.registrar_treino(self.token_ana)
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "recorde", "id_atividade": atividade["id"], "rede_social": "x"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))

    def test_nao_pode_compartilhar_atividade_de_outro_usuario(self):
        atividade = self.registrar_treino(self.token_ana)
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "atividade", "id_atividade": atividade["id"], "rede_social": "telegram"},
            headers=self.auth(self.token_bia),
        )
        self.assertEqual(resposta.status_code, 403)

    def test_atividade_inexistente_devolve_404(self):
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "atividade", "id_atividade": 99999, "rede_social": "copiar"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 404)

    def test_atividade_sem_id_devolve_400(self):
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "atividade", "rede_social": "copiar"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 400)


class TestCompartilharMeta(BaseCompartilhamento):

    def test_compartilha_a_propria_meta(self):
        meta = self.criar_meta(self.token_ana)
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "meta", "id_meta": meta["id"], "rede_social": "web_share"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        corpo = resposta.get_json()["compartilhamento"]
        self.assertEqual(corpo["id_meta"], meta["id"])
        self.assertIsNone(corpo["id_atividade"])

    def test_nao_pode_compartilhar_meta_de_outro_usuario(self):
        meta = self.criar_meta(self.token_ana)
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "meta", "id_meta": meta["id"], "rede_social": "telegram"},
            headers=self.auth(self.token_bia),
        )
        self.assertEqual(resposta.status_code, 403)

    def test_meta_inexistente_devolve_404(self):
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "meta", "id_meta": 99999, "rede_social": "copiar"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 404)

    def test_meta_sem_id_devolve_400(self):
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "meta", "rede_social": "copiar"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 400)


class TestCompartilharMedalha(BaseCompartilhamento):

    def compartilhar(self, token, chave=None, **extra):
        corpo = {"tipo_conteudo": "medalha", "rede_social": "whatsapp", **extra}
        if chave is not None:
            corpo["chave_medalha"] = chave
        return self.cli.post("/api/compartilhamentos", json=corpo, headers=self.auth(token))

    def test_compartilha_medalha_conquistada_e_grava_a_chave(self):
        self.registrar_treino(self.token_ana)
        resposta = self.compartilhar(self.token_ana, "primeiro_treino")
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        registro = resposta.get_json()["compartilhamento"]
        self.assertEqual(registro["tipo_conteudo"], "medalha")
        self.assertEqual(registro["chave_medalha"], "primeiro_treino")
        self.assertIsNone(registro["id_atividade"])
        self.assertIsNone(registro["id_meta"])

    def test_medalha_nao_conquistada_devolve_400(self):
        resposta = self.compartilhar(self.token_ana, "primeiro_treino")
        self.assertEqual(resposta.status_code, 400)

    def test_medalha_conquistada_por_outro_usuario_devolve_400(self):
        self.registrar_treino(self.token_ana)
        resposta = self.compartilhar(self.token_bia, "primeiro_treino")
        self.assertEqual(resposta.status_code, 400)

    def test_medalha_inexistente_devolve_404(self):
        self.registrar_treino(self.token_ana)
        resposta = self.compartilhar(self.token_ana, "medalha_que_nao_existe")
        self.assertEqual(resposta.status_code, 404)

    def test_medalha_sem_chave_devolve_400(self):
        self.registrar_treino(self.token_ana)
        resposta = self.compartilhar(self.token_ana)
        self.assertEqual(resposta.status_code, 400)

    def test_medalha_sem_consentimento_devolve_403(self):
        self.registrar_treino(self.token_ana)
        self.desativar_consentimento(self.token_ana, self.ana)
        resposta = self.compartilhar(self.token_ana, "primeiro_treino")
        self.assertEqual(resposta.status_code, 403)


class TestValidacaoCompartilhamento(BaseCompartilhamento):

    def test_tipo_conteudo_invalido_devolve_400(self):
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "desafio", "rede_social": "copiar"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 400)

    def test_rede_social_invalida_devolve_400(self):
        atividade = self.registrar_treino(self.token_ana)
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "atividade", "id_atividade": atividade["id"], "rede_social": "facebook"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 400)

    def test_sem_consentimento_devolve_403(self):
        self.desativar_consentimento(self.token_ana, self.ana)
        atividade = self.registrar_treino(self.token_ana)
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "atividade", "id_atividade": atividade["id"], "rede_social": "copiar"},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(resposta.status_code, 403)

    def test_exige_login(self):
        resposta = self.cli.post(
            "/api/compartilhamentos",
            json={"tipo_conteudo": "atividade", "id_atividade": 1, "rede_social": "copiar"},
        )
        self.assertEqual(resposta.status_code, 401)


if __name__ == "__main__":
    unittest.main()
