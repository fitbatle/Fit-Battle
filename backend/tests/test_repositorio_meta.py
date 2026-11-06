from datetime import date

from models.model import Meta, Usuario
from repositories.repository import MetaRepository
from tests.test_seguranca import BaseTeste


def criar_usuario(email):
    return Usuario(nome=email.split("@")[0], email=email, senha="hash", idade=30).salvar()


def criar_meta(id_usuario, descricao, inicio):
    return Meta(
        id_usuario=id_usuario, descricao=descricao, tipo="curto_prazo", tipo_metrica="frequencia",
        valor_objetivo=5, valor_partida=0, data_inicio=inicio, status="em_andamento",
    ).salvar()


class TestMetaRepository(BaseTeste):

    def test_listar_do_usuario_da_meta_mais_recente_para_a_mais_antiga(self):
        with self.app.app_context():
            ana = criar_usuario("meta.lista@repo.teste")
            bia = criar_usuario("meta.lista.outra@repo.teste")
            criar_meta(ana.id_usuario, "Antiga", date(2026, 1, 1))
            criar_meta(ana.id_usuario, "Recente", date(2026, 2, 1))
            criar_meta(bia.id_usuario, "Alheia", date(2026, 3, 1))
            linhas = MetaRepository.listar_do_usuario(ana.id_usuario)
        self.assertEqual([m["descricao"] for m in linhas], ["Recente", "Antiga"])
        self.assertIsInstance(linhas[0]["data_inicio"], date)
        self.assertEqual(linhas[0]["valor_objetivo"], 5.0)
        self.assertIsInstance(linhas[0]["valor_objetivo"], float)

    def test_listar_do_usuario_sem_metas_devolve_lista_vazia(self):
        with self.app.app_context():
            ana = criar_usuario("meta.vazia@repo.teste")
            self.assertEqual(MetaRepository.listar_do_usuario(ana.id_usuario), [])
