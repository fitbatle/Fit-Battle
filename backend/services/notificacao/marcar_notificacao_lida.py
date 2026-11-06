from models.notificacao import Notificacao
from models.notificacao import Notificacao
from services.comum import ErroValidacao


class MarcarNotificacaoLidaService:

    @staticmethod
    def executar(id_notificacao, id_usuario):
        notificacao = Notificacao.buscar_por_id(id_notificacao)
        if not notificacao:
            raise ErroValidacao("Notificação não encontrada.", status=404)
        if notificacao.id_usuario != id_usuario:
            raise ErroValidacao("Você não tem permissão para esta notificação.", status=403)
        notificacao.atualizar({"lida": True})
        return notificacao
