from flask import current_app, jsonify, request

from services import (
    CriarPostagemService,
    ErroValidacao,
    ExcluirPostagemService,
)

from controllers.apoio import id_logado


class PostagemController:

    @staticmethod
    def criar():
        try:
            postagem = CriarPostagemService.executar(
                id_logado(),
                request.form.get("texto"),
                request.files.get("foto"),
                current_app.config["UPLOAD_FOLDER"],
            )
            return jsonify({
                "mensagem": "Postagem publicada!",
                "postagem": postagem.to_dict(),
            }), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def excluir(id_postagem):
        try:
            ExcluirPostagemService.executar(id_logado(), id_postagem)
            return jsonify({"mensagem": "Postagem excluída.", "id": id_postagem})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
