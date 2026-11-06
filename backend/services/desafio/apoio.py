from datetime import datetime, timedelta

from models.desafio import Desafio
from models.desafio_usuario import DesafioUsuario
from models.usuario import Usuario
from repositories.repository import AtividadeRepository
from services.comum import VALOR_OBJETIVO_MAXIMO, ErroValidacao, numero_decimal, texto_do_cliente
from services.notificacao.apoio import gerar_notificacao
from services.usuario.apoio import buscar_usuario
from utils import agora, iso_utc

TIPOS_METRICA = {"treinos", "carga_maxima"}
NOME_MAX = 120
DESCRICAO_MAX = 500
RECOMPENSA_XP_MAXIMA = 100000


def buscar_desafio(id_desafio):
    desafio = Desafio.buscar_por_id(id_desafio)
    if not desafio:
        raise ErroValidacao("Desafio não encontrado.", status=404)
    return desafio


def _titulo_filtro(desafio):
    exercicio = (desafio.exercicio or "livre").strip().lower()
    return None if exercicio == "livre" else exercicio


def valor_atual_desafio(desafio, id_usuario):
    inicio = datetime.combine(desafio.data_inicio, datetime.min.time())
    fim = datetime.combine(desafio.data_fim, datetime.min.time()) + timedelta(days=1)
    titulo = _titulo_filtro(desafio)

    if desafio.tipo_metrica == "carga_maxima":
        return AtividadeRepository.maior_carga_no_periodo(id_usuario, inicio, fim, titulo)["maior_carga"] or 0.0
    return float(AtividadeRepository.contar_no_periodo(id_usuario, inicio, fim, titulo)["total"])


def avaliar_conclusao(desafio, inscricao):
    if inscricao.status != "inscrito":
        return
    atual = valor_atual_desafio(desafio, inscricao.id_usuario)
    objetivo = float(desafio.valor_objetivo)
    if objetivo <= 0 or atual < objetivo:
        return

    with Usuario.transacao():
        inscricao.status = "concluido"
        inscricao.concluido_em = agora()
        inscricao.salvar()

        if desafio.recompensa_xp:
            from services.atividade.apoio import nivel_por_xp

            usuario = buscar_usuario(inscricao.id_usuario)
            usuario.xp += desafio.recompensa_xp
            usuario.nivel = nivel_por_xp(usuario.xp)
            usuario.salvar()

        gerar_notificacao(
            inscricao.id_usuario,
            "desafio_concluido",
            f"Você concluiu o desafio \"{desafio.nome}\"!",
            tipo_alvo="desafio",
            id_alvo=desafio.id_desafio,
        )


def desafio_com_progresso(desafio, id_usuario):
    inscricao = DesafioUsuario.buscar_por_id((desafio.id_desafio, id_usuario))
    if inscricao:
        avaliar_conclusao(desafio, inscricao)

    atual = valor_atual_desafio(desafio, id_usuario)
    objetivo = float(desafio.valor_objetivo)
    percentual = max(0, min(100, round((atual / objetivo) * 100))) if objetivo > 0 else 0

    return {
        "id": desafio.id_desafio,
        "nome": desafio.nome,
        "descricao": desafio.descricao,
        "exercicio": desafio.exercicio,
        "tipo_metrica": desafio.tipo_metrica,
        "valor_objetivo": objetivo,
        "data_inicio": desafio.data_inicio.isoformat(),
        "data_fim": desafio.data_fim.isoformat(),
        "recompensa_xp": desafio.recompensa_xp,
        "minha_inscricao": {
            "status": inscricao.status if inscricao else None,
            "valor_atual": atual,
            "percentual": percentual,
            "concluido_em": iso_utc(inscricao.concluido_em) if inscricao and inscricao.concluido_em else None,
        },
    }


def dict_admin_desafio(desafio):
    return {
        "id": desafio.id_desafio,
        "nome": desafio.nome,
        "descricao": desafio.descricao,
        "exercicio": desafio.exercicio,
        "tipo_metrica": desafio.tipo_metrica,
        "valor_objetivo": float(desafio.valor_objetivo),
        "data_inicio": desafio.data_inicio.isoformat(),
        "data_fim": desafio.data_fim.isoformat(),
        "recompensa_xp": desafio.recompensa_xp,
    }


def validar_nome_desafio(nome):
    nome = texto_do_cliente(nome, "nome")
    if not nome:
        raise ErroValidacao("Informe o nome do desafio.")
    if len(nome) > NOME_MAX:
        raise ErroValidacao(f"O nome pode ter no máximo {NOME_MAX} caracteres.")
    return nome


def validar_tipo_metrica_desafio(tipo_metrica):
    tipo_metrica = texto_do_cliente(tipo_metrica, "tipo de métrica")
    if tipo_metrica not in TIPOS_METRICA:
        raise ErroValidacao("Tipo de métrica inválido. Use: treinos ou carga_maxima.")
    return tipo_metrica


def normalizar_exercicio_desafio(exercicio):
    exercicio = texto_do_cliente(exercicio, "exercício")
    return exercicio if exercicio else "livre"


def validar_numero_desafio(valor, nome):
    numero = numero_decimal(valor, nome, VALOR_OBJETIVO_MAXIMO)
    if numero <= 0:
        raise ErroValidacao(f"O {nome} deve ser maior que zero.")
    return round(numero, 2)


def validar_inteiro_desafio(valor, nome):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ErroValidacao(f"Informe um {nome} válido.")
    if numero < 0:
        raise ErroValidacao(f"O {nome} não pode ser negativo.")
    if numero > RECOMPENSA_XP_MAXIMA:
        raise ErroValidacao(f"O {nome} não pode passar de {RECOMPENSA_XP_MAXIMA}.")
    return numero


def validar_data_desafio(valor, nome):
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ErroValidacao(f"Informe uma {nome} válida. Use o formato AAAA-MM-DD.")
