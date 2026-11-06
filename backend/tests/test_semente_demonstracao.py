import os
import unittest
from datetime import date, timedelta

os.environ["DB_URI"] = "sqlite:///:memory:"

from app import criar_app
from database import db
from models.model import Atividade, Desafio, Usuario
from tests.apoio import criar_views_de_ranking
from tests.servidor_dev import PRINCIPAL, USUARIOS, planos_de_treino, popular

SEGUNDA_DE_REFERENCIA = date(2026, 11, 2)
SEMANAS_ESPERADAS = [2, 3, 1, 4, 2, 3, 1, 3]


class TestSementeDemonstracao(unittest.TestCase):

    def test_desafio_mostra_3_de_5_em_qualquer_dia_da_semana(self):
        for deslocamento in range(7):
            hoje = SEGUNDA_DE_REFERENCIA + timedelta(days=deslocamento)
            with self.subTest(dia=hoje.isoformat()):
                app = criar_app()
                with app.app_context():
                    criar_views_de_ranking(db)
                    popular(hoje)
                    helena = Usuario.query.filter_by(email=PRINCIPAL).first()
                    desafio = Desafio.query.first()
                    atividades = Atividade.query.filter_by(id_usuario=helena.id_usuario).all()
                    progresso = sum(
                        1 for atividade in atividades
                        if desafio.data_inicio <= atividade.data_registro.date() <= desafio.data_fim
                    )
                    self.assertEqual(progresso, 3)
                    self.assertEqual((desafio.data_fim - desafio.data_inicio).days + 1, 7)
                    self.assertTrue(all(a.data_registro.date() <= hoje for a in atividades))

    def test_treinos_por_semana_da_helena_seguem_o_padrao(self):
        for deslocamento in range(7):
            hoje = SEGUNDA_DE_REFERENCIA + timedelta(days=deslocamento)
            with self.subTest(dia=hoje.isoformat()):
                semanas = [0] * 8
                inicio_atual = hoje - timedelta(days=hoje.weekday())
                for treino in planos_de_treino(hoje)[PRINCIPAL]:
                    dia = hoje - timedelta(days=treino["dias_atras"])
                    inicio = dia - timedelta(days=dia.weekday())
                    semanas[7 - (inicio_atual - inicio).days // 7] += 1
                self.assertEqual(semanas, SEMANAS_ESPERADAS)

    def test_ranking_tem_helena_em_primeiro_e_podio_sem_empate(self):
        app = criar_app()
        with app.app_context():
            criar_views_de_ranking(db)
            popular(SEGUNDA_DE_REFERENCIA)
            xps = sorted((usuario.xp for usuario in Usuario.query.all()), reverse=True)
            helena = Usuario.query.filter_by(email=PRINCIPAL).first()
            self.assertEqual(xps[0], helena.xp)
            self.assertEqual(len(set(xps[:3])), 3)
            self.assertGreaterEqual(min(xps), 200)
            self.assertLessEqual(xps[1], 1400)
            self.assertEqual(len(xps), len(USUARIOS))


if __name__ == "__main__":
    unittest.main()
