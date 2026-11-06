from services.privacidade.apoio import CONSENTIMENTOS_OBRIGATORIOS, CONSENTIMENTOS_OPCIONAIS
from tests.test_seguranca import BaseTeste


class TestConsentimentosPadrao(BaseTeste):

    def consentimentos_do_usuario(self, email):
        token = self.entrar(email)
        usuario = self.cli.post("/api/login", json={"email": email, "senha": "senhaforte123"}).get_json()["usuario"]
        resposta = self.cli.get(
            f"/api/usuarios/{usuario['id']}/consentimentos",
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return {c["chave"]: c["aceito"] for c in resposta.get_json()}

    def test_opcionais_sem_escolha_ficam_nao_aceitos(self):
        self.cadastrar("Padrao Sem Escolha", email="padrao.sem.escolha@teste.com", consentimentos={})
        aceitos = self.consentimentos_do_usuario("padrao.sem.escolha@teste.com")
        for chave in CONSENTIMENTOS_OPCIONAIS:
            with self.subTest(chave=chave):
                self.assertIs(aceitos[chave], False)

    def test_obrigatorios_continuam_aceitos_sem_escolha(self):
        self.cadastrar("Padrao Obrigatorio", email="padrao.obrigatorio@teste.com", consentimentos={})
        aceitos = self.consentimentos_do_usuario("padrao.obrigatorio@teste.com")
        for chave in CONSENTIMENTOS_OBRIGATORIOS:
            with self.subTest(chave=chave):
                self.assertIs(aceitos[chave], True)

    def test_sem_ranking_publico_o_perfil_nao_aparece_na_busca_nem_no_ranking(self):
        self.cadastrar("Oculta Padrao", email="oculta.padrao@teste.com", consentimentos={})
        token = self.entrar("oculta.padrao@teste.com")
        perfil = self.cli.get("/api/eu", headers={"Authorization": "Bearer " + token}).get_json()["usuario"]
        self.assertIs(perfil["perfil_publico"], False)
        ranking = self.cli.get(
            "/api/ranking/global?limite=100", headers={"Authorization": "Bearer " + token}
        ).get_json()
        self.assertNotIn(perfil["id"], [linha["id_usuario"] for linha in ranking])

    def test_escolha_explicita_e_respeitada(self):
        self.cadastrar(
            "Escolha Explicita", email="escolha.explicita@teste.com",
            consentimentos={"ranking_publico": True, "busca_perfil": True},
        )
        aceitos = self.consentimentos_do_usuario("escolha.explicita@teste.com")
        self.assertIs(aceitos["ranking_publico"], True)
        self.assertIs(aceitos["busca_perfil"], True)
        self.assertIs(aceitos["notificacoes"], False)
