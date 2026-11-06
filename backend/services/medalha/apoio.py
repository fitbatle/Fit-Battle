from datetime import timedelta

from repositories.repository import AtividadeRepository
from services.atividade.apoio import FAIXAS_NIVEL
from services.meta.apoio import carregar_metas, valor_atual_meta
from utils import data_local

DIAS_SEMANA_PERFEITA = 7
KM_MARATONA = 42
NOMES_CATEGORIA = {
    "intermediario": "Intermediário",
    "avancado": "Avançado",
    "profissional": "Profissional",
    "elite": "Elite",
}


def metas_com_progresso(metas):
    return [(meta, valor_atual_meta(meta)) for meta in metas]


def calcular_medalhas(usuario, atividades, metas_progresso):
    ordenadas = sorted(atividades, key=lambda atividade: atividade["data_registro"])
    datas = [data_local(atividade["data_registro"]) for atividade in ordenadas]
    dias = sorted(set(datas))

    medalhas = [
        _contagem("primeiro_treino", "Primeiro treino", "Registrar 1 atividade.", datas, 1),
        _contagem("constancia", "Constância", "Registrar 10 atividades.", datas, 10),
        _contagem("veterano", "Veterano", "Registrar 50 atividades.", datas, 50),
        _semana_perfeita(dias),
        _meta_batida(metas_progresso),
        _maratonista(ordenadas),
    ]
    for minimo, chave_nivel in FAIXAS_NIVEL[1:]:
        medalhas.append(_categoria(usuario, chave_nivel, minimo, ordenadas))
    return medalhas


def _medalha(chave, nome, criterio, valor, meta, data):
    conquistada = valor >= meta
    return {
        "chave": chave,
        "nome": nome,
        "criterio": criterio,
        "progresso": {"valor": valor, "meta": meta},
        "conquistada": conquistada,
        "data_conquista": data.isoformat() if conquistada and data else None,
    }


def _contagem(chave, nome, criterio, datas, minimo):
    data = datas[minimo - 1] if len(datas) >= minimo else None
    return _medalha(chave, nome, criterio, len(datas), minimo, data)


def _semana_perfeita(dias):
    melhor = 0
    data = None
    inicio = None
    tamanho = 0
    anterior = None
    for dia in dias:
        if anterior is not None and (dia - anterior).days == 1:
            tamanho += 1
        else:
            inicio = dia
            tamanho = 1
        melhor = max(melhor, tamanho)
        if tamanho == DIAS_SEMANA_PERFEITA and data is None:
            data = inicio + timedelta(days=DIAS_SEMANA_PERFEITA - 1)
        anterior = dia
    return _medalha(
        "semana_perfeita", "Semana perfeita",
        "Treinar 7 dias seguidos.", melhor, DIAS_SEMANA_PERFEITA, data,
    )


def _meta_batida(metas_progresso):
    concluidas = []
    for meta, atual in metas_progresso:
        objetivo = float(meta.valor_objetivo) if meta.valor_objetivo is not None else None
        if meta.status == "concluida" or (objetivo and atual >= objetivo):
            concluidas.append(meta)
    datas = sorted(data_local(meta.concluida_em) for meta in concluidas if meta.concluida_em)
    return _medalha(
        "meta_batida", "Meta batida",
        "Concluir ao menos uma meta.", len(concluidas), 1, datas[0] if datas else None,
    )


def _maratonista(ordenadas):
    total = 0.0
    data = None
    for atividade in ordenadas:
        if atividade["distancia_km"] is None:
            continue
        total += float(atividade["distancia_km"])
        if data is None and total >= KM_MARATONA:
            data = data_local(atividade["data_registro"])
    return _medalha(
        "maratonista", "Maratonista",
        "Acumular 42 km em atividades com distância.", round(total, 2), KM_MARATONA, data,
    )


def _categoria(usuario, chave_nivel, minimo, ordenadas):
    xp = usuario.xp or 0
    total = 0
    data = None
    for atividade in ordenadas:
        total += atividade["pontuacao"]
        if data is None and total >= minimo:
            data = data_local(atividade["data_registro"])
    nome = NOMES_CATEGORIA[chave_nivel]
    return _medalha(
        f"categoria_{chave_nivel}", f"Categoria {nome}",
        f"Chegar à categoria {nome} com {minimo} XP.", xp, minimo, data,
    )


def medalhas_do_usuario(usuario):
    atividades = AtividadeRepository.listar_do_usuario(usuario.id_usuario)
    metas = carregar_metas(usuario.id_usuario)
    return calcular_medalhas(usuario, atividades, metas_com_progresso(metas))


def chaves_conquistadas(usuario):
    return {medalha["chave"] for medalha in medalhas_do_usuario(usuario) if medalha["conquistada"]}
