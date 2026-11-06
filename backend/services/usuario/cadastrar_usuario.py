import re

from werkzeug.security import generate_password_hash

from models.usuario import Usuario
from repositories.repository import UsuarioRepository
from services.comum import ErroValidacao, senha_do_cliente, texto_do_cliente
from services.privacidade.apoio import registrar_consentimentos_iniciais
from services.usuario.apoio import EMAIL_REGEX, validar_data_nascimento, validar_faixa_etaria
from utils import ConflitoDeDados


def _validar(dados):
    nome = texto_do_cliente(dados.get("nome"), "nome")
    email = texto_do_cliente(dados.get("email"), "e-mail")
    senha = senha_do_cliente(dados.get("senha") or "")

    if len(nome) < 3:
        raise ErroValidacao("O nome deve ter no mínimo 3 caracteres.")
    if not re.match(EMAIL_REGEX, email):
        raise ErroValidacao("Informe um e-mail válido.")
    if len(senha) < 8:
        raise ErroValidacao("A senha deve ter no mínimo 8 caracteres.")

    return {
        "nome": nome,
        "email": email,
        "senha": senha,
        "cidade": texto_do_cliente(dados.get("cidade"), "cidade") or None,
        "estado": texto_do_cliente(dados.get("estado"), "estado") or None,
        "descricao": texto_do_cliente(dados.get("descricao"), "descrição") or None,
    }


class CadastrarUsuarioService:

    @staticmethod
    def executar(dados):
        dados = dados or {}
        if not dados:
            raise ErroValidacao("Corpo da requisição vazio ou JSON inválido.")
        limpos = _validar(dados)

        if not dados.get("aceite_termos"):
            raise ErroValidacao(
                "É necessário ler e aceitar o Termo de Uso e o Termo de Consentimento."
            )

        nascimento, idade = validar_data_nascimento(dados.get("data_nascimento"))
        limpos["data_nascimento"] = nascimento
        limpos.update(validar_faixa_etaria(idade, dados))

        if UsuarioRepository.buscar_por_email(limpos["email"]):
            raise ErroValidacao("E-mail já cadastrado.", status=409)

        consentimentos = dados.get("consentimentos") or {}
        if not isinstance(consentimentos, dict):
            raise ErroValidacao("Os consentimentos devem ser enviados em formato de objeto.")
        limpos["perfil_publico"] = bool(consentimentos.get("ranking_publico", False))

        limpos["senha"] = generate_password_hash(limpos["senha"])
        with Usuario.transacao():
            try:
                usuario = Usuario(**limpos).salvar()
            except ConflitoDeDados:
                raise ErroValidacao("E-mail já cadastrado.", status=409)
            registrar_consentimentos_iniciais(usuario.id_usuario, consentimentos)
        return usuario
