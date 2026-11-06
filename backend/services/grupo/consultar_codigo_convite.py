from services.grupo.apoio import exigir_admin_grupo


class ConsultarCodigoConviteService:

    @staticmethod
    def executar(id_grupo, id_usuario):
        grupo = exigir_admin_grupo(id_grupo, id_usuario)
        return {"codigo": grupo.codigo_convite}
