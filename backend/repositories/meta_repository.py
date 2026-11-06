from models.meta import Meta
from repositories.apoio import consultar, linhas_de


class MetaRepository:

    @staticmethod
    def listar_do_usuario(id_usuario):
        linhas = consultar(
            "SELECT * FROM meta WHERE id_usuario = :id_usuario ORDER BY data_inicio DESC, id_meta DESC",
            {"id_usuario": id_usuario},
        )
        return linhas_de(linhas, Meta)
