from models.usuario import Usuario
from repositories.apoio import consultar, consultar_um, escapar_like, linha_de, linhas_de


class UsuarioRepository:

    @staticmethod
    def listar(filtro_nome=None):
        if filtro_nome:
            linhas = consultar(
                "SELECT * FROM usuario WHERE nome LIKE :padrao ORDER BY nome",
                {"padrao": "%" + filtro_nome + "%"},
            )
        else:
            linhas = consultar("SELECT * FROM usuario ORDER BY nome")
        return linhas_de(linhas, Usuario)

    @staticmethod
    def buscar_publicos(termo, id_excluido):
        parametros = {"padrao": "%" + escapar_like(termo) + "%"}
        clausula_excluido = ""
        if id_excluido is not None:
            clausula_excluido = " AND u.id_usuario <> :id_excluido"
            parametros["id_excluido"] = id_excluido
        linhas = consultar(
            "SELECT u.* FROM usuario u "
            "JOIN consentimento c ON c.id_usuario = u.id_usuario "
            "AND c.chave = 'busca_perfil' AND c.aceito = 1 "
            "WHERE u.perfil_publico = 1" + clausula_excluido + " "
            "AND (u.nome LIKE :padrao ESCAPE '!' OR u.cidade LIKE :padrao ESCAPE '!') "
            "ORDER BY u.nome",
            parametros,
        )
        return linhas_de(linhas, Usuario)

    @staticmethod
    def buscar_por_email(email):
        return linha_de(
            consultar_um("SELECT * FROM usuario WHERE email = :email", {"email": email}),
            Usuario,
        )
