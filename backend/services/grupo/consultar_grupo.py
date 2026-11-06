from repositories.repository import GrupoRepository
from services.grupo.apoio import exigir_membro


class ConsultarGrupoService:

    @staticmethod
    def executar(id_grupo, id_usuario):
        grupo, papel = exigir_membro(id_grupo, id_usuario)
        dado = grupo.to_dict()
        dado["meu_papel"] = papel
        dado["membros"] = GrupoRepository.contar_membros(id_grupo)["total"]
        return dado
