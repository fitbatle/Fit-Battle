import os

from models.usuario import Usuario
from repositories.repository import (
    AtividadeRepository,
    ComentarioRepository,
    CurtidaRepository,
    PostagemRepository,
)
from services.usuario.apoio import buscar_usuario


class ExcluirContaService:

    @staticmethod
    def executar(id_usuario, pasta_uploads=None):
        usuario = buscar_usuario(id_usuario)

        caminhos_foto = []
        if usuario.foto:
            caminhos_foto.append(usuario.foto)
        for postagem in PostagemRepository.listar_do_usuario(id_usuario):
            if postagem["foto"]:
                caminhos_foto.append(postagem["foto"])

        with Usuario.transacao():
            for atividade in AtividadeRepository.listar_do_usuario(id_usuario):
                CurtidaRepository.excluir_do_alvo("atividade", atividade["id_atividade"])
                ComentarioRepository.excluir_do_alvo("atividade", atividade["id_atividade"])
            for postagem in PostagemRepository.listar_do_usuario(id_usuario):
                CurtidaRepository.excluir_do_alvo("postagem", postagem["id_postagem"])
                ComentarioRepository.excluir_do_alvo("postagem", postagem["id_postagem"])
            CurtidaRepository.excluir_do_usuario(id_usuario)
            ComentarioRepository.excluir_do_usuario(id_usuario)
            usuario.deletar()

        if pasta_uploads:
            for caminho in caminhos_foto:
                try:
                    os.remove(os.path.join(pasta_uploads, os.path.basename(caminho)))
                except OSError:
                    pass
