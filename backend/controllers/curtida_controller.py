from flask import jsonify

from services import (
    AlternarCurtidaService,
    ErroValidacao,
)

from controllers.apoio import id_logado


class CurtidaController:

    @staticmethod
    def alternar(tipo_alvo, id_alvo):
        try:
            resultado = AlternarCurtidaService.executar(id_logado(), tipo_alvo, id_alvo)
            return jsonify(resultado)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
