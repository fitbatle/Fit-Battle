import re

from werkzeug.security import check_password_hash, generate_password_hash

from repositories.repository import UsuarioRepository
from services.comum import ErroValidacao, numero_decimal, senha_do_cliente, texto_do_cliente
from services.usuario.apoio import (
    EMAIL_REGEX,
    IDADE_MINIMA_CADASTRO,
    buscar_usuario,
    e_maior_de_idade,
    validar_data_nascimento,
)
from utils import IDADE_MAIORIDADE, ConflitoDeDados

CAMPOS_EDITAVEIS = (
    "nome", "email", "data_nascimento", "peso", "altura",
    "cidade", "estado", "descricao",
)

CAMPOS_DO_RESPONSAVEL = (
    "responsavel",
    "autorizacao_responsavel",
    "responsavel_nome",
    "responsavel_email",
    "responsavel_autorizado_em",
)


def _confirmar_senha_atual(usuario, senha_atual):
    if not senha_atual:
        raise ErroValidacao("Informe a senha atual para trocar e-mail ou senha.")
    if not check_password_hash(usuario.senha, senha_do_cliente(senha_atual)):
        raise ErroValidacao("A senha atual não confere.", status=403)


def _validar_numero(valor, nome, minimo, maximo):
    numero = numero_decimal(valor, nome, maximo)
    if numero < minimo:
        raise ErroValidacao(f"Valor de {nome} fora do intervalo permitido.")
    return round(numero, 2)


class AtualizarPerfilService:

    @staticmethod
    def executar(id_usuario, dados):
        usuario = buscar_usuario(id_usuario)
        dados = dict(dados or {})

        if dados.get("foto") is not None:
            raise ErroValidacao("A foto é trocada pelo envio de imagem, não pelos dados do perfil.")
        if any(dados.get(campo) is not None for campo in CAMPOS_DO_RESPONSAVEL):
            raise ErroValidacao("Os dados do responsável legal não podem ser alterados pelo perfil.")

        if dados.get("nome") is not None:
            dados["nome"] = texto_do_cliente(dados["nome"], "nome")
            if len(dados["nome"]) < 3:
                raise ErroValidacao("O nome deve ter no mínimo 3 caracteres.")

        email = None
        if dados.get("email") is not None:
            email = texto_do_cliente(dados["email"], "e-mail")
            if not re.match(EMAIL_REGEX, email):
                raise ErroValidacao("Informe um e-mail válido.")

        trocar_email = email is not None and email != usuario.email
        trocar_senha = bool(dados.get("senha"))
        if trocar_email or trocar_senha:
            _confirmar_senha_atual(usuario, dados.get("senha_atual"))

        if email is not None:
            existente = UsuarioRepository.buscar_por_email(email)
            if existente and existente["id_usuario"] != usuario.id_usuario:
                raise ErroValidacao("E-mail já cadastrado.", status=409)
            dados["email"] = email

        for campo, nome in (("cidade", "cidade"), ("estado", "estado"), ("descricao", "descrição")):
            if dados.get(campo) is not None:
                dados[campo] = texto_do_cliente(dados[campo], nome)

        if dados.get("senha"):
            senha = senha_do_cliente(dados["senha"])
            if len(senha) < 8:
                raise ErroValidacao("A senha deve ter no mínimo 8 caracteres.")
            dados["senha"] = generate_password_hash(senha)

        if dados.get("data_nascimento") is not None:
            nascimento, idade = validar_data_nascimento(dados["data_nascimento"])
            if idade < IDADE_MINIMA_CADASTRO:
                raise ErroValidacao(
                    "Não é permitido ter menos de 13 anos na plataforma (art. 14 da LGPD)."
                )
            if (idade >= IDADE_MAIORIDADE) != e_maior_de_idade(usuario):
                raise ErroValidacao(
                    "Não é possível mudar a faixa etária (menor ou maior de 18 anos) pelo perfil."
                )
            dados["data_nascimento"] = nascimento

        for campo in ("peso", "altura"):
            if dados.get(campo) == "":
                dados.pop(campo)
        if dados.get("peso") not in (None, ""):
            dados["peso"] = _validar_numero(dados["peso"], "peso", 20, 400)
        if dados.get("altura") not in (None, ""):
            dados["altura"] = _validar_numero(dados["altura"], "altura", 0.5, 2.7)

        campos = {campo: dados[campo] for campo in CAMPOS_EDITAVEIS if dados.get(campo) is not None}
        if dados.get("senha"):
            campos["senha"] = dados["senha"]
        try:
            return usuario.atualizar(campos)
        except ConflitoDeDados:
            raise ErroValidacao("E-mail já cadastrado.", status=409)
