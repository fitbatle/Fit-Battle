from tests.test_seguranca import BaseTeste


class BaseLimitesXp(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Lia Limites")

    def registrar(self, **campos):
        corpo = {"tipo": "musculacao", "titulo": "Teste", "tempo_min": 600, "carga_kg": 300, "repeticoes": 460}
        corpo.update(campos)
        return self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/atividades",
            json=corpo,
            headers=self.auth(self.token),
        )

    def historico(self):
        resposta = self.cli.get(f"/api/usuarios/{self.usuario['id']}/atividades", headers=self.auth(self.token))
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_json()

    def xp_atual(self):
        resposta = self.cli.get("/api/eu", headers=self.auth(self.token))
        return resposta.get_json()["usuario"]["xp"]


class TestLimiteDeXpPorTreino(BaseLimitesXp):

    def test_treino_de_2000_xp_e_aceito(self):
        resposta = self.registrar()
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        self.assertEqual(resposta.get_json()["pontuacao_ganha"], 2000)

    def test_treino_acima_de_2000_xp_e_recusado_com_400(self):
        resposta = self.registrar(carga_kg=301, repeticoes=460)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("2000 XP", resposta.get_json()["erro"])

    def test_treino_recusado_nao_e_gravado_nem_soma_xp(self):
        self.registrar(carga_kg=301, repeticoes=460)
        self.assertEqual(self.historico(), [])
        self.assertEqual(self.xp_atual(), 0)

    def test_treino_recusado_nao_e_cortado_para_o_limite(self):
        resposta = self.registrar(carga_kg=500, repeticoes=1000)
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.historico(), [])


class TestLimiteDeXpPorDia(BaseLimitesXp):

    def registrar_ate_o_limite_do_dia(self):
        self.assertEqual(self.registrar().status_code, 201)
        resposta = self.registrar(tipo="outro", tempo_min=600, carga_kg=395, repeticoes=100)
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        self.assertEqual(resposta.get_json()["pontuacao_ganha"], 1000)

    def test_total_de_3000_xp_no_dia_e_aceito(self):
        self.registrar_ate_o_limite_do_dia()
        self.assertEqual(self.xp_atual(), 3000)

    def test_treino_que_estoura_3000_xp_no_dia_e_recusado_com_400(self):
        self.registrar_ate_o_limite_do_dia()
        resposta = self.registrar(tipo="outro", tempo_min=10, carga_kg=None, repeticoes=None)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("3000", resposta.get_json()["erro"])

    def test_treino_recusado_pelo_limite_diario_nao_e_gravado(self):
        self.registrar_ate_o_limite_do_dia()
        self.registrar(tipo="outro", tempo_min=10, carga_kg=None, repeticoes=None)
        self.assertEqual(len(self.historico()), 2)
        self.assertEqual(self.xp_atual(), 3000)
