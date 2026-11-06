from models.atividade import Atividade
from models.postagem import Postagem
from models.usuario import Usuario
from services.comum import ErroValidacao
from services.usuario.apoio import usuario_visivel_para

TIPOS_ALVO_FEED = {"atividade", "postagem"}


def buscar_alvo(tipo_alvo, id_alvo, id_solicitante):
    if tipo_alvo not in TIPOS_ALVO_FEED:
        raise ErroValidacao("Tipo de conteúdo inválido.")
    if tipo_alvo == "atividade":
        alvo = Atividade.buscar_por_id(id_alvo)
    else:
        alvo = Postagem.buscar_por_id(id_alvo)
    if not alvo:
        raise ErroValidacao("Conteúdo não encontrado.", status=404)
    dono = Usuario.buscar_por_id(alvo.id_usuario)
    if dono is None or not usuario_visivel_para(dono, id_solicitante):
        raise ErroValidacao("Conteúdo não encontrado.", status=404)
    return alvo
