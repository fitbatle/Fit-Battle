from models.atividade import Atividade
from repositories.apoio import (
    consultar,
    consultar_um,
    converter_agregado,
    filtro_maior_de_idade,
    linhas_de,
)


class AtividadeRepository:

    @staticmethod
    def listar_do_usuario(id_usuario):
        linhas = consultar(
            "SELECT * FROM atividade WHERE id_usuario = :id_usuario ORDER BY data_registro DESC, id_atividade DESC",
            {"id_usuario": id_usuario},
        )
        return linhas_de(linhas, Atividade)

    @staticmethod
    def listar_publicas(limite, id_solicitante=None):
        clausula, parametros = filtro_maior_de_idade(id_solicitante)
        parametros["limite"] = limite
        linhas = consultar(
            "SELECT a.* FROM atividade a "
            "JOIN usuario u ON u.id_usuario = a.id_usuario "
            "WHERE u.perfil_publico = 1 AND " + clausula + " "
            "ORDER BY a.data_registro DESC, a.id_atividade ASC LIMIT :limite",
            parametros,
        )
        return linhas_de(linhas, Atividade)

    @staticmethod
    def maior_carga(id_usuario, titulo_normalizado):
        linha = consultar_um(
            "SELECT MAX(carga_kg) AS maior_carga FROM atividade "
            "WHERE id_usuario = :id_usuario AND tipo = 'musculacao' AND LOWER(titulo) = :titulo",
            {"id_usuario": id_usuario, "titulo": titulo_normalizado},
        )
        return converter_agregado(linha, floats=("maior_carga",))

    @staticmethod
    def contar_desde(id_usuario, data_inicio):
        linha = consultar_um(
            "SELECT COUNT(*) AS total FROM atividade "
            "WHERE id_usuario = :id_usuario AND data_registro >= :inicio",
            {"id_usuario": id_usuario, "inicio": data_inicio},
        )
        return converter_agregado(linha, inteiros=("total",))

    @staticmethod
    def contar_no_periodo(id_usuario, inicio, fim, titulo_normalizado=None):
        sql = (
            "SELECT COUNT(*) AS total FROM atividade "
            "WHERE id_usuario = :id_usuario AND data_registro >= :inicio AND data_registro < :fim"
        )
        parametros = {"id_usuario": id_usuario, "inicio": inicio, "fim": fim}
        if titulo_normalizado:
            sql += " AND LOWER(titulo) = :titulo"
            parametros["titulo"] = titulo_normalizado
        return converter_agregado(consultar_um(sql, parametros), inteiros=("total",))

    @staticmethod
    def maior_carga_no_periodo(id_usuario, inicio, fim, titulo_normalizado=None):
        sql = (
            "SELECT MAX(carga_kg) AS maior_carga FROM atividade "
            "WHERE id_usuario = :id_usuario AND tipo = 'musculacao'"
            " AND data_registro >= :inicio AND data_registro < :fim"
        )
        parametros = {"id_usuario": id_usuario, "inicio": inicio, "fim": fim}
        if titulo_normalizado:
            sql += " AND LOWER(titulo) = :titulo"
            parametros["titulo"] = titulo_normalizado
        return converter_agregado(consultar_um(sql, parametros), floats=("maior_carga",))

    @staticmethod
    def listar_do_usuario_por_titulo(id_usuario, titulo_normalizado):
        linhas = consultar(
            "SELECT * FROM atividade "
            "WHERE id_usuario = :id_usuario AND tipo = 'musculacao' AND LOWER(titulo) = :titulo "
            "ORDER BY data_registro ASC, id_atividade ASC",
            {"id_usuario": id_usuario, "titulo": titulo_normalizado},
        )
        return linhas_de(linhas, Atividade)

    @staticmethod
    def pontuacao_total_desde(id_usuario, desde_utc):
        linha = consultar_um(
            "SELECT COALESCE(SUM(pontuacao), 0) AS total FROM atividade "
            "WHERE id_usuario = :id_usuario AND data_registro >= :desde",
            {"id_usuario": id_usuario, "desde": desde_utc},
        )
        return converter_agregado(linha, inteiros=("total",))

    @staticmethod
    def pontuacoes_desde(id_usuario, desde_utc):
        linhas = consultar(
            "SELECT data_registro, pontuacao FROM atividade "
            "WHERE id_usuario = :id_usuario AND data_registro >= :desde",
            {"id_usuario": id_usuario, "desde": desde_utc},
        )
        return linhas_de(linhas, Atividade)

    @staticmethod
    def distribuicao_por_tipo(id_usuario):
        linhas = consultar(
            "SELECT tipo, COUNT(id_atividade) AS total FROM atividade "
            "WHERE id_usuario = :id_usuario GROUP BY tipo",
            {"id_usuario": id_usuario},
        )
        return {linha["tipo"]: int(linha["total"]) for linha in linhas}

    @staticmethod
    def datas_registro(id_usuario):
        linhas = consultar(
            "SELECT data_registro FROM atividade WHERE id_usuario = :id_usuario",
            {"id_usuario": id_usuario},
        )
        return linhas_de(linhas, Atividade)

    @staticmethod
    def totais(id_usuario):
        linha = consultar_um(
            "SELECT COUNT(id_atividade) AS treinos, COALESCE(SUM(tempo_min), 0) AS tempo_min "
            "FROM atividade WHERE id_usuario = :id_usuario",
            {"id_usuario": id_usuario},
        )
        return converter_agregado(linha, inteiros=("treinos", "tempo_min"))

    @staticmethod
    def titulos_distintos(id_usuario):
        linhas = consultar(
            "SELECT DISTINCT titulo FROM atividade "
            "WHERE id_usuario = :id_usuario AND tipo = 'musculacao' AND carga_kg IS NOT NULL",
            {"id_usuario": id_usuario},
        )
        titulos = [linha["titulo"] for linha in linhas if linha["titulo"]]
        return [{"titulo": titulo} for titulo in sorted(titulos)]

    @staticmethod
    def contagem_de_cargas_por_titulo(id_usuario):
        linhas = consultar(
            "SELECT titulo, COUNT(*) AS quantidade FROM atividade "
            "WHERE id_usuario = :id_usuario AND tipo = 'musculacao' AND carga_kg IS NOT NULL AND titulo IS NOT NULL "
            "GROUP BY titulo",
            {"id_usuario": id_usuario},
        )
        return [{"titulo": linha["titulo"], "quantidade": int(linha["quantidade"])} for linha in linhas]
