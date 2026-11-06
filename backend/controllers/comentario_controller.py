from flask import jsonify

from services import (
    BuscarUsuarioService,
    CriarComentarioService,
    ErroValidacao,
    ExcluirComentarioService,
    ListarComentariosService,
)

from controllers.apoio import corpo_json, id_logado


class ComentarioController:

    @staticmethod
    def listar(tipo_alvo, id_alvo):
        try:
            comentarios = ListarComentariosService.executar(tipo_alvo, id_alvo, id_logado())
            return jsonify(comentarios)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def criar(tipo_alvo, id_alvo):
        try:
            dados = corpo_json()
            comentario = CriarComentarioService.executar(
                id_logado(), tipo_alvo, id_alvo, dados.get("texto")
            )
            resultado = comentario.to_dict()
            autor = BuscarUsuarioService.executar(comentario.id_usuario)
            resultado["usuario"] = {
                "id": autor.id_usuario, "nome": autor.nome, "foto": autor.foto,
            }
            return jsonify({"mensagem": "Comentário publicado.", "comentario": resultado}), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def excluir(id_comentario):
        try:
            ExcluirComentarioService.executar(id_logado(), id_comentario)
            return jsonify({"mensagem": "Comentário excluído.", "id": id_comentario})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
