from flask import jsonify, request

from services import (
    ConsultarRankingGlobalService,
    ConsultarRankingPorExercicioService,
    ConsultarRankingRegionalService,
    ConsultarResumoRankingUsuarioService,
    ErroValidacao,
)

from controllers.apoio import id_logado


class RankingController:

    @staticmethod
    def ranking_global():
        return jsonify(ConsultarRankingGlobalService.executar(request.args.get("limite", 20)))

    @staticmethod
    def ranking_regional():
        try:
            dados = ConsultarRankingRegionalService.executar(
                request.args.get("cidade"), request.args.get("limite", 20), request.args.get("estado")
            )
            return jsonify(dados)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def ranking_por_exercicio():
        try:
            dados = ConsultarRankingPorExercicioService.executar(
                request.args.get("titulo"),
                request.args.get("cidade"),
                request.args.get("limite", 20),
            )
            return jsonify(dados)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def resumo_usuario(id_usuario):
        try:
            return jsonify(ConsultarResumoRankingUsuarioService.executar(id_usuario, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
