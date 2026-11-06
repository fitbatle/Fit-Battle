from models.atividade import Atividade
from repositories.repository import AtividadeRepository
from services.comum import ErroValidacao, numero_decimal, texto_do_cliente
from utils import agora, data_local, inicio_utc_do_dia_local

FAIXAS_NIVEL = [
    (0, "iniciante"),
    (1000, "intermediario"),
    (3000, "avancado"),
    (7000, "profissional"),
    (15000, "elite"),
]

PONTUACAO_MAXIMA_TREINO = 2000
XP_MAXIMO_DIARIO = 3000
TIPOS_VALIDOS = {"musculacao", "cardio", "yoga", "outro"}
PREFIXO_RECORDE = "Novo recorde pessoal! "
DESCRICAO_MAXIMA = 500

LIMITES_CAMPOS = {
    "tempo_min": 600,
    "distancia_km": 500,
    "carga_kg": 500,
    "repeticoes": 1000,
}


def nivel_por_xp(xp):
    nivel = FAIXAS_NIVEL[0][1]
    for xp_minimo, nome in FAIXAS_NIVEL:
        if xp >= xp_minimo:
            nivel = nome
    return nivel


def progresso_de_nivel(xp):
    indice = 0
    for posicao, (xp_minimo, _) in enumerate(FAIXAS_NIVEL):
        if xp >= xp_minimo:
            indice = posicao
    nivel = FAIXAS_NIVEL[indice][1]

    if indice == len(FAIXAS_NIVEL) - 1:
        return {"nivel": nivel, "percentual": 100, "xp_faltante": 0}

    base = FAIXAS_NIVEL[indice][0]
    proximo = FAIXAS_NIVEL[indice + 1][0]
    percentual = int((xp - base) * 100 / (proximo - base) + 0.5)
    return {
        "nivel": nivel,
        "percentual": min(100, max(0, percentual)),
        "xp_faltante": proximo - xp,
    }


def calcular_pontuacao(dados):
    tempo = dados.get("tempo_min") or 0
    distancia = dados.get("distancia_km") or 0
    carga = dados.get("carga_kg") or 0
    reps = dados.get("repeticoes") or 0

    pontos = tempo * 1 + distancia * 10 + (carga * reps) / 100

    bonus_tipo = {"musculacao": 20, "cardio": 15, "yoga": 10, "outro": 5}
    pontos += bonus_tipo.get(dados["tipo"], 5)

    return max(10, round(pontos))


def validar_treino(dados):
    if not dados:
        raise ErroValidacao("Corpo da requisição vazio ou JSON inválido.")

    tipo = texto_do_cliente(dados.get("tipo"), "tipo").lower()
    if tipo not in TIPOS_VALIDOS:
        raise ErroValidacao(
            "Tipo inválido. Use: " + ", ".join(sorted(TIPOS_VALIDOS))
        )

    numericos = {}
    for campo in ("tempo_min", "distancia_km", "carga_kg", "repeticoes"):
        valor = dados.get(campo)
        if valor in (None, ""):
            numericos[campo] = None
            continue
        valor = numero_decimal(valor, campo, LIMITES_CAMPOS[campo])
        if valor < 0:
            raise ErroValidacao(f"O campo '{campo}' não pode ser negativo.")
        numericos[campo] = valor

    if not numericos["tempo_min"] and not numericos["distancia_km"]:
        raise ErroValidacao("Informe ao menos a duração ou a distância do treino.")

    return {
        "tipo": tipo,
        "titulo": texto_do_cliente(dados.get("titulo"), "título") or None,
        "descricao": texto_do_cliente(dados.get("descricao"), "descrição") or None,
        **numericos,
    }


def validar_teto_xp(id_usuario, pontuacao):
    if pontuacao > PONTUACAO_MAXIMA_TREINO:
        raise ErroValidacao(
            f"Este treino vale {pontuacao} XP, acima do máximo de {PONTUACAO_MAXIMA_TREINO} XP por treino. "
            "Confira os valores informados."
        )
    xp_hoje = AtividadeRepository.pontuacao_total_desde(
        id_usuario, inicio_utc_do_dia_local(data_local(agora()))
    )["total"]
    if xp_hoje + pontuacao > XP_MAXIMO_DIARIO:
        raise ErroValidacao(
            f"Limite diário de XP atingido: você já somou {xp_hoje} XP hoje e o máximo é "
            f"{XP_MAXIMO_DIARIO} XP por dia. Tente novamente amanhã."
        )


def maior_carga_do_exercicio(id_usuario, limpos):
    if limpos["tipo"] != "musculacao" or not limpos["titulo"]:
        return None
    return AtividadeRepository.maior_carga(id_usuario, limpos["titulo"].lower())["maior_carga"]


def eh_recorde_pessoal(id_usuario, limpos, maior_carga):
    if limpos["tipo"] != "musculacao" or not limpos["titulo"] or limpos["carga_kg"] is None:
        return False
    return maior_carga is None or limpos["carga_kg"] > maior_carga


def marcar_recorde(limpos):
    descricao = PREFIXO_RECORDE + (limpos["descricao"] or "")
    if len(descricao.strip()) > DESCRICAO_MAXIMA:
        raise ErroValidacao(
            "A descrição é longa demais para registrar um recorde pessoal. "
            "Reduza o texto e tente de novo."
        )
    limpos["descricao"] = descricao.strip()


def buscar_atividade(id_atividade):
    atividade = Atividade.buscar_por_id(id_atividade)
    if not atividade:
        raise ErroValidacao("Atividade não encontrada.", status=404)
    return atividade
