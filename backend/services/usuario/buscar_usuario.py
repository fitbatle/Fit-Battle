from services.usuario.apoio import buscar_usuario


class BuscarUsuarioService:

    @staticmethod
    def executar(id_usuario):
        return buscar_usuario(id_usuario)
