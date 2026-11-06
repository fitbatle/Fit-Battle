from models.notificacao import Notificacao
from repositories.apoio import consultar, consultar_um, converter_agregado, executar_comando, linhas_de


class NotificacaoRepository:

    @staticmethod
    def existe(id_usuario, tipo, mensagem):
        return consultar_um(
            "SELECT id_notif FROM notificacao "
            "WHERE id_usuario = :id_usuario AND tipo = :tipo AND mensagem = :mensagem",
            {"id_usuario": id_usuario, "tipo": tipo, "mensagem": mensagem},
        )

    @staticmethod
    def listar_do_usuario(id_usuario, limite=50):
        linhas = consultar(
            "SELECT * FROM notificacao WHERE id_usuario = :id_usuario "
            "ORDER BY data_envio DESC, id_notif DESC LIMIT :limite",
            {"id_usuario": id_usuario, "limite": limite},
        )
        return linhas_de(linhas, Notificacao)

    @staticmethod
    def contar_nao_lidas(id_usuario):
        linha = consultar_um(
            "SELECT COUNT(*) AS total FROM notificacao WHERE id_usuario = :id_usuario AND lida = 0",
            {"id_usuario": id_usuario},
        )
        return converter_agregado(linha, inteiros=("total",))

    @staticmethod
    def marcar_todas_lidas(id_usuario):
        executar_comando(
            "UPDATE notificacao SET lida = 1 WHERE id_usuario = :id_usuario AND lida = 0",
            {"id_usuario": id_usuario},
        )
