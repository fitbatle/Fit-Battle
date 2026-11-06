from models.consentimento import Consentimento
from repositories.apoio import consultar, consultar_um, linha_de, linhas_de


class ConsentimentoRepository:

    @staticmethod
    def listar_do_usuario(id_usuario):
        linhas = consultar(
            "SELECT * FROM consentimento WHERE id_usuario = :id_usuario "
            "ORDER BY obrigatorio DESC, id_consentimento",
            {"id_usuario": id_usuario},
        )
        return linhas_de(linhas, Consentimento)

    @staticmethod
    def buscar(id_usuario, chave):
        return linha_de(
            consultar_um(
                "SELECT * FROM consentimento WHERE id_usuario = :id_usuario AND chave = :chave",
                {"id_usuario": id_usuario, "chave": chave},
            ),
            Consentimento,
        )
