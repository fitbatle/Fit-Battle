from tests.test_seguranca import BaseTeste

CORPO = {"tipo": "musculacao", "titulo": "Supino Reto", "tempo_min": 40, "carga_kg": 100, "repeticoes": 5}


class BasePrevia(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Lia Previa")

    def previa(self, corpo=None, usuario=None, token=None):
        dono = usuario or self.usuario
        return self.cli.post(
            f"/api/usuarios/{dono['id']}/atividades/previa",
            json=corpo if corpo is not None else CORPO,
            headers=self.auth(token or self.token),
        )

    def registrar(self, corpo=None):
        resposta = self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/atividades",
            json=corpo if corpo is not None else CORPO,
            headers=self.auth(self.token),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()

    def historico(self):
        return self.cli.get(
            f"/api/usuarios/{self.usuario['id']}/atividades", headers=self.auth(self.token)
        ).get_json()

    def xp(self):
        return self.cli.get("/api/eu", headers=self.auth(self.token)).get_json()["usuario"]["xp"]


class TestPreviaAlinhadaAoRegistro(BasePrevia):

    def test_previa_e_igual_a_pontuacao_do_registro_real(self):
        resposta = self.previa()
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        estimada = resposta.get_json()["pontuacao_estimada"]
        registro = self.registrar()
        self.assertEqual(estimada, registro["pontuacao_ganha"])

    def test_previa_de_cardio_e_igual_ao_registro_real(self):
        corpo = {"tipo": "cardio", "titulo": "Corrida", "tempo_min": 30, "distancia_km": 5}
        estimada = self.previa(corpo).get_json()["pontuacao_estimada"]
        self.assertEqual(estimada, self.registrar(corpo)["pontuacao_ganha"])


class TestPreviaNaoGrava(BasePrevia):

    def test_previa_nao_grava_treino_nem_altera_xp(self):
        self.registrar()
        historico_antes = self.historico()
        xp_antes = self.xp()
        self.previa({"tipo": "cardio", "titulo": "Corrida", "tempo_min": 30, "distancia_km": 5})
        self.assertEqual(self.historico(), historico_antes)
        self.assertEqual(self.xp(), xp_antes)


class TestPreviaRecorde(BasePrevia):

    def test_recorde_verdadeiro_sem_treino_anterior(self):
        corpo = self.previa().get_json()
        self.assertIs(corpo["recorde_pessoal"], True)
        self.assertIsNone(corpo["recorde_atual"])

    def test_recorde_falso_com_carga_igual_e_verdadeiro_com_carga_maior(self):
        self.registrar()
        igual = self.previa().get_json()
        self.assertIs(igual["recorde_pessoal"], False)
        self.assertEqual(igual["recorde_atual"], 100.0)
        maior = self.previa({**CORPO, "carga_kg": 110}).get_json()
        self.assertIs(maior["recorde_pessoal"], True)
        self.assertEqual(maior["recorde_atual"], 100.0)

    def test_recorde_nao_vale_para_cardio(self):
        corpo = self.previa({"tipo": "cardio", "titulo": "Corrida", "tempo_min": 30, "distancia_km": 5}).get_json()
        self.assertIs(corpo["recorde_pessoal"], False)
        self.assertIsNone(corpo["recorde_atual"])


class TestPreviaLimitesDeXp(BasePrevia):

    def test_treino_acima_de_2000_xp_e_recusado_com_400(self):
        resposta = self.previa({**CORPO, "tempo_min": 600, "carga_kg": 301, "repeticoes": 460})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("2000 XP", resposta.get_json()["erro"])

    def test_limite_diario_recusa_a_previa_com_400(self):
        self.registrar({**CORPO, "tempo_min": 600, "carga_kg": 300, "repeticoes": 460})
        self.registrar({"tipo": "outro", "titulo": "Outro", "tempo_min": 600, "carga_kg": 395, "repeticoes": 100})
        resposta = self.previa({"tipo": "outro", "titulo": "Outro", "tempo_min": 10})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("3000", resposta.get_json()["erro"])


class TestPreviaAcesso(BasePrevia):

    def test_usuario_diferente_do_dono_e_recusado(self):
        outro, token_outro = self.criar_usuario_logado("Outra Previa")
        resposta = self.previa(usuario=self.usuario, token=token_outro)
        self.assertEqual(resposta.status_code, 403)

    def test_nao_logado_e_recusado(self):
        resposta = self.cli.post(f"/api/usuarios/{self.usuario['id']}/atividades/previa", json=CORPO)
        self.assertEqual(resposta.status_code, 401)

    def test_corpo_invalido_e_recusado_com_400(self):
        resposta = self.previa({"tipo": "tenis", "tempo_min": 10})
        self.assertEqual(resposta.status_code, 400)
