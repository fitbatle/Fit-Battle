from services.usuario.apoio import usuario_eh_admin


class VerificarAdminService:

    @staticmethod
    def executar(usuario):
        return usuario_eh_admin(usuario)
