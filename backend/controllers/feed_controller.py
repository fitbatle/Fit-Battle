from flask import jsonify, request

from services import (
    ListarFeedService,
)

from controllers.apoio import id_logado


class FeedController:

    @staticmethod
    def listar():
        limite = request.args.get("limite", 30)
        return jsonify(ListarFeedService.executar(id_logado(), limite))
