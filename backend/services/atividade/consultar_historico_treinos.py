from models.atividade import Atividade
from repositories.repository import AtividadeRepository
from services.usuario.apoio import buscar_usuario


class ConsultarHistoricoTreinosService:

    @staticmethod
    def executar(id_usuario):
        buscar_usuario(id_usuario)
        return [Atividade.formatar(linha) for linha in AtividadeRepository.listar_do_usuario(id_usuario)]
