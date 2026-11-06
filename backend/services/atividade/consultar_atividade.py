from models.usuario import Usuario
from services.atividade.apoio import buscar_atividade
from services.comum import ErroValidacao
from services.usuario.apoio import usuario_visivel_para


class ConsultarAtividadeService:

    @staticmethod
    def executar(id_atividade, id_solicitante):
        atividade = buscar_atividade(id_atividade)
        dono = Usuario.buscar_por_id(atividade.id_usuario)
        if dono is None or not usuario_visivel_para(dono, id_solicitante):
            raise ErroValidacao("Atividade não encontrada.", status=404)
        return atividade
