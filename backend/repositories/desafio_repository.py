from models.desafio import Desafio
from repositories.apoio import consultar, linhas_de


class DesafioRepository:

    @staticmethod
    def listar_ativos(hoje):
        linhas = consultar(
            "SELECT * FROM desafio WHERE data_fim >= :hoje ORDER BY data_inicio ASC, id_desafio ASC",
            {"hoje": hoje},
        )
        return linhas_de(linhas, Desafio)
