from models.convite import Convite
from repositories.apoio import consultar, consultar_um, converter_agregado, linha_de, linhas_de


class ConviteRepository:

    @staticmethod
    def buscar_pendente(id_grupo, id_destinatario):
        return linha_de(
            consultar_um(
                "SELECT * FROM convite "
                "WHERE id_grupo = :id_grupo AND id_destinatario = :id_destinatario AND status = 'pendente'",
                {"id_grupo": id_grupo, "id_destinatario": id_destinatario},
            ),
            Convite,
        )

    @staticmethod
    def listar_pendentes_recebidos(id_usuario):
        linhas = consultar(
            "SELECT c.id_convite, c.id_grupo, c.data_envio, "
            "g.nome AS grupo_nome, g.descricao AS grupo_descricao, "
            "u.id_usuario AS remetente_id, u.nome AS remetente_nome "
            "FROM convite c "
            "JOIN grupo g ON g.id_grupo = c.id_grupo "
            "JOIN usuario u ON u.id_usuario = c.id_remetente "
            "WHERE c.id_destinatario = :id_usuario AND c.status = 'pendente' "
            "ORDER BY c.data_envio DESC, c.id_convite DESC",
            {"id_usuario": id_usuario},
        )
        return linhas_de(linhas, Convite)

    @staticmethod
    def contar_enviados_pendentes(id_usuario):
        linha = consultar_um(
            "SELECT COUNT(*) AS total FROM convite "
            "WHERE id_remetente = :id_usuario AND status = 'pendente'",
            {"id_usuario": id_usuario},
        )
        return converter_agregado(linha, inteiros=("total",))
