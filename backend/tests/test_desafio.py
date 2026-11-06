import unittest
from datetime import date, timedelta
from unittest import mock

from tests.test_seguranca import BaseTeste
from utils import agora

ADMIN_EMAIL = "admin@teste.com"


class BaseDesafio(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Desafio")
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Desafio")
        self.admin, self.token_admin = self.criar_usuario_logado("Admin Geral", email=ADMIN_EMAIL)
        self._patch_admin = mock.patch.dict("os.environ", {"ADMIN_EMAILS": ADMIN_EMAIL})
        self._patch_admin.start()
        self.addCleanup(self._patch_admin.stop)

    def corpo_desafio(self, **extra):
        hoje = date.today()
        corpo = {
            "nome": "Desafio de Outubro",
            "descricao": "Treine bastante este mês.",
            "exercicio": "livre",
            "tipo_metrica": "treinos",
            "valor_objetivo": 3,
            "data_inicio": hoje.isoformat(),
            "data_fim": (hoje + timedelta(days=7)).isoformat(),
            "recompensa_xp": 50,
        }
        corpo.update(extra)
        return corpo

    def criar_desafio(self, token=None, **extra):
        resposta = self.cli.post(
            "/api/desafios", json=self.corpo_desafio(**extra), headers=self.auth(token or self.token_admin)
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["desafio"]

    def treinar(self, token, usuario, titulo="Supino Reto", carga=100, tempo=40, reps=5):
        resposta = self.cli.post(
            f"/api/usuarios/{usuario['id']}/atividades",
            json={"tipo": "musculacao", "titulo": titulo, "tempo_min": tempo, "carga_kg": carga, "repeticoes": reps},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["atividade"]

    def listar(self, token):
        resposta = self.cli.get("/api/desafios", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_json()


class TestPermissaoDeAdministracao(BaseDesafio):

    def test_usuario_comum_nao_cria_desafio(self):
        resposta = self.cli.post("/api/desafios", json=self.corpo_desafio(), headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 403)

    def test_admin_cria_desafio(self):
        desafio = self.criar_desafio()
        self.assertEqual(desafio["nome"], "Desafio de Outubro")
        self.assertEqual(desafio["tipo_metrica"], "treinos")

    def test_usuario_comum_nao_edita_nem_encerra(self):
        desafio = self.criar_desafio()
        resposta = self.cli.put(
            f"/api/desafios/{desafio['id']}", json={"nome": "Hackeado"}, headers=self.auth(self.token_ana)
        )
        self.assertEqual(resposta.status_code, 403)
        resposta = self.cli.put(f"/api/desafios/{desafio['id']}/encerrar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 403)

    def test_admin_edita_e_encerra(self):
        desafio = self.criar_desafio()
        resposta = self.cli.put(
            f"/api/desafios/{desafio['id']}", json={"nome": "Novo nome"}, headers=self.auth(self.token_admin)
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["desafio"]["nome"], "Novo nome")

        resposta = self.cli.put(f"/api/desafios/{desafio['id']}/encerrar", headers=self.auth(self.token_admin))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.get_json()["desafio"]["data_fim"],
            (agora().date() - timedelta(days=1)).isoformat(),
        )

        self.assertEqual(self.listar(self.token_ana), [])

    def test_encerrar_desafio_em_andamento_mantem_data_inicio_anterior_ao_fim(self):
        hoje = agora().date()
        desafio = self.criar_desafio(
            data_inicio=(hoje - timedelta(days=5)).isoformat(),
            data_fim=(hoje + timedelta(days=5)).isoformat(),
        )

        resposta = self.cli.put(f"/api/desafios/{desafio['id']}/encerrar", headers=self.auth(self.token_admin))
        self.assertEqual(resposta.status_code, 200)
        encerrado = resposta.get_json()["desafio"]
        self.assertEqual(encerrado["data_fim"], (hoje - timedelta(days=1)).isoformat())
        self.assertEqual(encerrado["data_inicio"], (hoje - timedelta(days=5)).isoformat())
        self.assertLessEqual(encerrado["data_inicio"], encerrado["data_fim"])

        resposta = self.cli.put(
            f"/api/desafios/{desafio['id']}", json={"nome": "Renomeado após encerrar"},
            headers=self.auth(self.token_admin),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["desafio"]["nome"], "Renomeado após encerrar")

        detalhe = self.cli.get(f"/api/desafios/{desafio['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(self.listar(self.token_ana), [])

    def test_encerrar_desafio_futuro_nao_deixa_fim_antes_do_inicio(self):
        hoje = agora().date()
        desafio = self.criar_desafio(
            data_inicio=(hoje + timedelta(days=10)).isoformat(),
            data_fim=(hoje + timedelta(days=20)).isoformat(),
        )

        resposta = self.cli.put(f"/api/desafios/{desafio['id']}/encerrar", headers=self.auth(self.token_admin))
        self.assertEqual(resposta.status_code, 200)
        encerrado = resposta.get_json()["desafio"]
        self.assertEqual(encerrado["data_fim"], (hoje - timedelta(days=1)).isoformat())
        self.assertEqual(encerrado["data_inicio"], encerrado["data_fim"])

        resposta = self.cli.put(
            f"/api/desafios/{desafio['id']}", json={"nome": "Cancelado antes de começar"},
            headers=self.auth(self.token_admin),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["desafio"]["nome"], "Cancelado antes de começar")

        detalhe = self.cli.get(f"/api/desafios/{desafio['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(detalhe.get_json()["minha_inscricao"]["percentual"], 0)
        self.assertEqual(self.listar(self.token_ana), [])


class TestListagemEInscricao(BaseDesafio):

    def test_desafio_encerrado_nao_aparece_na_listagem(self):
        hoje = date.today()
        self.criar_desafio(data_inicio=(hoje - timedelta(days=10)).isoformat(), data_fim=(hoje - timedelta(days=1)).isoformat())
        self.assertEqual(self.listar(self.token_ana), [])

    def test_lista_mostra_inscricao_propria_como_nula_antes_de_participar(self):
        self.criar_desafio()
        desafios = self.listar(self.token_ana)
        self.assertEqual(len(desafios), 1)
        self.assertIsNone(desafios[0]["minha_inscricao"]["status"])

    def test_participar_e_depois_listar_mostra_inscrito(self):
        desafio = self.criar_desafio()
        resposta = self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["desafio"]["minha_inscricao"]["status"], "inscrito")

        desafios = self.listar(self.token_ana)
        self.assertEqual(desafios[0]["minha_inscricao"]["status"], "inscrito")

    def test_nao_pode_participar_duas_vezes(self):
        desafio = self.criar_desafio()
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        resposta = self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 409)

    def test_participar_de_desafio_inexistente_e_404(self):
        resposta = self.cli.post("/api/desafios/999999/participar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 404)

    def test_desistir_e_depois_pode_participar_de_novo(self):
        desafio = self.criar_desafio()
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))

        resposta = self.cli.delete(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["desafio"]["minha_inscricao"]["status"], "desistiu")

        resposta = self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["desafio"]["minha_inscricao"]["status"], "inscrito")

    def test_desistir_sem_estar_inscrito_e_404(self):
        desafio = self.criar_desafio()
        resposta = self.cli.delete(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 404)

    def test_cada_usuario_so_ve_e_mexe_na_propria_inscricao(self):
        desafio = self.criar_desafio()
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))

        desafios_bia = self.listar(self.token_bia)
        self.assertIsNone(desafios_bia[0]["minha_inscricao"]["status"])

        resposta = self.cli.delete(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_bia))
        self.assertEqual(resposta.status_code, 404)


class TestProgressoETiposDeMetrica(BaseDesafio):

    def test_progresso_de_treinos_conta_qualquer_exercicio_quando_livre(self):
        desafio = self.criar_desafio(tipo_metrica="treinos", exercicio="livre", valor_objetivo=2)
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))

        self.treinar(self.token_ana, self.ana, titulo="Supino Reto")
        detalhe = self._detalhe(desafio["id"], self.token_ana)
        self.assertEqual(detalhe["minha_inscricao"]["valor_atual"], 1)
        self.assertEqual(detalhe["minha_inscricao"]["status"], "inscrito")

        self.treinar(self.token_ana, self.ana, titulo="Corrida")
        detalhe = self._detalhe(desafio["id"], self.token_ana)
        self.assertEqual(detalhe["minha_inscricao"]["valor_atual"], 2)
        self.assertEqual(detalhe["minha_inscricao"]["status"], "concluido")

    def test_progresso_de_treinos_filtra_por_exercicio_especifico(self):
        desafio = self.criar_desafio(tipo_metrica="treinos", exercicio="Supino Reto", valor_objetivo=2)
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))

        self.treinar(self.token_ana, self.ana, titulo="Corrida")
        detalhe = self._detalhe(desafio["id"], self.token_ana)
        self.assertEqual(detalhe["minha_inscricao"]["valor_atual"], 0)

        self.treinar(self.token_ana, self.ana, titulo="Supino Reto")
        self.treinar(self.token_ana, self.ana, titulo="Supino Reto")
        detalhe = self._detalhe(desafio["id"], self.token_ana)
        self.assertEqual(detalhe["minha_inscricao"]["valor_atual"], 2)
        self.assertEqual(detalhe["minha_inscricao"]["status"], "concluido")

    def test_progresso_de_carga_maxima(self):
        desafio = self.criar_desafio(tipo_metrica="carga_maxima", exercicio="Supino Reto", valor_objetivo=100)
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))

        self.treinar(self.token_ana, self.ana, titulo="Supino Reto", carga=80)
        detalhe = self._detalhe(desafio["id"], self.token_ana)
        self.assertEqual(detalhe["minha_inscricao"]["valor_atual"], 80)
        self.assertEqual(detalhe["minha_inscricao"]["status"], "inscrito")

        self.treinar(self.token_ana, self.ana, titulo="Supino Reto", carga=120)
        detalhe = self._detalhe(desafio["id"], self.token_ana)
        self.assertEqual(detalhe["minha_inscricao"]["valor_atual"], 120)
        self.assertEqual(detalhe["minha_inscricao"]["status"], "concluido")

    def test_treino_fora_do_periodo_nao_conta(self):
        hoje = date.today()
        desafio = self.criar_desafio(
            tipo_metrica="treinos", exercicio="livre", valor_objetivo=1,
            data_inicio=(hoje + timedelta(days=5)).isoformat(),
            data_fim=(hoje + timedelta(days=10)).isoformat(),
        )
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.treinar(self.token_ana, self.ana)
        detalhe = self._detalhe(desafio["id"], self.token_ana)
        self.assertEqual(detalhe["minha_inscricao"]["valor_atual"], 0)
        self.assertEqual(detalhe["minha_inscricao"]["status"], "inscrito")

    def _detalhe(self, id_desafio, token):
        resposta = self.cli.get(f"/api/desafios/{id_desafio}", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_json()


class TestConclusaoRecompensaENotificacao(BaseDesafio):

    def test_conclusao_credita_xp_uma_unica_vez_e_notifica(self):
        desafio = self.criar_desafio(tipo_metrica="treinos", exercicio="livre", valor_objetivo=1, recompensa_xp=50)
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))

        xp_antes = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana)).get_json()["xp"]
        atividade = self.treinar(self.token_ana, self.ana)
        xp_depois = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana)).get_json()["xp"]
        self.assertEqual(xp_depois, xp_antes + atividade["pontuacao"] + 50)

        self._detalhe(desafio["id"], self.token_ana)
        self._detalhe(desafio["id"], self.token_ana)
        xp_final = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana)).get_json()["xp"]
        self.assertEqual(xp_final, xp_depois)

        notificacoes = [
            n for n in self.cli.get("/api/notificacoes", headers=self.auth(self.token_ana)).get_json()
            if n["tipo"] == "desafio_concluido"
        ]
        self.assertEqual(len(notificacoes), 1)

    def test_participar_de_desafio_ja_concluido_e_409_sem_novo_xp(self):
        desafio = self.criar_desafio(tipo_metrica="treinos", exercicio="livre", valor_objetivo=1, recompensa_xp=50)
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.treinar(self.token_ana, self.ana)
        xp_antes = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana)).get_json()["xp"]

        resposta = self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 409)
        self.assertIn("concluiu", resposta.get_json()["erro"])

        xp_depois = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana)).get_json()["xp"]
        self.assertEqual(xp_depois, xp_antes)
        self.assertEqual(self.listar(self.token_ana)[0]["minha_inscricao"]["status"], "concluido")

    def test_conclusao_avaliada_ao_ler_tambem(self):
        desafio = self.criar_desafio(tipo_metrica="treinos", exercicio="livre", valor_objetivo=1, recompensa_xp=0)
        self.cli.post(f"/api/desafios/{desafio['id']}/participar", headers=self.auth(self.token_ana))
        self.treinar(self.token_ana, self.ana)

        desafios = self.listar(self.token_ana)
        self.assertEqual(desafios[0]["minha_inscricao"]["status"], "concluido")

    def _detalhe(self, id_desafio, token):
        resposta = self.cli.get(f"/api/desafios/{id_desafio}", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_json()


if __name__ == "__main__":
    unittest.main()


class TestValidacaoNumericaDeDesafio(BaseDesafio):

    def test_desafio_com_valor_objetivo_nan_e_400(self):
        resposta = self.cli.post(
            "/api/desafios", json=self.corpo_desafio(valor_objetivo="nan"), headers=self.auth(self.token_admin)
        )
        self.assertEqual(resposta.status_code, 400)

    def test_desafio_com_valor_objetivo_acima_do_maximo_e_400(self):
        resposta = self.cli.post(
            "/api/desafios", json=self.corpo_desafio(valor_objetivo=1e308), headers=self.auth(self.token_admin)
        )
        self.assertEqual(resposta.status_code, 400)
