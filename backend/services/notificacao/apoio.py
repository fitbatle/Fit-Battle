from models.notificacao import Notificacao
from repositories.repository import ConsentimentoRepository
from services.email.enviar_email import EnviarEmailService


def gerar_notificacao(id_usuario, tipo, mensagem, tipo_alvo=None, id_alvo=None):
    consentimento = ConsentimentoRepository.buscar(id_usuario, "notificacoes")
    if not consentimento or not consentimento["aceito"]:
        return None
    notificacao = Notificacao(
        id_usuario=id_usuario, tipo=tipo, mensagem=mensagem, tipo_alvo=tipo_alvo, id_alvo=id_alvo,
    ).salvar()
    EnviarEmailService.executar(id_usuario, mensagem)
    return notificacao
