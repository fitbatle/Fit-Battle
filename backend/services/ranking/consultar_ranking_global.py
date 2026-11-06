from repositories.repository import RankingRepository
from services.ranking.apoio import LIMITE_PADRAO, com_nivel, normalizar_limite_ranking


class ConsultarRankingGlobalService:

    @staticmethod
    def executar(limite=LIMITE_PADRAO):
        return com_nivel(RankingRepository.global_(normalizar_limite_ranking(limite)))
