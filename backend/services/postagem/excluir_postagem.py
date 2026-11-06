from models.postagem import Postagem
from repositories.repository import ComentarioRepository, CurtidaRepository
from services.comum import ErroValidacao


class ExcluirPostagemService:

    @staticmethod
    def executar(id_usuario, id_postagem):
        if id_usuario is None:
            raise ErroValidacao("Informe o usuário.", status=401)
        postagem = Postagem.buscar_por_id(id_postagem)
        if not postagem:
            raise ErroValidacao("Postagem não encontrada.", status=404)
        if postagem.id_usuario != id_usuario:
            raise ErroValidacao("Você só pode excluir suas próprias postagens.", status=403)
        CurtidaRepository.excluir_do_alvo("postagem", id_postagem)
        ComentarioRepository.excluir_do_alvo("postagem", id_postagem)
        postagem.deletar()
