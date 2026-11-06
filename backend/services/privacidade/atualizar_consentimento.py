from models.consentimento import Consentimento
from models.usuario import Usuario
from repositories.repository import ConsentimentoRepository
from services.comum import ErroValidacao
from services.privacidade.apoio import CONSENTIMENTOS_OBRIGATORIOS, CONSENTIMENTOS_OPCIONAIS
from services.usuario.apoio import buscar_usuario
from utils import agora


class AtualizarConsentimentoService:

    @staticmethod
    def executar(id_usuario, chave, aceito):
        buscar_usuario(id_usuario)

        if chave in CONSENTIMENTOS_OBRIGATORIOS:
            raise ErroValidacao(
                "Este consentimento é obrigatório para manter a conta e não pode ser alterado.",
                status=409,
            )
        if chave not in CONSENTIMENTOS_OPCIONAIS:
            raise ErroValidacao("Consentimento não encontrado.", status=404)
        if aceito is None:
            raise ErroValidacao("Informe o campo 'aceito' (true ou false).")

        linha = ConsentimentoRepository.buscar(id_usuario, chave)
        if not linha:
            raise ErroValidacao("Consentimento não encontrado.", status=404)
        registro = Consentimento.buscar_por_id(linha["id_consentimento"])

        with Consentimento.transacao():
            registro.aceito = bool(aceito)
            registro.data_atualizacao = agora()
            registro.salvar()

            if chave == "ranking_publico":
                usuario = Usuario.buscar_por_id(id_usuario)
                usuario.perfil_publico = registro.aceito
                usuario.salvar()

        return registro
