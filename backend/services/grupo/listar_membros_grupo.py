from repositories.repository import GrupoRepository
from services.grupo.apoio import exigir_membro, montar_handles


class ListarMembrosGrupoService:

    @staticmethod
    def executar(id_grupo, id_usuario):
        exigir_membro(id_grupo, id_usuario)
        pares = GrupoRepository.listar_membros(id_grupo)
        handles = montar_handles(pares)
        return [
            {
                "id": usuario["id_usuario"],
                "nome": usuario["nome"],
                "handle": handles[usuario["id_usuario"]],
                "cidade": usuario["cidade"],
                "estado": usuario["estado"],
                "foto": usuario["foto"],
                "papel": usuario["papel"],
            }
            for usuario in pares
        ]
