from models.comentario import Comentario
from models.usuario import Usuario
from repositories.repository import ComentarioRepository
from services.feed.apoio import buscar_alvo


class ListarComentariosService:

    @staticmethod
    def executar(tipo_alvo, id_alvo, id_solicitante):
        buscar_alvo(tipo_alvo, id_alvo, id_solicitante)
        comentarios = ComentarioRepository.listar(tipo_alvo, id_alvo)

        resultado = []
        for c in comentarios:
            dado = Comentario.formatar(c)
            autor = Usuario.buscar_por_id(c["id_usuario"])
            dado["usuario"] = {
                "id": autor.id_usuario if autor else None,
                "nome": autor.nome if autor else "Usuário removido",
                "foto": autor.foto if autor else None,
            }
            resultado.append(dado)
        return resultado
