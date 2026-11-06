from repositories.repository import RankingRepository
from services.grupo.apoio import exigir_membro
from services.ranking.apoio import com_nivel, normalizar_limite_ranking


class ConsultarRankingGrupoService:

    @staticmethod
    def executar(id_grupo, id_usuario, limite=20):
        exigir_membro(id_grupo, id_usuario)
        return com_nivel(RankingRepository.grupo(id_grupo, normalizar_limite_ranking(limite)))
