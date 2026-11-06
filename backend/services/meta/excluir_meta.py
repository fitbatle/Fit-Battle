from services.meta.apoio import exigir_dono_meta


class ExcluirMetaService:

    @staticmethod
    def executar(id_meta, id_usuario):
        meta = exigir_dono_meta(id_meta, id_usuario)
        meta.deletar()
