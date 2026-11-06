from models.meta import Meta
from datetime import date, datetime

from repositories.repository import AtividadeRepository, MetaRepository
from services.comum import VALOR_OBJETIVO_MAXIMO, ErroValidacao, numero_decimal
from services.notificacao.apoio import gerar_notificacao
from utils import agora


def carregar_metas(id_usuario):
    return [Meta.buscar_por_id(linha["id_meta"]) for linha in MetaRepository.listar_do_usuario(id_usuario)]


def buscar_meta(id_meta):
    meta = Meta.buscar_por_id(id_meta)
    if not meta:
        raise ErroValidacao("Meta não encontrada.", status=404)
    return meta


def exigir_dono_meta(id_meta, id_usuario):
    meta = buscar_meta(id_meta)
    if meta.id_usuario != id_usuario:
        raise ErroValidacao("Você não tem permissão para acessar esta meta.", status=403)
    return meta


def valor_atual_meta(meta):
    if meta.tipo_metrica == "carga_maxima":
        maior = AtividadeRepository.maior_carga(meta.id_usuario, (meta.exercicio or "").strip().lower())["maior_carga"]
        if maior is None:
            return float(meta.valor_partida) if meta.valor_partida is not None else 0.0
        return maior
    inicio = datetime.combine(meta.data_inicio, datetime.min.time())
    return float(AtividadeRepository.contar_desde(meta.id_usuario, inicio)["total"])


def meta_com_progresso(meta):
    if meta.valor_objetivo is None:
        return {
            "id": meta.id_meta,
            "titulo": meta.descricao,
            "tipo": meta.tipo,
            "tipo_metrica": None,
            "exercicio": None,
            "valor_objetivo": None,
            "valor_partida": None,
            "valor_atual": None,
            "faltam": None,
            "percentual": None,
            "status": meta.status,
            "data_inicio": meta.data_inicio.isoformat(),
            "data_final": meta.data_final.isoformat() if meta.data_final else None,
            "dias_restantes": (meta.data_final - date.today()).days if meta.data_final else None,
            "concluida_em": meta.concluida_em.isoformat() if meta.concluida_em else None,
        }

    atual = valor_atual_meta(meta)
    objetivo = float(meta.valor_objetivo)
    partida = float(meta.valor_partida) if meta.valor_partida is not None else 0.0

    if meta.status == "em_andamento" and objetivo > 0 and atual >= objetivo:
        meta.status = "concluida"
        meta.concluida_em = agora()
        meta.salvar()
        gerar_notificacao(
            meta.id_usuario,
            "meta_concluida",
            f"Você concluiu a meta \"{meta.descricao}\"!",
            tipo_alvo="meta",
            id_alvo=meta.id_meta,
        )

    percentual = 0
    if objetivo > 0:
        percentual = max(0, min(100, round((atual / objetivo) * 100)))

    dias_restantes = None
    if meta.data_final:
        dias_restantes = (meta.data_final - date.today()).days

    return {
        "id": meta.id_meta,
        "titulo": meta.descricao,
        "tipo": meta.tipo,
        "tipo_metrica": meta.tipo_metrica,
        "exercicio": meta.exercicio,
        "valor_objetivo": objetivo,
        "valor_partida": partida,
        "valor_atual": atual,
        "faltam": max(0, round(objetivo - atual, 2)),
        "percentual": percentual,
        "status": meta.status,
        "data_inicio": meta.data_inicio.isoformat(),
        "data_final": meta.data_final.isoformat() if meta.data_final else None,
        "dias_restantes": dias_restantes,
        "concluida_em": meta.concluida_em.isoformat() if meta.concluida_em else None,
    }


def validar_numero_meta(valor, nome):
    numero = numero_decimal(valor, nome, VALOR_OBJETIVO_MAXIMO)
    if numero <= 0:
        raise ErroValidacao(f"O {nome} deve ser maior que zero.")
    return round(numero, 2)


def validar_data_meta(valor):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ErroValidacao("Data inválida. Use o formato AAAA-MM-DD.")
