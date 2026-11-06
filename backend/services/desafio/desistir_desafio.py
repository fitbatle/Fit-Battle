from models.desafio_usuario import DesafioUsuario
from services.comum import ErroValidacao
from services.desafio.apoio import buscar_desafio, desafio_com_progresso


class DesistirDesafioService:

    @staticmethod
    def executar(id_usuario, id_desafio):
        inscricao = DesafioUsuario.buscar_por_id((id_desafio, id_usuario))
        if not inscricao or inscricao.status != "inscrito":
            raise ErroValidacao("Você não está inscrito neste desafio.", status=404)
        inscricao.status = "desistiu"
        inscricao.salvar()
        desafio = buscar_desafio(id_desafio)
        return desafio_com_progresso(desafio, id_usuario)
