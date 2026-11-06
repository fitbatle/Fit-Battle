from models.desafio import Desafio
from models.desafio_usuario import DesafioUsuario
from repositories.repository import DesafioUsuarioRepository
from services.desafio.apoio import avaliar_conclusao


class AvaliarDesafiosDoUsuarioService:

    @staticmethod
    def executar(id_usuario):
        for linha in DesafioUsuarioRepository.listar_do_usuario(id_usuario):
            if linha["status"] != "inscrito":
                continue
            inscricao = DesafioUsuario.buscar_por_id((linha["id_desafio"], linha["id_usuario"]))
            desafio = Desafio.buscar_por_id(linha["id_desafio"])
            if desafio:
                avaliar_conclusao(desafio, inscricao)
