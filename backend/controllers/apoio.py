import os
from flask import g, request

from services import ErroValidacao


def id_logado():
    return g.usuario_atual.id_usuario


def ip_do_cliente():
    if os.getenv("TRUST_PROXY") == "1":
        encaminhado = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if encaminhado:
            return encaminhado
    return request.remote_addr or ""


def corpo_json():
    corpo = request.get_json(silent=True)
    if not isinstance(corpo, dict):
        raise ErroValidacao("Corpo da requisição vazio ou JSON inválido.")
    return corpo
