from datetime import date, datetime, timezone

from sqlalchemy import bindparam, text

from database import db
from models.base import efetivar, sincronizar
from utils import IDADE_MAIORIDADE, limite_nascimento_maioridade


CLAUSULA_MAIOR_DE_IDADE = (
    "(u.data_nascimento <= :limite_maioridade"
    " OR (u.data_nascimento IS NULL AND (u.idade IS NULL OR u.idade >= :idade_maioridade)))"
)

ESCAPE_LIKE = "!"

def filtro_maior_de_idade(id_solicitante=None):
    limite = limite_nascimento_maioridade(date.today())
    parametros = {"limite_maioridade": limite, "idade_maioridade": IDADE_MAIORIDADE}
    if id_solicitante is None:
        return CLAUSULA_MAIOR_DE_IDADE, parametros
    parametros["id_solicitante"] = id_solicitante
    return "(u.id_usuario = :id_solicitante OR " + CLAUSULA_MAIOR_DE_IDADE + ")", parametros


def escapar_like(termo):
    return termo.replace(ESCAPE_LIKE, ESCAPE_LIKE * 2).replace("%", ESCAPE_LIKE + "%").replace("_", ESCAPE_LIKE + "_")


def _comando(sql, listas):
    comando = text(sql)
    if listas:
        comando = comando.bindparams(*(bindparam(nome, expanding=True) for nome in listas))
    return comando


def consultar(sql, parametros=None, listas=()):
    sincronizar()
    linhas = db.session.execute(_comando(sql, listas), parametros or {}).mappings().all()
    return [dict(linha) for linha in linhas]


def consultar_um(sql, parametros=None):
    sincronizar()
    linha = db.session.execute(text(sql), parametros or {}).mappings().first()
    return dict(linha) if linha is not None else None


def executar_comando(sql, parametros=None, listas=()):
    sincronizar()
    db.session.execute(_comando(sql, listas), parametros or {})
    efetivar()


def _tipos_das_colunas(modelos):
    tipos = {}
    for modelo in modelos:
        for coluna in modelo.__table__.columns:
            tipos.setdefault(coluna.name, coluna.type)
    return tipos


def _normalizar_valor(tipo, valor):
    if valor is None:
        return None
    if isinstance(tipo, db.Boolean):
        return bool(valor)
    if isinstance(tipo, db.DateTime):
        if isinstance(valor, str):
            valor = datetime.fromisoformat(valor)
        if valor.tzinfo is not None:
            valor = valor.astimezone(timezone.utc).replace(tzinfo=None)
        return valor
    if isinstance(tipo, db.Date) and isinstance(valor, str):
        return date.fromisoformat(valor)
    if isinstance(tipo, db.Numeric):
        return float(valor)
    return valor


def linha_de(linha, *modelos):
    if linha is None:
        return None
    tipos = _tipos_das_colunas(modelos)
    return {
        chave: _normalizar_valor(tipos[chave], valor) if chave in tipos else valor
        for chave, valor in linha.items()
    }


def linhas_de(linhas, *modelos):
    tipos = _tipos_das_colunas(modelos)
    return [
        {
            chave: _normalizar_valor(tipos[chave], valor) if chave in tipos else valor
            for chave, valor in linha.items()
        }
        for linha in linhas
    ]


def converter_agregado(linha, floats=(), inteiros=()):
    d = dict(linha)
    for chave in floats:
        if d.get(chave) is not None:
            d[chave] = float(d[chave])
    for chave in inteiros:
        d[chave] = int(d[chave] or 0)
    return d


def linha_ranking(linha):
    if linha is None:
        return None
    d = dict(linha)
    if "pontuacao_total" in d:
        d["pontuacao_total"] = int(d["pontuacao_total"] or 0)
    if "carga_maxima" in d and d["carga_maxima"] is not None:
        d["carga_maxima"] = float(d["carga_maxima"])
    if "posicao" in d and d["posicao"] is not None:
        d["posicao"] = int(d["posicao"])
    return d
