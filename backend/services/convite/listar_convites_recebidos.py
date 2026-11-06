from repositories.repository import ConviteRepository, GrupoRepository
from utils import iso_utc


class ListarConvitesRecebidosService:

    @staticmethod
    def executar(id_usuario):
        pendentes = []
        for linha in ConviteRepository.listar_pendentes_recebidos(id_usuario):
            pendentes.append({
                "id": linha["id_convite"],
                "grupo": {
                    "id": linha["id_grupo"],
                    "nome": linha["grupo_nome"],
                    "descricao": linha["grupo_descricao"],
                    "membros": GrupoRepository.contar_membros(linha["id_grupo"])["total"],
                },
                "remetente": {"id": linha["remetente_id"], "nome": linha["remetente_nome"]},
                "data_envio": iso_utc(linha["data_envio"]),
            })
        return {
            "pendentes": pendentes,
            "meus_grupos": len(GrupoRepository.listar_do_usuario(id_usuario)),
            "convites_enviados_pendentes": ConviteRepository.contar_enviados_pendentes(id_usuario)["total"],
        }
