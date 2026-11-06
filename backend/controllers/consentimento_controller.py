from flask import jsonify

from services import (
    AtualizarConsentimentoService,
    ErroValidacao,
    ListarConsentimentosService,
)

from controllers.apoio import corpo_json


class ConsentimentoController:

    @staticmethod
    def listar(id_usuario):
        try:
            registros = ListarConsentimentosService.executar(id_usuario)
            return jsonify(registros)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def atualizar(id_usuario, chave):
        try:
            dados = corpo_json()
            registro = AtualizarConsentimentoService.executar(id_usuario, chave, dados.get("aceito"))
            return jsonify({
                "mensagem": "Consentimento atualizado.",
                "consentimento": registro.to_dict(),
            })
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
