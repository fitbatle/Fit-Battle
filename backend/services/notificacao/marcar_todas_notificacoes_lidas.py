from repositories.repository import NotificacaoRepository


class MarcarTodasNotificacoesLidasService:

    @staticmethod
    def executar(id_usuario):
        NotificacaoRepository.marcar_todas_lidas(id_usuario)
