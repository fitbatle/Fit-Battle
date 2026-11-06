from models.comentario import Comentario
from repositories.apoio import consultar, executar_comando, linhas_de


class ComentarioRepository:

    @staticmethod
    def listar(tipo_alvo, id_alvo):
        linhas = consultar(
            "SELECT * FROM comentario "
            "WHERE tipo_alvo = :tipo_alvo AND id_alvo = :id_alvo ORDER BY data_registro ASC, id_comentario ASC",
            {"tipo_alvo": tipo_alvo, "id_alvo": id_alvo},
        )
        return linhas_de(linhas, Comentario)

    @staticmethod
    def contar_em_lote(tipo_alvo, ids_alvo):
        if not ids_alvo:
            return {}
        linhas = consultar(
            "SELECT id_alvo, COUNT(id_comentario) AS total FROM comentario "
            "WHERE tipo_alvo = :tipo_alvo AND id_alvo IN :ids_alvo GROUP BY id_alvo",
            {"tipo_alvo": tipo_alvo, "ids_alvo": list(ids_alvo)},
            listas=("ids_alvo",),
        )
        return {linha["id_alvo"]: int(linha["total"]) for linha in linhas}

    @staticmethod
    def excluir_do_alvo(tipo_alvo, id_alvo):
        executar_comando(
            "DELETE FROM comentario WHERE tipo_alvo = :tipo_alvo AND id_alvo = :id_alvo",
            {"tipo_alvo": tipo_alvo, "id_alvo": id_alvo},
        )

    @staticmethod
    def excluir_do_usuario(id_usuario):
        executar_comando(
            "DELETE FROM comentario WHERE id_usuario = :id_usuario",
            {"id_usuario": id_usuario},
        )
