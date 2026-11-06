from repositories.repository import ConviteRepository, GrupoRepository
from services.grupo.apoio import exigir_membro, montar_handles
from services.usuario.buscar_perfis import buscar_adultos


class BuscarUsuariosParaConvidarService:

    @staticmethod
    def executar(id_grupo, id_usuario, termo):
        exigir_membro(id_grupo, id_usuario)
        encontrados = buscar_adultos(termo, id_usuario)
        ids_membros = {linha["id_usuario"] for linha in GrupoRepository.ids_membros(id_grupo)}
        candidatos = [u for u in encontrados if u["id_usuario"] not in ids_membros]
        handles = montar_handles(candidatos)

        resultado = []
        for usuario in candidatos:
            resultado.append({
                "id": usuario["id_usuario"],
                "nome": usuario["nome"],
                "handle": handles[usuario["id_usuario"]],
                "cidade": usuario["cidade"],
                "estado": usuario["estado"],
                "foto": usuario["foto"],
                "convite_pendente": ConviteRepository.buscar_pendente(id_grupo, usuario["id_usuario"]) is not None,
            })
        return resultado
