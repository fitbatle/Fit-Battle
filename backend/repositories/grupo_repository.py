from models.grupo import Grupo
from models.usuario import Usuario
from repositories.apoio import consultar, consultar_um, converter_agregado, linha_de, linhas_de


class GrupoRepository:

    @staticmethod
    def buscar_por_codigo(codigo):
        return linha_de(
            consultar_um("SELECT * FROM grupo WHERE codigo_convite = :codigo", {"codigo": codigo}),
            Grupo,
        )

    @staticmethod
    def listar_do_usuario(id_usuario):
        linhas = consultar(
            "SELECT g.*, gm.papel AS papel FROM grupo g "
            "JOIN grupo_membro gm ON gm.id_grupo = g.id_grupo "
            "WHERE gm.id_usuario = :id_usuario",
            {"id_usuario": id_usuario},
        )
        return sorted(linhas_de(linhas, Grupo), key=lambda linha: linha["nome"])

    @staticmethod
    def contar_membros(id_grupo):
        linha = consultar_um(
            "SELECT COUNT(*) AS total FROM grupo_membro WHERE id_grupo = :id_grupo",
            {"id_grupo": id_grupo},
        )
        return converter_agregado(linha, inteiros=("total",))

    @staticmethod
    def papel_do_membro(id_grupo, id_usuario):
        return consultar_um(
            "SELECT papel FROM grupo_membro WHERE id_grupo = :id_grupo AND id_usuario = :id_usuario",
            {"id_grupo": id_grupo, "id_usuario": id_usuario},
        )

    @staticmethod
    def listar_membros(id_grupo):
        linhas = consultar(
            "SELECT u.*, gm.papel AS papel FROM usuario u "
            "JOIN grupo_membro gm ON gm.id_usuario = u.id_usuario "
            "WHERE gm.id_grupo = :id_grupo",
            {"id_grupo": id_grupo},
        )
        return sorted(linhas_de(linhas, Usuario), key=lambda linha: (linha["papel"], linha["nome"]))

    @staticmethod
    def ids_membros(id_grupo):
        return consultar(
            "SELECT id_usuario FROM grupo_membro WHERE id_grupo = :id_grupo",
            {"id_grupo": id_grupo},
        )
