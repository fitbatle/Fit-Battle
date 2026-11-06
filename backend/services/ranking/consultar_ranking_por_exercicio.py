from repositories.repository import RankingRepository
from services.comum import ErroValidacao
from services.ranking.apoio import LIMITE_PADRAO, normalizar_limite_ranking


class ConsultarRankingPorExercicioService:

    @staticmethod
    def executar(titulo, cidade=None, limite=LIMITE_PADRAO):
        titulo = (titulo or "").strip()
        if not titulo:
            raise ErroValidacao("Informe o exercício para ver o ranking.")
        cidade = (cidade or "").strip() or None
        return RankingRepository.por_exercicio(titulo, cidade, normalizar_limite_ranking(limite))
