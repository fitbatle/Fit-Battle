from models.desafio_usuario import DesafioUsuario
from repositories.apoio import consultar, linhas_de


class DesafioUsuarioRepository:

    @staticmethod
    def listar_do_usuario(id_usuario):
        linhas = consultar(
            "SELECT * FROM desafio_usuario WHERE id_usuario = :id_usuario",
            {"id_usuario": id_usuario},
        )
        return linhas_de(linhas, DesafioUsuario)
