from datetime import date, datetime, timedelta, timezone

FUSO_LOCAL = timezone(timedelta(hours=-3))
IDADE_MAIORIDADE = 18


class ConflitoDeDados(Exception):
    pass


def agora():
    return datetime.now(timezone.utc)


def iso_utc(valor):
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.isoformat()


def data_local(valor):
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(FUSO_LOCAL).date()


def inicio_utc_do_dia_local(dia):
    meia_noite_local = datetime(dia.year, dia.month, dia.day)
    return meia_noite_local - FUSO_LOCAL.utcoffset(None)


def limite_nascimento_maioridade(hoje):
    try:
        return hoje.replace(year=hoje.year - IDADE_MAIORIDADE)
    except ValueError:
        return date(hoje.year - IDADE_MAIORIDADE, 2, 28)


def calcular_idade(data_nascimento, idade_legada=None, hoje=None):
    if data_nascimento is None:
        return idade_legada
    hoje = hoje or date.today()
    idade = hoje.year - data_nascimento.year
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade
