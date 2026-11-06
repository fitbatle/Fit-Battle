from datetime import date, timedelta

from models.model import Desafio
from repositories.repository import DesafioRepository
from tests.test_seguranca import BaseTeste

HOJE = date(2026, 1, 20)


def criar_desafio(nome, inicio, fim):
    return Desafio(
        nome=nome, exercicio="livre", tipo_metrica="treinos", valor_objetivo=3,
        data_inicio=inicio, data_fim=fim, recompensa_xp=10,
    ).salvar()


class TestDesafioRepository(BaseTeste):

    def test_listar_ativos_so_traz_os_que_ainda_nao_terminaram_em_ordem_de_inicio(self):
        with self.app.app_context():
            criar_desafio("Repo Ativo Tarde", HOJE - timedelta(days=1), HOJE + timedelta(days=5))
            criar_desafio("Repo Ativo Cedo", HOJE - timedelta(days=9), HOJE + timedelta(days=1))
            criar_desafio("Repo Encerrado", HOJE - timedelta(days=20), HOJE - timedelta(days=2))
            linhas = DesafioRepository.listar_ativos(HOJE)
        nomes = [d["nome"] for d in linhas if d["nome"].startswith("Repo ")]
        self.assertEqual(nomes, ["Repo Ativo Cedo", "Repo Ativo Tarde"])
        self.assertIsInstance(linhas[0]["data_inicio"], date)
        self.assertIsInstance(linhas[0]["valor_objetivo"], float)

