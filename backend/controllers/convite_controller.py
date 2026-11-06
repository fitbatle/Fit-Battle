from flask import jsonify

from services import (
    ErroValidacao,
    ListarConvitesRecebidosService,
    ResponderConviteService,
)

from controllers.apoio import corpo_json, id_logado


class ConviteController:

    @staticmethod
    def meus_recebidos():
        return jsonify(ListarConvitesRecebidosService.executar(id_logado()))

    @staticmethod
    def responder(id_convite):
        try:
            dados = corpo_json()
            ResponderConviteService.executar(id_convite, id_logado(), dados.get("aceito"))
            return jsonify({"mensagem": "Convite respondido.", "id": id_convite})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
