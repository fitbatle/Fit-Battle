from models.comentario import Comentario
from services.comum import ErroValidacao
from services.feed.apoio import buscar_alvo


class ExcluirComentarioService:

    @staticmethod
    def executar(id_usuario, id_comentario):
        if id_usuario is None:
            raise ErroValidacao("Informe o usuário.", status=401)
        comentario = Comentario.buscar_por_id(id_comentario)
        if not comentario:
            raise ErroValidacao("Comentário não encontrado.", status=404)
        buscar_alvo(comentario.tipo_alvo, comentario.id_alvo, id_usuario)
        if comentario.id_usuario != id_usuario:
            raise ErroValidacao("Você só pode excluir seus próprios comentários.", status=403)
        comentario.deletar()
