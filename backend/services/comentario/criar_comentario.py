from models.comentario import Comentario
from services.comum import ErroValidacao, texto_do_cliente
from services.feed.apoio import buscar_alvo
from services.notificacao.apoio import gerar_notificacao
from services.usuario.apoio import buscar_usuario


class CriarComentarioService:

    TEXTO_MAX = 500

    @staticmethod
    def executar(id_usuario, tipo_alvo, id_alvo, texto):
        if id_usuario is None:
            raise ErroValidacao("Informe o usuário.", status=401)
        autor = buscar_usuario(id_usuario)
        alvo = buscar_alvo(tipo_alvo, id_alvo, id_usuario)

        texto = texto_do_cliente(texto, "texto")
        if not texto:
            raise ErroValidacao("Escreva um comentário.")
        if len(texto) > CriarComentarioService.TEXTO_MAX:
            raise ErroValidacao(
                f"O comentário pode ter no máximo {CriarComentarioService.TEXTO_MAX} caracteres."
            )

        comentario = Comentario(
            id_usuario=id_usuario, tipo_alvo=tipo_alvo, id_alvo=id_alvo, texto=texto,
        ).salvar()

        if alvo.id_usuario != id_usuario:
            rotulo = "treino" if tipo_alvo == "atividade" else "postagem"
            gerar_notificacao(
                alvo.id_usuario,
                "comentario",
                f"{autor.nome} comentou no seu {rotulo}.",
                tipo_alvo=tipo_alvo,
                id_alvo=id_alvo,
            )

        return comentario
