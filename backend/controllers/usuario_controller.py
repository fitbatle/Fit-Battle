from flask import current_app, g, jsonify, request

from auth import gerar_token

from services import (
    AtualizarFotoPerfilService,
    AtualizarPerfilService,
    AutenticarUsuarioService,
    BuscarPerfisService,
    CadastrarUsuarioService,
    ConsultarEstatisticasService,
    ConsultarPerfilService,
    ConsultarProgressoNivelService,
    ErroValidacao,
    ExcluirContaService,
    VerificarAdminService,
)

from controllers.apoio import corpo_json, id_logado, ip_do_cliente


class UsuarioController:

    @staticmethod
    def cadastrar():
        try:
            usuario = CadastrarUsuarioService.executar(corpo_json())
            return jsonify({
                "mensagem": "Cadastro concluído!",
                "usuario": usuario.to_dict(),
            }), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def login():
        try:
            dados = corpo_json()
            usuario = AutenticarUsuarioService.executar(dados.get("email"), dados.get("senha"), ip_do_cliente())
            return jsonify({
                "mensagem": "Login efetuado!",
                "token": gerar_token(usuario.id_usuario, usuario.senha),
                "usuario": usuario.to_dict(),
            })
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def eu():
        dados = g.usuario_atual.to_dict()
        dados["admin"] = VerificarAdminService.executar(g.usuario_atual)
        dados["progresso_nivel"] = ConsultarProgressoNivelService.executar(g.usuario_atual.xp)
        return jsonify({"usuario": dados})

    @staticmethod
    def busca():
        try:
            usuarios = BuscarPerfisService.executar(
                request.args.get("nome"), id_logado()
            )
            return jsonify(usuarios)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def buscar(id_usuario):
        try:
            usuario = ConsultarPerfilService.executar(id_usuario, id_logado())
            if usuario.id_usuario == id_logado():
                return jsonify(usuario.to_dict())
            return jsonify(usuario.to_publico())
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def atualizar(id_usuario):
        try:
            dados = corpo_json()
            usuario = AtualizarPerfilService.executar(id_usuario, dados)
            resposta = {
                "mensagem": "Usuário atualizado.",
                "usuario": usuario.to_dict(),
            }
            if dados.get("senha"):
                resposta["token"] = gerar_token(usuario.id_usuario, usuario.senha)
            return jsonify(resposta)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def excluir(id_usuario):
        try:
            ExcluirContaService.executar(id_usuario, current_app.config["UPLOAD_FOLDER"])
            return jsonify({"mensagem": "Usuário excluído.", "id": id_usuario})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def upload_foto(id_usuario):
        try:
            usuario = AtualizarFotoPerfilService.executar(
                id_usuario,
                request.files.get("foto"),
                current_app.config["UPLOAD_FOLDER"],
            )
            return jsonify({"mensagem": "Foto atualizada.", "usuario": usuario.to_dict()})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def estatisticas():
        return jsonify(ConsultarEstatisticasService.executar())
