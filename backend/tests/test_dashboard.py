import unittest
from datetime import date, datetime, timedelta

from database import db
from models.model import Atividade
from tests.test_seguranca import BaseTeste
from utils import agora, data_local


class BaseDashboard(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Dashboard")
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Dashboard")

    def dashboard(self, token, exercicio=None):
        query = {"exercicio": exercicio} if exercicio else {}
        return self.cli.get("/api/dashboard", query_string=query, headers=self.auth(token))

    def registrar(self, token, tipo="musculacao", titulo="Supino Reto", carga=100, tempo=40, reps=5):
        resposta = self.cli.post(
            f"/api/usuarios/{self.ana['id']}/atividades",
            json={"tipo": tipo, "titulo": titulo, "tempo_min": tempo, "carga_kg": carga, "repeticoes": reps},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["atividade"]

    def forcar_data(self, id_atividade, data_registro):
        with self.app.app_context():
            atividade = db.session.get(Atividade, id_atividade)
            atividade.data_registro = data_registro
            db.session.commit()

    def utc_de_local(self, dia, hora, minuto=0):
        return datetime(dia.year, dia.month, dia.day, hora, minuto) + timedelta(hours=3)


class TestDashboardEstadoVazio(BaseDashboard):

    def test_exige_login(self):
        resposta = self.cli.get("/api/dashboard")
        self.assertEqual(resposta.status_code, 401)

    def test_sem_atividades_mostra_estado_vazio_honesto(self):
        resposta = self.dashboard(self.token_ana)
        self.assertEqual(resposta.status_code, 200)
        corpo = resposta.get_json()
        self.assertEqual(len(corpo["xp_por_semana"]), 8)
        self.assertTrue(all(s["xp"] == 0 for s in corpo["xp_por_semana"]))
        self.assertTrue(all(s["quantidade"] == 0 for s in corpo["treinos_por_semana"]))
        self.assertEqual(corpo["distribuicao_por_tipo"], {})
        self.assertEqual(corpo["sequencia_atual"], 0)
        self.assertEqual(corpo["melhor_sequencia"], 0)
        self.assertEqual(corpo["totais"], {"treinos": 0, "tempo_min": 0, "xp": 0})
        self.assertEqual(corpo["exercicios_disponiveis"], [])
        self.assertIsNone(corpo["exercicio_selecionado"])
        self.assertEqual(corpo["evolucao_carga"], [])


class TestDashboardComDados(BaseDashboard):

    def test_totais_e_distribuicao(self):
        self.registrar(self.token_ana, tipo="musculacao", tempo=40)
        self.registrar(self.token_ana, tipo="musculacao", tempo=30)
        self.registrar(self.token_ana, tipo="cardio", titulo="Corrida", carga=None, tempo=20)

        corpo = self.dashboard(self.token_ana).get_json()
        self.assertEqual(corpo["totais"]["treinos"], 3)
        self.assertEqual(corpo["totais"]["tempo_min"], 90)
        self.assertEqual(corpo["distribuicao_por_tipo"], {"musculacao": 2, "cardio": 1})

    def test_xp_da_semana_atual_bate_com_a_pontuacao_ganha(self):
        atividade = self.registrar(self.token_ana)
        corpo = self.dashboard(self.token_ana).get_json()
        self.assertEqual(len(corpo["xp_por_semana"]), 8)
        self.assertEqual(corpo["xp_por_semana"][-1]["xp"], atividade["pontuacao"])
        self.assertEqual(corpo["treinos_por_semana"][-1]["quantidade"], 1)

    def test_evolucao_de_carga_e_o_recorde_corrente_nao_a_carga_bruta(self):
        primeira = self.registrar(self.token_ana, carga=100)
        self.forcar_data(primeira["id"], date.today() - timedelta(days=2))
        self.registrar(self.token_ana, carga=90)
        self.registrar(self.token_ana, carga=120)

        corpo = self.dashboard(self.token_ana, exercicio="Supino Reto").get_json()
        self.assertEqual(corpo["exercicio_selecionado"], "Supino Reto")
        cargas_maximas = [p["carga_maxima"] for p in corpo["evolucao_carga"]]
        self.assertEqual(cargas_maximas, [100, 100, 120])

    def test_exercicio_padrao_e_o_com_mais_registros_de_carga(self):
        self.registrar(self.token_ana, titulo="Agachamento Livre", carga=80)
        self.registrar(self.token_ana, titulo="Supino Reto", carga=100)
        self.registrar(self.token_ana, titulo="Supino Reto", carga=102)
        self.registrar(self.token_ana, titulo="Supino Reto", carga=104)

        corpo = self.dashboard(self.token_ana).get_json()
        self.assertEqual(corpo["exercicio_selecionado"], "Supino Reto")
        self.assertEqual(len(corpo["evolucao_carga"]), 3)

    def test_sequencia_atual_e_melhor_sequencia(self):
        hoje = date.today()
        a1 = self.registrar(self.token_ana)
        self.forcar_data(a1["id"], hoje - timedelta(days=5))
        a2 = self.registrar(self.token_ana)
        self.forcar_data(a2["id"], hoje - timedelta(days=4))
        a3 = self.registrar(self.token_ana)
        self.forcar_data(a3["id"], hoje - timedelta(days=3))
        self.registrar(self.token_ana)

        corpo = self.dashboard(self.token_ana).get_json()
        self.assertEqual(corpo["sequencia_atual"], 1)
        self.assertEqual(corpo["melhor_sequencia"], 3)

    def test_treinos_as_08h_e_22h_em_dias_seguidos_formam_sequencia_de_dois_dias(self):
        hoje_local = data_local(agora())
        ontem_local = hoje_local - timedelta(days=1)

        a1 = self.registrar(self.token_ana)
        self.forcar_data(a1["id"], self.utc_de_local(ontem_local, 8))
        a2 = self.registrar(self.token_ana)
        self.forcar_data(a2["id"], self.utc_de_local(hoje_local, 22))

        corpo = self.dashboard(self.token_ana).get_json()
        self.assertEqual(corpo["sequencia_atual"], 2)
        self.assertEqual(corpo["melhor_sequencia"], 2)

    def test_treino_as_21h30_locais_conta_no_dia_local_correto(self):
        hoje_local = data_local(agora())
        timestamp_utc = self.utc_de_local(hoje_local, 21, 30)
        self.assertEqual(timestamp_utc.date(), hoje_local + timedelta(days=1))
        self.assertEqual((timestamp_utc.hour, timestamp_utc.minute), (0, 30))

        atividade = self.registrar(self.token_ana)
        self.forcar_data(atividade["id"], timestamp_utc)

        corpo = self.dashboard(self.token_ana).get_json()
        self.assertEqual(corpo["sequencia_atual"], 1)
        self.assertEqual(corpo["treinos_por_semana"][-1]["quantidade"], 1)
        self.assertEqual(corpo["xp_por_semana"][-1]["xp"], atividade["pontuacao"])

    def test_so_ve_os_proprios_dados(self):
        self.registrar(self.token_ana)
        corpo_bia = self.dashboard(self.token_bia).get_json()
        self.assertEqual(corpo_bia["totais"]["treinos"], 0)
        self.assertEqual(corpo_bia["exercicios_disponiveis"], [])


if __name__ == "__main__":
    unittest.main()
