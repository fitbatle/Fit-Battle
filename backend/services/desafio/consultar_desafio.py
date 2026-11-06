from services.desafio.apoio import buscar_desafio, desafio_com_progresso


class ConsultarDesafioService:

    @staticmethod
    def executar(id_desafio, id_usuario):
        desafio = buscar_desafio(id_desafio)
        return desafio_com_progresso(desafio, id_usuario)
