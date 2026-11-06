from models.desafio import Desafio
from repositories.repository import DesafioRepository
from services.desafio.apoio import desafio_com_progresso
from utils import agora


class ListarDesafiosAtivosService:

    @staticmethod
    def executar(id_usuario):
        hoje = agora().date()
        desafios = [Desafio.buscar_por_id(linha["id_desafio"]) for linha in DesafioRepository.listar_ativos(hoje)]
        return [desafio_com_progresso(d, id_usuario) for d in desafios]
