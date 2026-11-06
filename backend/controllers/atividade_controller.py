from flask import jsonify

from services import (
    ConsultarAtividadeService,
    ConsultarHistoricoTreinosService,
    ErroValidacao,
    ExcluirAtividadeService,
    PreverTreinoService,
    RegistrarTreinoService,
)

from controllers.apoio import corpo_json, id_logado


class AtividadeController:

    @staticmethod
    def registrar(id_usuario):
        try:
            atividade, usuario, recorde = RegistrarTreinoService.executar(
                id_usuario, corpo_json()
            )
            return jsonify({
                "mensagem": "Treino registrado!",
                "pontuacao_ganha": atividade.pontuacao,
                "recorde_pessoal": recorde,
                "atividade": atividade.to_dict(),
                "usuario": usuario.to_dict(),
            }), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def previa(id_usuario):
        try:
            return jsonify(PreverTreinoService.executar(id_usuario, corpo_json())), 200
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def historico(id_usuario):
        try:
            atividades = ConsultarHistoricoTreinosService.executar(id_usuario)
            return jsonify(atividades)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def buscar(id_atividade):
        try:
            return jsonify(ConsultarAtividadeService.executar(id_atividade, id_logado()).to_dict())
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def excluir(id_atividade):
        try:
            ExcluirAtividadeService.executar(id_logado(), id_atividade)
            return jsonify({"mensagem": "Atividade excluída.", "id": id_atividade})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
