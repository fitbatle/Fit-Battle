from datetime import datetime, timedelta

from models.model import Comentario, Usuario
from repositories.repository import ComentarioRepository
from tests.test_seguranca import BaseTeste

HOJE = datetime(2026, 1, 20, 12, 0)


def criar_usuario(email):
    return Usuario(nome=email.split("@")[0], email=email, senha="hash", idade=30).salvar()


def comentar(id_usuario, tipo_alvo, id_alvo, texto, quando=HOJE):
    return Comentario(
        id_usuario=id_usuario, tipo_alvo=tipo_alvo, id_alvo=id_alvo, texto=texto, data_registro=quando,
    ).salvar()


class TestComentarioRepository(BaseTeste):

    def test_listar_traz_os_comentarios_do_alvo_do_mais_antigo_ao_mais_novo(self):
        with self.app.app_context():
            ana = criar_usuario("com.listar@repo.teste")
            comentar(ana.id_usuario, "atividade", 1000, "Segundo", quando=HOJE)
            comentar(ana.id_usuario, "atividade", 1000, "Primeiro", quando=HOJE - timedelta(hours=2))
            comentar(ana.id_usuario, "atividade", 1001, "Outro alvo", quando=HOJE)
            linhas = ComentarioRepository.listar("atividade", 1000)
        self.assertEqual([c["texto"] for c in linhas], ["Primeiro", "Segundo"])
        self.assertIsInstance(linhas[0], dict)
        self.assertIsInstance(linhas[0]["data_registro"], datetime)

    def test_contar_em_lote_conta_por_alvo_sem_misturar_tipos(self):
        with self.app.app_context():
            ana = criar_usuario("com.lote@repo.teste")
            comentar(ana.id_usuario, "postagem", 1010, "Um")
            comentar(ana.id_usuario, "postagem", 1010, "Dois")
            comentar(ana.id_usuario, "postagem", 1011, "Tres")
            comentar(ana.id_usuario, "atividade", 1010, "De atividade")
            lote = ComentarioRepository.contar_em_lote("postagem", [1010, 1011, 1012])
        self.assertEqual(lote, {1010: 2, 1011: 1})

    def test_contar_em_lote_sem_ids_devolve_vazio(self):
        with self.app.app_context():
            self.assertEqual(ComentarioRepository.contar_em_lote("postagem", []), {})

    def test_excluir_do_alvo_apaga_so_os_comentarios_daquele_alvo(self):
        with self.app.app_context():
            ana = criar_usuario("com.excl.alvo@repo.teste")
            comentar(ana.id_usuario, "atividade", 1020, "Some")
            comentar(ana.id_usuario, "atividade", 1021, "Fica")
            ComentarioRepository.excluir_do_alvo("atividade", 1020)
            self.assertEqual(ComentarioRepository.listar("atividade", 1020), [])
            self.assertEqual(len(ComentarioRepository.listar("atividade", 1021)), 1)

    def test_excluir_do_usuario_apaga_os_comentarios_dele_em_qualquer_alvo(self):
        with self.app.app_context():
            ana = criar_usuario("com.excl.user.a@repo.teste")
            bia = criar_usuario("com.excl.user.b@repo.teste")
            comentar(ana.id_usuario, "atividade", 1030, "Dela")
            comentar(ana.id_usuario, "postagem", 1031, "Dela tambem")
            comentar(bia.id_usuario, "atividade", 1030, "Da Bia")
            ComentarioRepository.excluir_do_usuario(ana.id_usuario)
            restantes = [c["texto"] for c in ComentarioRepository.listar("atividade", 1030)]
            postagem = ComentarioRepository.listar("postagem", 1031)
        self.assertEqual(restantes, ["Da Bia"])
        self.assertEqual(postagem, [])
