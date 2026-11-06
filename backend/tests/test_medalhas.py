import os
import sys
import unittest
from datetime import date, timedelta

os.environ["DB_URI"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models.atividade import Atividade
from models.usuario import Usuario
from tests.test_seguranca import BaseTeste
from utils import inicio_utc_do_dia_local

CHAVES = [
    "primeiro_treino", "constancia", "veterano", "semana_perfeita", "meta_batida", "maratonista",
    "categoria_intermediario", "categoria_avancado", "categoria_profissional", "categoria_elite",
]


class BaseMedalhas(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Medalha", idade=30)
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Medalha", idade=31)

    def medalhas(self, usuario, token):
        resposta = self.cli.get(f"/api/usuarios/{usuario['id']}/medalhas", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return {m["chave"]: m for m in resposta.get_json()}

    def minhas(self, usuario):
        return self.medalhas(usuario, self.token_do(usuario))

    def token_do(self, usuario):
        return self.token_ana if usuario["id"] == self.ana["id"] else self.token_bia

    def registrar_em(self, usuario, dia, distancia=None, hora=18.0):
        with self.app.app_context():
            atividade = Atividade(id_usuario=usuario["id"], **{
                "tipo": "cardio", "titulo": "Corrida teste", "descricao": None,
                "tempo_min": 20, "distancia_km": distancia, "carga_kg": None,
                "repeticoes": None, "pontuacao": 20,
            }).salvar()
            atividade.data_registro = inicio_utc_do_dia_local(dia) + timedelta(hours=hora)
            db.session.commit()
            return atividade.id_atividade

    def definir_xp(self, usuario, xp):
        with self.app.app_context():
            registro = Usuario.buscar_por_id(usuario["id"])
            registro.xp = xp
            db.session.commit()

    def hoje(self):
        return date.today()


class TestCalculoDasMedalhas(BaseMedalhas):

    def test_usuario_sem_atividades_tem_todas_bloqueadas_sem_data(self):
        medalhas = self.minhas(self.ana)
        self.assertEqual(sorted(medalhas), sorted(CHAVES))
        for medalha in medalhas.values():
            self.assertFalse(medalha["conquistada"])
            self.assertIsNone(medalha["data_conquista"])
        self.assertEqual(medalhas["primeiro_treino"]["progresso"], {"valor": 0, "meta": 1})

    def test_primeiro_treino_no_limite_exato(self):
        self.assertFalse(self.minhas(self.ana)["primeiro_treino"]["conquistada"])
        self.registrar_em(self.ana, self.hoje())
        medalha = self.minhas(self.ana)["primeiro_treino"]
        self.assertTrue(medalha["conquistada"])
        self.assertEqual(medalha["data_conquista"], self.hoje().isoformat())

    def test_constancia_exige_dez_atividades(self):
        for i in range(9):
            self.registrar_em(self.ana, self.hoje() - timedelta(days=i))
        self.assertFalse(self.minhas(self.ana)["constancia"]["conquistada"])
        self.assertEqual(self.minhas(self.ana)["constancia"]["progresso"], {"valor": 9, "meta": 10})
        self.registrar_em(self.ana, self.hoje() - timedelta(days=30))
        medalha = self.minhas(self.ana)["constancia"]
        self.assertTrue(medalha["conquistada"])
        self.assertEqual(medalha["data_conquista"], self.hoje().isoformat())

    def test_veterano_exige_cinquenta_atividades(self):
        for i in range(49):
            self.registrar_em(self.ana, self.hoje() - timedelta(days=i))
        self.assertFalse(self.minhas(self.ana)["veterano"]["conquistada"])
        self.registrar_em(self.ana, self.hoje() - timedelta(days=60))
        self.assertTrue(self.minhas(self.ana)["veterano"]["conquistada"])

    def test_semana_perfeita_exige_sete_dias_seguidos(self):
        inicio = self.hoje() - timedelta(days=20)
        for i in range(6):
            self.registrar_em(self.ana, inicio + timedelta(days=i))
        self.assertFalse(self.minhas(self.ana)["semana_perfeita"]["conquistada"])
        self.assertEqual(self.minhas(self.ana)["semana_perfeita"]["progresso"], {"valor": 6, "meta": 7})
        self.registrar_em(self.ana, inicio + timedelta(days=6))
        medalha = self.minhas(self.ana)["semana_perfeita"]
        self.assertTrue(medalha["conquistada"])
        self.assertEqual(medalha["data_conquista"], (inicio + timedelta(days=6)).isoformat())

    def test_semana_perfeita_nao_soma_dias_separados(self):
        inicio = self.hoje() - timedelta(days=30)
        for i in range(7):
            if i == 3:
                continue
            self.registrar_em(self.ana, inicio + timedelta(days=i))
        self.assertFalse(self.minhas(self.ana)["semana_perfeita"]["conquistada"])
        self.assertEqual(self.minhas(self.ana)["semana_perfeita"]["progresso"]["valor"], 3)

    def test_maratonista_no_limite_de_quarenta_e_dois_km(self):
        dia = self.hoje() - timedelta(days=5)
        self.registrar_em(self.ana, dia, distancia=41.9)
        self.assertFalse(self.minhas(self.ana)["maratonista"]["conquistada"])
        self.registrar_em(self.ana, dia + timedelta(days=1), distancia=0.1)
        medalha = self.minhas(self.ana)["maratonista"]
        self.assertTrue(medalha["conquistada"])
        self.assertEqual(medalha["data_conquista"], (dia + timedelta(days=1)).isoformat())

    def test_meta_batida_quando_o_progresso_real_atinge_o_objetivo(self):
        meta = self.cli.post("/api/metas", json={
            "titulo": "Supino 50", "tipo": "curto_prazo", "tipo_metrica": "carga_maxima",
            "exercicio": "supino", "valor_objetivo": 50, "data_final": "2031-01-01",
        }, headers=self.auth(self.token_ana))
        self.assertEqual(meta.status_code, 201, meta.get_data(as_text=True))
        self.assertFalse(self.minhas(self.ana)["meta_batida"]["conquistada"])
        treino = self.cli.post(f"/api/usuarios/{self.ana['id']}/atividades", json={
            "tipo": "musculacao", "titulo": "supino", "tempo_min": 30, "carga_kg": 60, "repeticoes": 8,
        }, headers=self.auth(self.token_ana))
        self.assertEqual(treino.status_code, 201, treino.get_data(as_text=True))
        self.assertTrue(self.minhas(self.ana)["meta_batida"]["conquistada"])

    def test_categoria_intermediario_no_limite_de_mil_xp(self):
        self.definir_xp(self.ana, 999)
        self.assertFalse(self.minhas(self.ana)["categoria_intermediario"]["conquistada"])
        self.definir_xp(self.ana, 1000)
        medalha = self.minhas(self.ana)["categoria_intermediario"]
        self.assertTrue(medalha["conquistada"])
        self.assertEqual(medalha["progresso"], {"valor": 1000, "meta": 1000})

    def test_categoria_sem_xp_de_atividades_fica_com_data_indisponivel(self):
        self.definir_xp(self.ana, 1500)
        medalha = self.minhas(self.ana)["categoria_intermediario"]
        self.assertTrue(medalha["conquistada"])
        self.assertIsNone(medalha["data_conquista"])

    def test_categoria_com_xp_de_atividades_usa_a_data_em_que_o_total_cruzou(self):
        dia = self.hoje() - timedelta(days=4)
        with self.app.app_context():
            for i in range(60):
                atividade = Atividade(id_usuario=self.ana["id"], **{
                    "tipo": "cardio", "titulo": "Corrida", "descricao": None, "tempo_min": 20,
                    "distancia_km": None, "carga_kg": None, "repeticoes": None, "pontuacao": 20,
                }).salvar()
                atividade.data_registro = inicio_utc_do_dia_local(dia + timedelta(days=i // 30)) + timedelta(hours=18)
            db.session.commit()
            Usuario.buscar_por_id(self.ana["id"]).xp = 1200
            db.session.commit()
        medalha = self.minhas(self.ana)["categoria_intermediario"]
        self.assertTrue(medalha["conquistada"])
        self.assertEqual(medalha["data_conquista"], (dia + timedelta(days=1)).isoformat())


class TestVisibilidadeDasMedalhas(BaseMedalhas):

    def test_dois_usuarios_nao_se_misturam(self):
        self.registrar_em(self.ana, self.hoje())
        self.assertTrue(self.minhas(self.ana)["primeiro_treino"]["conquistada"])
        self.assertFalse(self.minhas(self.bia)["primeiro_treino"]["conquistada"])

    def test_outro_usuario_ve_so_as_conquistadas(self):
        self.registrar_em(self.ana, self.hoje())
        visto = self.medalhas(self.ana, self.token_bia)
        self.assertEqual(sorted(visto), ["primeiro_treino"])

    def test_menor_visto_por_outro_usuario_recebe_404(self):
        menor, token_menor = self.criar_usuario_logado(
            "Lia Menor", idade=15, responsavel={"nome": "Responsavel Teste", "email": "resp.lia@teste.com"}
        )
        self.registrar_em(menor, self.hoje())
        resposta = self.cli.get(f"/api/usuarios/{menor['id']}/medalhas", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 404)
        proprias = self.cli.get(f"/api/usuarios/{menor['id']}/medalhas", headers=self.auth(token_menor))
        self.assertEqual(proprias.status_code, 200)
        self.assertTrue({m["chave"]: m for m in proprias.get_json()}["primeiro_treino"]["conquistada"])

    def test_perfil_privado_visto_por_outro_recebe_404(self):
        self.cli.put(
            f"/api/usuarios/{self.bia['id']}/consentimentos/ranking_publico",
            json={"aceito": False}, headers=self.auth(self.token_bia),
        )
        self.registrar_em(self.bia, self.hoje())
        resposta = self.cli.get(f"/api/usuarios/{self.bia['id']}/medalhas", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 404)

    def test_exige_login(self):
        resposta = self.cli.get(f"/api/usuarios/{self.ana['id']}/medalhas")
        self.assertEqual(resposta.status_code, 401)

    def test_exclusao_de_atividade_tira_a_medalha(self):
        ids = [self.registrar_em(self.ana, self.hoje() - timedelta(days=i)) for i in range(10)]
        self.assertTrue(self.minhas(self.ana)["constancia"]["conquistada"])
        excluido = self.cli.delete(f"/api/atividades/{ids[0]}", headers=self.auth(self.token_ana))
        self.assertEqual(excluido.status_code, 200)
        medalha = self.minhas(self.ana)["constancia"]
        self.assertFalse(medalha["conquistada"])
        self.assertEqual(medalha["progresso"], {"valor": 9, "meta": 10})


class TestFusoLocal(BaseMedalhas):

    def test_treino_as_23h30_locais_conta_no_dia_local_e_nao_no_dia_seguinte_utc(self):
        dia = self.hoje() - timedelta(days=3)
        self.registrar_em(self.ana, dia, hora=23.5)
        medalha = self.minhas(self.ana)["primeiro_treino"]
        self.assertEqual(medalha["data_conquista"], dia.isoformat())

    def test_semana_perfeita_respeita_o_dia_local(self):
        inicio = self.hoje() - timedelta(days=12)
        for i in range(7):
            self.registrar_em(self.ana, inicio + timedelta(days=i), hora=23.5)
        medalha = self.minhas(self.ana)["semana_perfeita"]
        self.assertTrue(medalha["conquistada"])
        self.assertEqual(medalha["data_conquista"], (inicio + timedelta(days=6)).isoformat())


class TestAvisoDeMedalhaNova(BaseMedalhas):

    def treinar(self, usuario, token, quantidade=1):
        ids = []
        for _ in range(quantidade):
            resposta = self.cli.post(
                f"/api/usuarios/{usuario['id']}/atividades",
                json={"tipo": "cardio", "titulo": "Corrida", "tempo_min": 20},
                headers=self.auth(token),
            )
            self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
            ids.append(resposta.get_json()["atividade"]["id"])
        return ids

    def avisos(self, token):
        resposta = self.cli.get("/api/notificacoes", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        return [n["mensagem"] for n in resposta.get_json() if n["tipo"] == "medalha"]

    def test_primeiro_treino_gera_um_aviso(self):
        self.treinar(self.ana, self.token_ana)
        self.assertEqual(self.avisos(self.token_ana), ['Você conquistou a medalha "Primeiro treino".'])

    def test_treinos_seguintes_nao_repetem_o_aviso(self):
        self.treinar(self.ana, self.token_ana, 3)
        self.assertEqual(self.avisos(self.token_ana), ['Você conquistou a medalha "Primeiro treino".'])

    def test_decimo_treino_gera_aviso_de_constancia_uma_vez(self):
        self.treinar(self.ana, self.token_ana, 11)
        avisos = self.avisos(self.token_ana)
        self.assertEqual(avisos.count('Você conquistou a medalha "Constância".'), 1)
        self.assertEqual(avisos.count('Você conquistou a medalha "Primeiro treino".'), 1)

    def test_sem_consentimento_de_notificacoes_nao_gera_aviso(self):
        self.cli.put(
            f"/api/usuarios/{self.ana['id']}/consentimentos/notificacoes",
            json={"aceito": False}, headers=self.auth(self.token_ana),
        )
        self.treinar(self.ana, self.token_ana)
        self.assertEqual(self.avisos(self.token_ana), [])

    def test_medalha_perdida_e_recuperada_nao_repete_o_aviso(self):
        ids = self.treinar(self.ana, self.token_ana)
        self.cli.delete(f"/api/atividades/{ids[0]}", headers=self.auth(self.token_ana))
        self.treinar(self.ana, self.token_ana)
        self.assertEqual(self.avisos(self.token_ana), ['Você conquistou a medalha "Primeiro treino".'])


if __name__ == "__main__":
    unittest.main()
