from services.comum import ErroValidacao, salvar_imagem
from services.usuario.apoio import buscar_usuario


class AtualizarFotoPerfilService:

    @staticmethod
    def executar(id_usuario, arquivo, pasta_destino):
        usuario = buscar_usuario(id_usuario)

        if arquivo is None or not arquivo.filename:
            raise ErroValidacao("Nenhuma imagem enviada.")

        usuario.foto = salvar_imagem(
            arquivo, pasta_destino, f"usuario_{id_usuario}", apagar_existentes=True
        )
        return usuario.salvar()
