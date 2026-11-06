from flask import jsonify

from services import (
    AtualizarMetaService,
    ConsultarMetaService,
    CriarMetaService,
    ErroValidacao,
    ExcluirMetaService,
    ListarMetasService,
)

from controllers.apoio import corpo_json, id_logado


class MetaController:

    @staticmethod
    def criar():
        try:
            meta = CriarMetaService.executar(id_logado(), corpo_json())
            return jsonify({"mensagem": "Meta criada!", "meta": meta}), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def listar():
        return jsonify(ListarMetasService.executar(id_logado()))

    @staticmethod
    def detalhe(id_meta):
        try:
            return jsonify(ConsultarMetaService.executar(id_meta, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def atualizar(id_meta):
        try:
            meta = AtualizarMetaService.executar(id_meta, id_logado(), corpo_json())
            return jsonify({"mensagem": "Meta atualizada.", "meta": meta})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def excluir(id_meta):
        try:
            ExcluirMetaService.executar(id_meta, id_logado())
            return jsonify({"mensagem": "Meta excluída.", "id": id_meta})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
