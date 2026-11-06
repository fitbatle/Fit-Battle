from models.convite import Convite
from repositories.repository import GrupoRepository
from services.comum import ErroValidacao, inteiro_do_cliente
from services.grupo.apoio import buscar_grupo, exigir_membro
from services.notificacao.apoio import gerar_notificacao
from services.usuario.apoio import buscar_usuario
from utils import ConflitoDeDados


class ConvidarParaGrupoService:

    @staticmethod
    def executar(id_grupo, id_remetente, id_destinatario):
        exigir_membro(id_grupo, id_remetente)
        destinatario = buscar_usuario(
            inteiro_do_cliente(id_destinatario, "id_usuario") if id_destinatario is not None else None
        )
        if GrupoRepository.papel_do_membro(id_grupo, destinatario.id_usuario) is not None:
            raise ErroValidacao("Esse usuário já é membro do grupo.", status=409)
        try:
            convite = Convite(
                id_grupo=id_grupo, id_remetente=id_remetente, id_destinatario=destinatario.id_usuario,
            ).salvar()
        except ConflitoDeDados:
            raise ErroValidacao("Já existe um convite pendente para esse usuário.", status=409)

        grupo = buscar_grupo(id_grupo)
        gerar_notificacao(
            destinatario.id_usuario,
            "convite_recebido",
            f"Você recebeu um convite para o grupo {grupo.nome}.",
            tipo_alvo="convite",
            id_alvo=convite.id_convite,
        )
        return convite
