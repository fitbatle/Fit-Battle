from models.grupo import Grupo
from repositories.repository import GrupoRepository


class ListarMeusGruposService:

    @staticmethod
    def executar(id_usuario):
        resultado = []
        for linha in GrupoRepository.listar_do_usuario(id_usuario):
            dado = Grupo.formatar(linha)
            dado["meu_papel"] = linha["papel"]
            dado["membros"] = GrupoRepository.contar_membros(linha["id_grupo"])["total"]
            resultado.append(dado)
        return resultado
