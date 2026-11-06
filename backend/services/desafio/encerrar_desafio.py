from datetime import timedelta

from services.desafio.apoio import buscar_desafio, dict_admin_desafio
from services.usuario.apoio import exigir_admin
from utils import agora


class EncerrarDesafioService:

    @staticmethod
    def executar(id_usuario, id_desafio):
        exigir_admin(id_usuario)
        desafio = buscar_desafio(id_desafio)
        ontem = agora().date() - timedelta(days=1)
        if desafio.data_fim > ontem:
            desafio.data_fim = ontem
            if desafio.data_inicio > desafio.data_fim:
                desafio.data_inicio = desafio.data_fim
            desafio.salvar()
        return dict_admin_desafio(desafio)
