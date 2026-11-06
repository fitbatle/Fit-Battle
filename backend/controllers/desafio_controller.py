from flask import jsonify

from services import (
    AtualizarDesafioService,
    ConsultarDesafioService,
    CriarDesafioService,
    DesistirDesafioService,
    EncerrarDesafioService,
    ErroValidacao,
    ListarDesafiosAtivosService,
    ParticiparDesafioService,
)

from controllers.apoio import corpo_json, id_logado


class DesafioController:

    @staticmethod
    def criar():
        try:
            desafio = CriarDesafioService.executar(id_logado(), corpo_json())
            return jsonify({"mensagem": "Desafio criado!", "desafio": desafio}), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def listar():
        return jsonify(ListarDesafiosAtivosService.executar(id_logado()))

    @staticmethod
    def detalhe(id_desafio):
        try:
            return jsonify(ConsultarDesafioService.executar(id_desafio, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def atualizar(id_desafio):
        try:
            desafio = AtualizarDesafioService.executar(id_logado(), id_desafio, corpo_json())
            return jsonify({"mensagem": "Desafio atualizado.", "desafio": desafio})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def encerrar(id_desafio):
        try:
            desafio = EncerrarDesafioService.executar(id_logado(), id_desafio)
            return jsonify({"mensagem": "Desafio encerrado.", "desafio": desafio})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def participar(id_desafio):
        try:
            desafio = ParticiparDesafioService.executar(id_logado(), id_desafio)
            return jsonify({"mensagem": "Inscrição confirmada!", "desafio": desafio})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def desistir(id_desafio):
        try:
            desafio = DesistirDesafioService.executar(id_logado(), id_desafio)
            return jsonify({"mensagem": "Você desistiu do desafio.", "desafio": desafio})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
