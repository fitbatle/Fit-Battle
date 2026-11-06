from services.usuario.apoio import buscar_usuario_visivel


class ConsultarPerfilService:

    @staticmethod
    def executar(id_usuario, id_solicitante):
        return buscar_usuario_visivel(id_usuario, id_solicitante)
