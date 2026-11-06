from flask import jsonify

from services import (
    ContarNotificacoesNaoLidasService,
    ErroValidacao,
    ListarNotificacoesService,
    MarcarNotificacaoLidaService,
    MarcarTodasNotificacoesLidasService,
)

from controllers.apoio import id_logado


class NotificacaoController:

    @staticmethod
    def listar():
        return jsonify(ListarNotificacoesService.executar(id_logado()))

    @staticmethod
    def contagem():
        return jsonify({"nao_lidas": ContarNotificacoesNaoLidasService.executar(id_logado())})

    @staticmethod
    def marcar_lida(id_notificacao):
        try:
            MarcarNotificacaoLidaService.executar(id_notificacao, id_logado())
            return jsonify({"mensagem": "Notificação marcada como lida.", "id": id_notificacao})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def marcar_todas_lidas():
        MarcarTodasNotificacoesLidasService.executar(id_logado())
        return jsonify({"mensagem": "Todas as notificações foram marcadas como lidas."})
