from werkzeug.security import check_password_hash

from models.usuario import Usuario
from repositories.repository import UsuarioRepository
from services.comum import ErroValidacao, senha_do_cliente, texto_do_cliente
from services.usuario.limitador_login import _LimitadorLogin


class AutenticarUsuarioService:

    @staticmethod
    def executar(email, senha, ip=""):
        email = texto_do_cliente(email, "e-mail")
        senha = senha_do_cliente(senha) if senha is not None else ""
        chave = f"{email.lower()}|{ip}"
        _LimitadorLogin.verificar(chave)

        linha = UsuarioRepository.buscar_por_email(email)
        usuario = Usuario.buscar_por_id(linha["id_usuario"]) if linha else None
        if not usuario or not check_password_hash(usuario.senha, senha):
            _LimitadorLogin.registrar_falha(chave)
            raise ErroValidacao("E-mail ou senha incorretos.", status=401)

        _LimitadorLogin.registrar_sucesso(chave)
        return usuario
