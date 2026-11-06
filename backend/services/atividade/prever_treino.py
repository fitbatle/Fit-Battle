from services.atividade.apoio import (
    calcular_pontuacao,
    eh_recorde_pessoal,
    maior_carga_do_exercicio,
    marcar_recorde,
    validar_teto_xp,
    validar_treino,
)


class PreverTreinoService:

    @staticmethod
    def executar(id_usuario, dados):
        limpos = validar_treino(dados)
        limpos["pontuacao"] = calcular_pontuacao(limpos)
        validar_teto_xp(id_usuario, limpos["pontuacao"])
        maior_carga = maior_carga_do_exercicio(id_usuario, limpos)
        recorde = eh_recorde_pessoal(id_usuario, limpos, maior_carga)
        if recorde:
            marcar_recorde(limpos)
        return {
            "pontuacao_estimada": limpos["pontuacao"],
            "recorde_pessoal": recorde,
            "recorde_atual": maior_carga,
        }
