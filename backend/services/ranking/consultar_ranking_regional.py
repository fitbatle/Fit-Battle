from repositories.repository import RankingRepository
from services.comum import ErroValidacao
from services.ranking.apoio import (
    LIMITE_PADRAO,
    atribuir_posicoes,
    com_nivel,
    normalizar_limite_ranking,
    normalizar_texto,
)


class ConsultarRankingRegionalService:

    @staticmethod
    def executar(cidade, limite=LIMITE_PADRAO, estado=None):
        cidade = (cidade or "").strip()
        estado = (estado or "").strip()
        if not cidade and not estado:
            raise ErroValidacao(
                "Informe a cidade para ver o ranking regional."
            )
        linhas = RankingRepository.regional_todos()
        if estado:
            chave = normalizar_texto(estado)
            linhas = [linha for linha in linhas if normalizar_texto(linha["estado"]) == chave]
        else:
            chave = normalizar_texto(cidade)
            linhas = [linha for linha in linhas if normalizar_texto(linha["cidade"]) == chave]
        return com_nivel(atribuir_posicoes(linhas)[: normalizar_limite_ranking(limite)])
