from flask import jsonify

from services import (
    ErroValidacao,
    ListarMedalhasService,
)

from controllers.apoio import id_logado


class MedalhaController:

    @staticmethod
    def listar(id_usuario):
        try:
            return jsonify(ListarMedalhasService.executar(id_usuario, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
