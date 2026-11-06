from services.meta.apoio import carregar_metas, meta_com_progresso


class ListarMetasService:

    @staticmethod
    def executar(id_usuario):
        return [meta_com_progresso(m) for m in carregar_metas(id_usuario)]
