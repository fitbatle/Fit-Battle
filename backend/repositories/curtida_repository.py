from models.curtida import Curtida
from repositories.apoio import consultar, consultar_um, converter_agregado, executar_comando, linha_de


class CurtidaRepository:

    @staticmethod
    def buscar(id_usuario, tipo_alvo, id_alvo):
        return linha_de(
            consultar_um(
                "SELECT * FROM curtida "
                "WHERE id_usuario = :id_usuario AND tipo_alvo = :tipo_alvo AND id_alvo = :id_alvo",
                {"id_usuario": id_usuario, "tipo_alvo": tipo_alvo, "id_alvo": id_alvo},
            ),
            Curtida,
        )

    @staticmethod
    def contar(tipo_alvo, id_alvo):
        linha = consultar_um(
            "SELECT COUNT(*) AS total FROM curtida WHERE tipo_alvo = :tipo_alvo AND id_alvo = :id_alvo",
            {"tipo_alvo": tipo_alvo, "id_alvo": id_alvo},
        )
        return converter_agregado(linha, inteiros=("total",))

    @staticmethod
    def contar_em_lote(tipo_alvo, ids_alvo):
        if not ids_alvo:
            return {}
        linhas = consultar(
            "SELECT id_alvo, COUNT(id_curtida) AS total FROM curtida "
            "WHERE tipo_alvo = :tipo_alvo AND id_alvo IN :ids_alvo GROUP BY id_alvo",
            {"tipo_alvo": tipo_alvo, "ids_alvo": list(ids_alvo)},
            listas=("ids_alvo",),
        )
        return {linha["id_alvo"]: int(linha["total"]) for linha in linhas}

    @staticmethod
    def curtidos_pelo_usuario(id_usuario, tipo_alvo, ids_alvo):
        if not ids_alvo:
            return []
        return consultar(
            "SELECT id_alvo FROM curtida "
            "WHERE id_usuario = :id_usuario AND tipo_alvo = :tipo_alvo AND id_alvo IN :ids_alvo",
            {"id_usuario": id_usuario, "tipo_alvo": tipo_alvo, "ids_alvo": list(ids_alvo)},
            listas=("ids_alvo",),
        )

    @staticmethod
    def excluir_do_alvo(tipo_alvo, id_alvo):
        executar_comando(
            "DELETE FROM curtida WHERE tipo_alvo = :tipo_alvo AND id_alvo = :id_alvo",
            {"tipo_alvo": tipo_alvo, "id_alvo": id_alvo},
        )

    @staticmethod
    def excluir_do_usuario(id_usuario):
        executar_comando(
            "DELETE FROM curtida WHERE id_usuario = :id_usuario",
            {"id_usuario": id_usuario},
        )
