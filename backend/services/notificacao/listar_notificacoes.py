from models.notificacao import Notificacao
from repositories.repository import NotificacaoRepository


class ListarNotificacoesService:

    @staticmethod
    def executar(id_usuario):
        return [Notificacao.formatar(n) for n in NotificacaoRepository.listar_do_usuario(id_usuario)]
