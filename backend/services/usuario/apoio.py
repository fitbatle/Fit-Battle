import os
import re
from datetime import date, datetime

from models.usuario import Usuario
from services.comum import ErroValidacao, texto_do_cliente
from utils import IDADE_MAIORIDADE, agora, calcular_idade

EMAIL_REGEX = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
IDADE_MINIMA_CADASTRO = 13
IDADE_MAXIMA_PLAUSIVEL = 120


def buscar_usuario(id_usuario):
    usuario = Usuario.buscar_por_id(id_usuario)
    if not usuario:
        raise ErroValidacao("Usuário não encontrado.", status=404)
    return usuario


def maior_de_idade_pelos_campos(data_nascimento, idade_legada):
    idade = calcular_idade(data_nascimento, idade_legada)
    return idade is None or idade >= IDADE_MAIORIDADE


def e_maior_de_idade(usuario):
    return maior_de_idade_pelos_campos(usuario.data_nascimento, usuario.idade)


def usuario_visivel_para(usuario, id_solicitante):
    if usuario.id_usuario == id_solicitante:
        return True
    return bool(usuario.perfil_publico) and e_maior_de_idade(usuario)


def buscar_usuario_visivel(id_usuario, id_solicitante):
    usuario = buscar_usuario(id_usuario)
    if not usuario_visivel_para(usuario, id_solicitante):
        raise ErroValidacao("Usuário não encontrado.", status=404)
    return usuario


def usuario_eh_admin(usuario):
    admins = {
        email.strip().lower()
        for email in os.environ.get("ADMIN_EMAILS", "").split(",")
        if email.strip()
    }
    return usuario.email.lower() in admins


def exigir_admin(id_usuario):
    usuario = buscar_usuario(id_usuario)
    if not usuario_eh_admin(usuario):
        raise ErroValidacao("Apenas a administração pode fazer isso.", status=403)
    return usuario


def validar_data_nascimento(valor):
    if not valor:
        raise ErroValidacao("Informe a data de nascimento.")
    try:
        nascimento = datetime.strptime(valor, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ErroValidacao("Data de nascimento inválida. Use o formato AAAA-MM-DD.")

    hoje = date.today()
    if nascimento > hoje:
        raise ErroValidacao("A data de nascimento não pode ser no futuro.")

    idade = calcular_idade(nascimento, hoje=hoje)
    if idade > IDADE_MAXIMA_PLAUSIVEL:
        raise ErroValidacao("Data de nascimento inválida.")
    return nascimento, idade


def validar_faixa_etaria(idade, dados):
    if idade is None:
        raise ErroValidacao("Informe a idade.")

    if idade < IDADE_MINIMA_CADASTRO:
        raise ErroValidacao(
            "Não é permitido ter menos de 13 anos na plataforma (art. 14 da LGPD)."
        )

    if idade >= IDADE_MAIORIDADE:
        return {}

    responsavel = dados.get("responsavel") or {}
    if not isinstance(responsavel, dict):
        raise ErroValidacao("Os dados do responsável legal devem ser enviados em formato de objeto.")
    nome = texto_do_cliente(responsavel.get("nome"), "nome do responsável")
    email = texto_do_cliente(responsavel.get("email"), "e-mail do responsável")

    if not dados.get("autorizacao_responsavel"):
        raise ErroValidacao(
            "Para menores de 18 anos é necessária a autorização do responsável legal."
        )
    if len(nome) < 3:
        raise ErroValidacao("Informe o nome completo do responsável legal.")
    if not re.match(EMAIL_REGEX, email):
        raise ErroValidacao("Informe um e-mail válido do responsável legal.")

    return {
        "responsavel_nome": nome,
        "responsavel_email": email,
        "responsavel_autorizado_em": agora(),
    }
