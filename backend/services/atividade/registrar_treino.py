from models.atividade import Atividade
from models.usuario import Usuario
from repositories.repository import RankingRepository
from services.atividade.apoio import (
    calcular_pontuacao,
    eh_recorde_pessoal,
    maior_carga_do_exercicio,
    marcar_recorde,
    nivel_por_xp,
    validar_teto_xp,
    validar_treino,
)
from services.medalha.apoio import chaves_conquistadas
from services.medalha.avisar_medalhas_novas import AvisarMedalhasNovasService
from services.desafio.avaliar_desafios_do_usuario import AvaliarDesafiosDoUsuarioService
from services.notificacao.apoio import gerar_notificacao
from services.usuario.apoio import buscar_usuario


def _notificar_subida_no_ranking(id_usuario, posicao_antes):
    posicao_depois = RankingRepository.minha_posicao_global(id_usuario)
    if not posicao_antes or not posicao_depois:
        return
    if posicao_depois["posicao"] < posicao_antes["posicao"]:
        gerar_notificacao(
            id_usuario,
            "subida_ranking",
            f"Você subiu para a posição #{posicao_depois['posicao']} no ranking global!",
        )


class RegistrarTreinoService:

    @staticmethod
    def executar(id_usuario, dados):
        usuario = buscar_usuario(id_usuario)
        limpos = validar_treino(dados)

        posicao_antes = RankingRepository.minha_posicao_global(id_usuario)
        medalhas_antes = chaves_conquistadas(usuario)

        limpos["pontuacao"] = calcular_pontuacao(limpos)
        validar_teto_xp(id_usuario, limpos["pontuacao"])
        recorde = eh_recorde_pessoal(id_usuario, limpos, maior_carga_do_exercicio(id_usuario, limpos))
        if recorde:
            marcar_recorde(limpos)

        with Usuario.transacao():
            atividade = Atividade(id_usuario=id_usuario, **limpos).salvar()

            usuario.xp += atividade.pontuacao
            usuario.nivel = nivel_por_xp(usuario.xp)
            usuario.salvar()

            _notificar_subida_no_ranking(id_usuario, posicao_antes)
            AvaliarDesafiosDoUsuarioService.executar(id_usuario)
            AvisarMedalhasNovasService.executar(id_usuario, medalhas_antes)

        return atividade, usuario, recorde
