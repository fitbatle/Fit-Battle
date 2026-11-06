from datetime import date, timedelta

from models.model import Desafio, DesafioUsuario, Usuario
from repositories.repository import DesafioUsuarioRepository
from tests.test_seguranca import BaseTeste

HOJE = date(2026, 1, 20)


def criar_desafio(nome, inicio, fim):
    return Desafio(
        nome=nome, exercicio="livre", tipo_metrica="treinos", valor_objetivo=3,
        data_inicio=inicio, data_fim=fim, recompensa_xp=10,
    ).salvar()


class TestDesafioUsuarioRepository(BaseTeste):

    def test_listar_do_usuario_traz_so_as_inscricoes_dele(self):
        with self.app.app_context():
            ana = Usuario(nome="Ana Desafio", email="desafio.ana@repo.teste", senha="hash", idade=30).salvar()
            bia = Usuario(nome="Bia Desafio", email="desafio.bia@repo.teste", senha="hash", idade=30).salvar()
            desafio = criar_desafio("Repo Inscricao", HOJE, HOJE + timedelta(days=3))
            DesafioUsuario(id_desafio=desafio.id_desafio, id_usuario=ana.id_usuario, status="inscrito").salvar()
            DesafioUsuario(id_desafio=desafio.id_desafio, id_usuario=bia.id_usuario, status="inscrito").salvar()
            linhas = DesafioUsuarioRepository.listar_do_usuario(ana.id_usuario)
        self.assertEqual([l["id_usuario"] for l in linhas], [ana.id_usuario])
        self.assertEqual(linhas[0]["status"], "inscrito")
