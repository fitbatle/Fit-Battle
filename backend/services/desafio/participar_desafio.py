from models.desafio_usuario import DesafioUsuario
from services.comum import ErroValidacao
from services.desafio.apoio import buscar_desafio, desafio_com_progresso
from utils import agora


class ParticiparDesafioService:

    @staticmethod
    def executar(id_usuario, id_desafio):
        desafio = buscar_desafio(id_desafio)
        hoje = agora().date()
        if desafio.data_fim < hoje:
            raise ErroValidacao("Este desafio já foi encerrado.")

        inscricao = DesafioUsuario.buscar_por_id((id_desafio, id_usuario))
        if inscricao and inscricao.status == "inscrito":
            raise ErroValidacao("Você já está inscrito neste desafio.", status=409)
        if inscricao and inscricao.status == "concluido":
            raise ErroValidacao("Você já concluiu este desafio.", status=409)
        if inscricao:
            inscricao.status = "inscrito"
            inscricao.concluido_em = None
            inscricao.salvar()
        else:
            DesafioUsuario(id_desafio=id_desafio, id_usuario=id_usuario, status="inscrito").salvar()
        return desafio_com_progresso(desafio, id_usuario)
