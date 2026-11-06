from repositories.apoio import consultar, consultar_um, linha_ranking


class RankingRepository:

    @staticmethod
    def global_(limite):
        linhas = consultar(
            "SELECT id_usuario, nome, cidade, estado, pontuacao_total, posicao "
            "FROM vw_ranking_global ORDER BY posicao LIMIT :lim",
            {"lim": limite},
        )
        return [linha_ranking(linha) for linha in linhas]

    @staticmethod
    def regional_todos():
        linhas = consultar(
            "SELECT id_usuario, nome, cidade, estado, pontuacao_total, posicao "
            "FROM vw_ranking_regional"
        )
        return [linha_ranking(linha) for linha in linhas]

    @staticmethod
    def por_exercicio(titulo, cidade, limite):
        sql = (
            "SELECT id_usuario, nome, cidade, estado, titulo, carga_maxima, posicao "
            "FROM vw_ranking_exercicio "
            "WHERE titulo_normalizado = :titulo "
        )
        parametros = {"titulo": titulo.strip().lower(), "lim": limite}
        if cidade:
            sql += "AND cidade = :cidade "
            parametros["cidade"] = cidade
        sql += "ORDER BY posicao LIMIT :lim"
        linhas = consultar(sql, parametros)
        return [linha_ranking(linha) for linha in linhas]

    @staticmethod
    def minha_posicao_global(id_usuario):
        return linha_ranking(consultar_um(
            "SELECT posicao, pontuacao_total FROM vw_ranking_global WHERE id_usuario = :id",
            {"id": id_usuario},
        ))

    @staticmethod
    def minha_posicao_regional(id_usuario):
        return linha_ranking(consultar_um(
            "SELECT posicao, pontuacao_total, cidade FROM vw_ranking_regional WHERE id_usuario = :id",
            {"id": id_usuario},
        ))

    @staticmethod
    def grupo(id_grupo, limite):
        linhas = consultar(
            "SELECT id_usuario, nome, pontuacao_total, posicao FROM vw_ranking_grupo "
            "WHERE id_grupo = :id_grupo ORDER BY posicao LIMIT :lim",
            {"id_grupo": id_grupo, "lim": limite},
        )
        return [linha_ranking(linha) for linha in linhas]
