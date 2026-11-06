from flask import jsonify

from services import (
    ErroValidacao,
    RegistrarCompartilhamentoService,
)

from controllers.apoio import corpo_json, id_logado


class CompartilhamentoController:

    @staticmethod
    def registrar():
        try:
            registro = RegistrarCompartilhamentoService.executar(id_logado(), corpo_json())
            return jsonify({
                "mensagem": "Compartilhamento registrado.",
                "compartilhamento": registro.to_dict(),
            }), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
