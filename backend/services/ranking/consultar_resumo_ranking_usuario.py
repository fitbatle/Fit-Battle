from repositories.repository import RankingRepository
from services.usuario.apoio import buscar_usuario_visivel
from utils import calcular_idade

IDADE_MINIMA_RANKING_PUBLICO = 18
RESTRICAO_MENOR_DE_IDADE = "menor_de_idade"


class ConsultarResumoRankingUsuarioService:

    @staticmethod
    def executar(id_usuario, id_solicitante):
        usuario = buscar_usuario_visivel(id_usuario, id_solicitante)
        idade = calcular_idade(usuario.data_nascimento, usuario.idade)
        menor = idade is not None and idade < IDADE_MINIMA_RANKING_PUBLICO
        return {
            "global": RankingRepository.minha_posicao_global(id_usuario),
            "regional": RankingRepository.minha_posicao_regional(id_usuario),
            "restricao": RESTRICAO_MENOR_DE_IDADE if menor else None,
        }
