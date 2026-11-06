import unicodedata

from services.atividade.apoio import nivel_por_xp

LIMITE_PADRAO = 20
LIMITE_MAXIMO = 100


def com_nivel(linhas):
    for linha in linhas:
        linha["nivel"] = nivel_por_xp(linha["pontuacao_total"])
    return linhas


def normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    sem_acentos = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return " ".join(sem_acentos.lower().split())


def atribuir_posicoes(linhas):
    ordenadas = sorted(linhas, key=lambda linha: -linha["pontuacao_total"])
    posicao = 0
    anterior = None
    for indice, linha in enumerate(ordenadas, 1):
        if linha["pontuacao_total"] != anterior:
            posicao = indice
            anterior = linha["pontuacao_total"]
        linha["posicao"] = posicao
    return ordenadas


def normalizar_limite_ranking(valor):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return LIMITE_PADRAO
    return max(1, min(numero, LIMITE_MAXIMO))
