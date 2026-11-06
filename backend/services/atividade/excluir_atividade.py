from models.usuario import Usuario
from repositories.repository import ComentarioRepository, CurtidaRepository
from services.atividade.apoio import buscar_atividade, nivel_por_xp
from services.comum import ErroValidacao


class ExcluirAtividadeService:

    @staticmethod
    def executar(id_usuario, id_atividade):
        atividade = buscar_atividade(id_atividade)
        if atividade.id_usuario != id_usuario:
            raise ErroValidacao("Você só pode excluir seus próprios treinos.", status=403)
        with Usuario.transacao():
            usuario = Usuario.buscar_por_id(atividade.id_usuario)
            if usuario:
                usuario.xp = max(0, usuario.xp - atividade.pontuacao)
                usuario.nivel = nivel_por_xp(usuario.xp)
                usuario.salvar()
            CurtidaRepository.excluir_do_alvo("atividade", id_atividade)
            ComentarioRepository.excluir_do_alvo("atividade", id_atividade)
            atividade.deletar()
