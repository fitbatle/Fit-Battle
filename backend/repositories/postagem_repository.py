from models.postagem import Postagem
from repositories.apoio import consultar, filtro_maior_de_idade, linhas_de


class PostagemRepository:

    @staticmethod
    def listar_publicas(limite, id_solicitante=None):
        clausula, parametros = filtro_maior_de_idade(id_solicitante)
        parametros["limite"] = limite
        linhas = consultar(
            "SELECT p.* FROM postagem p "
            "JOIN usuario u ON u.id_usuario = p.id_usuario "
            "WHERE u.perfil_publico = 1 AND " + clausula + " "
            "ORDER BY p.data_registro DESC, p.id_postagem ASC LIMIT :limite",
            parametros,
        )
        return linhas_de(linhas, Postagem)

    @staticmethod
    def listar_do_usuario(id_usuario):
        linhas = consultar(
            "SELECT * FROM postagem WHERE id_usuario = :id_usuario",
            {"id_usuario": id_usuario},
        )
        return linhas_de(linhas, Postagem)
