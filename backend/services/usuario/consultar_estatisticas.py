from repositories.repository import UsuarioRepository


class ConsultarEstatisticasService:

    @staticmethod
    def executar():
        usuarios = UsuarioRepository.listar()
        total = len(usuarios)
        media_xp = round(sum(u["xp"] for u in usuarios) / total, 2) if total else 0
        return {"total_usuarios": total, "media_xp": media_xp}
