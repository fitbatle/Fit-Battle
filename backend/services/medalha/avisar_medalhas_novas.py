from models.usuario import Usuario
from repositories.repository import NotificacaoRepository
from services.medalha.apoio import medalhas_do_usuario
from services.notificacao.apoio import gerar_notificacao


class AvisarMedalhasNovasService:

    @staticmethod
    def executar(id_usuario, chaves_antes):
        usuario = Usuario.buscar_por_id(id_usuario)
        for medalha in medalhas_do_usuario(usuario):
            if not medalha["conquistada"] or medalha["chave"] in chaves_antes:
                continue
            mensagem = f'Você conquistou a medalha "{medalha["nome"]}".'
            if NotificacaoRepository.existe(id_usuario, "medalha", mensagem) is not None:
                continue
            gerar_notificacao(id_usuario, "medalha", mensagem)
