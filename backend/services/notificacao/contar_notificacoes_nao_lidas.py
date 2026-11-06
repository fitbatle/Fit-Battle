from repositories.repository import NotificacaoRepository


class ContarNotificacoesNaoLidasService:

    @staticmethod
    def executar(id_usuario):
        return NotificacaoRepository.contar_nao_lidas(id_usuario)["total"]
