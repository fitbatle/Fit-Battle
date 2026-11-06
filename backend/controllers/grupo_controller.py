from flask import jsonify, request

from services import (
    BuscarUsuariosParaConvidarService,
    ConsultarCodigoConviteService,
    ConsultarGrupoService,
    ConsultarRankingGrupoService,
    ConvidarParaGrupoService,
    CriarGrupoService,
    EntrarGrupoPorCodigoService,
    ErroValidacao,
    ListarMembrosGrupoService,
    ListarMeusGruposService,
    RegenerarCodigoConviteService,
)

from controllers.apoio import corpo_json, id_logado


class GrupoController:

    @staticmethod
    def criar():
        try:
            grupo = CriarGrupoService.executar(id_logado(), corpo_json())
            return jsonify({"mensagem": "Grupo criado!", "grupo": grupo.to_dict()}), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def listar_meus():
        return jsonify(ListarMeusGruposService.executar(id_logado()))

    @staticmethod
    def detalhe(id_grupo):
        try:
            return jsonify(ConsultarGrupoService.executar(id_grupo, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def membros(id_grupo):
        try:
            return jsonify(ListarMembrosGrupoService.executar(id_grupo, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def ranking(id_grupo):
        try:
            return jsonify(ConsultarRankingGrupoService.executar(id_grupo, id_logado(), request.args.get("limite", 20)))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def convite_info(id_grupo):
        try:
            return jsonify(ConsultarCodigoConviteService.executar(id_grupo, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def regenerar_convite(id_grupo):
        try:
            return jsonify(RegenerarCodigoConviteService.executar(id_grupo, id_logado()))
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def entrar():
        try:
            dados = corpo_json()
            grupo = EntrarGrupoPorCodigoService.executar(id_logado(), dados.get("codigo"))
            return jsonify({"mensagem": "Você entrou no grupo!", "grupo": grupo.to_dict()})
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def buscar_para_convidar(id_grupo):
        try:
            resultado = BuscarUsuariosParaConvidarService.executar(
                id_grupo, id_logado(), request.args.get("nome")
            )
            return jsonify(resultado)
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status

    @staticmethod
    def convidar(id_grupo):
        try:
            dados = corpo_json()
            convite = ConvidarParaGrupoService.executar(id_grupo, id_logado(), dados.get("id_usuario"))
            return jsonify({"mensagem": "Convite enviado!", "id": convite.id_convite}), 201
        except ErroValidacao as erro:
            return jsonify({"erro": erro.mensagem}), erro.status
