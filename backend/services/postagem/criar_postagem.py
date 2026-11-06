from models.postagem import Postagem
from services.comum import ErroValidacao, salvar_imagem
from services.usuario.apoio import buscar_usuario


class CriarPostagemService:

    TEXTO_MAX = 1000

    @staticmethod
    def executar(id_usuario, texto, arquivo, pasta_destino):
        if id_usuario is None:
            raise ErroValidacao("Informe o usuário.", status=401)
        buscar_usuario(id_usuario)
        texto = (texto or "").strip()

        if not texto and not (arquivo and arquivo.filename):
            raise ErroValidacao("Escreva algo ou envie uma foto para publicar.")
        if len(texto) > CriarPostagemService.TEXTO_MAX:
            raise ErroValidacao(
                f"O texto pode ter no máximo {CriarPostagemService.TEXTO_MAX} caracteres."
            )

        foto = None
        if arquivo and arquivo.filename:
            foto = salvar_imagem(arquivo, pasta_destino, f"postagem_{id_usuario}")

        return Postagem(id_usuario=id_usuario, texto=texto, foto=foto).salvar()
