from models.consentimento import Consentimento
from repositories.repository import ConsentimentoRepository
from services.usuario.apoio import buscar_usuario


class ListarConsentimentosService:

    @staticmethod
    def executar(id_usuario):
        buscar_usuario(id_usuario)
        return [Consentimento.formatar(c) for c in ConsentimentoRepository.listar_do_usuario(id_usuario)]
