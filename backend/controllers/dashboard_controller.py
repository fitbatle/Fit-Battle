from flask import jsonify, request

from services import (
    ConsultarDashboardService,
    ErroValidacao,
)

from controllers.apoio import id_logado


class DashboardController:

    @staticmethod
    def resumo():
        try:
            dados = ConsultarDashboardService.executar(id_logado(), request.args.get("exercicio"))
            return jsonify(dados)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
