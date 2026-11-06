from services.atividade.registrar_treino import RegistrarTreinoService
from tests.test_seguranca import BaseTeste

PREFIXO = "Novo recorde pessoal!"


class BaseRecorde(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Rafa Recorde")

    def registrar(self, titulo="Supino Reto", carga=100, tipo="musculacao", descricao=None,
                  usuario=None, token=None):
        dono = usuario or self.usuario
        corpo = {"tipo": tipo, "titulo": titulo, "tempo_min": 40, "carga_kg": carga, "repeticoes": 5}
        if descricao is not None:
            corpo["descricao"] = descricao
        resposta = self.cli.post(
            f"/api/usuarios/{dono['id']}/atividades",
            json=corpo,
            headers=self.auth(token or self.token),
        )
        return resposta

    def registrar_com_sucesso(self, **kwargs):
        resposta = self.registrar(**kwargs)
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()


class TestRecordePessoalNaRota(BaseRecorde):

    def test_primeiro_treino_do_exercicio_e_recorde(self):
        corpo = self.registrar_com_sucesso()
        self.assertIs(corpo["recorde_pessoal"], True)
        self.assertEqual(corpo["atividade"]["descricao"], PREFIXO)

    def test_carga_maior_que_a_anterior_e_recorde(self):
        self.registrar_com_sucesso(carga=100)
        corpo = self.registrar_com_sucesso(carga=110)
        self.assertIs(corpo["recorde_pessoal"], True)
        self.assertEqual(corpo["atividade"]["descricao"], PREFIXO)

    def test_carga_igual_a_anterior_nao_e_recorde(self):
        self.registrar_com_sucesso(carga=100)
        corpo = self.registrar_com_sucesso(carga=100)
        self.assertIs(corpo["recorde_pessoal"], False)
        self.assertIsNone(corpo["atividade"]["descricao"])

    def test_carga_menor_que_a_anterior_nao_e_recorde(self):
        self.registrar_com_sucesso(carga=100)
        corpo = self.registrar_com_sucesso(carga=90)
        self.assertIs(corpo["recorde_pessoal"], False)

    def test_titulo_sem_diferenca_de_caixa_ou_espacos_e_o_mesmo_exercicio(self):
        self.registrar_com_sucesso(titulo="Supino Reto", carga=100)
        corpo = self.registrar_com_sucesso(titulo="  supino reto ", carga=100)
        self.assertIs(corpo["recorde_pessoal"], False)

    def test_outro_exercicio_comeca_do_zero(self):
        self.registrar_com_sucesso(titulo="Supino Reto", carga=100)
        corpo = self.registrar_com_sucesso(titulo="Agachamento", carga=50)
        self.assertIs(corpo["recorde_pessoal"], True)

    def test_recorde_nao_vale_para_cardio(self):
        corpo = self.registrar_com_sucesso(tipo="cardio", titulo="Corrida", carga=None)
        self.assertIs(corpo["recorde_pessoal"], False)

    def test_descricao_do_usuario_e_preservada_depois_do_prefixo(self):
        corpo = self.registrar_com_sucesso(descricao="Boa sessão")
        self.assertEqual(corpo["atividade"]["descricao"], PREFIXO + " Boa sessão")

    def test_descricao_que_estoura_o_limite_com_o_prefixo_e_recusada_so_no_recorde(self):
        longa = "a" * 490
        resposta = self.registrar(descricao=longa)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("recorde pessoal", resposta.get_json()["erro"])

        self.registrar_com_sucesso(carga=100)
        corpo = self.registrar_com_sucesso(carga=90, descricao=longa)
        self.assertIs(corpo["recorde_pessoal"], False)
        self.assertEqual(corpo["atividade"]["descricao"], longa)

    def test_recorde_e_isolado_por_usuario(self):
        outra, token_outra = self.criar_usuario_logado("Outra Recorde")
        self.registrar_com_sucesso(carga=100)
        corpo = self.registrar_com_sucesso(usuario=outra, token=token_outra, carga=100)
        self.assertIs(corpo["recorde_pessoal"], True)


class TestRecordePessoalNoServico(BaseRecorde):

    def test_servico_devolve_o_indicador_de_recorde(self):
        dados = {"tipo": "musculacao", "titulo": "Remada", "tempo_min": 30, "carga_kg": 50, "repeticoes": 8}
        with self.app.app_context():
            _, _, recorde = RegistrarTreinoService.executar(self.usuario["id"], dict(dados))
            self.assertIs(recorde, True)
            _, _, recorde = RegistrarTreinoService.executar(self.usuario["id"], dict(dados))
            self.assertIs(recorde, False)
