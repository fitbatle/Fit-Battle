from models.desafio import Desafio
from services.comum import ErroValidacao, texto_do_cliente
from services.desafio.apoio import (
    DESCRICAO_MAX,
    dict_admin_desafio,
    normalizar_exercicio_desafio,
    validar_data_desafio,
    validar_inteiro_desafio,
    validar_nome_desafio,
    validar_numero_desafio,
    validar_tipo_metrica_desafio,
)
from services.usuario.apoio import exigir_admin


class CriarDesafioService:

    @staticmethod
    def executar(id_usuario, dados):
        exigir_admin(id_usuario)
        limpos = CriarDesafioService._validar(dados or {})
        desafio = Desafio(**limpos).salvar()
        return dict_admin_desafio(desafio)

    @staticmethod
    def _validar(dados):
        nome = validar_nome_desafio(dados.get("nome"))
        descricao = texto_do_cliente(dados.get("descricao"), "descrição")
        if len(descricao) > DESCRICAO_MAX:
            raise ErroValidacao(f"A descrição pode ter no máximo {DESCRICAO_MAX} caracteres.")

        tipo_metrica = validar_tipo_metrica_desafio(dados.get("tipo_metrica"))
        exercicio = normalizar_exercicio_desafio(dados.get("exercicio"))
        valor_objetivo = validar_numero_desafio(dados.get("valor_objetivo"), "valor objetivo")
        data_inicio = validar_data_desafio(dados.get("data_inicio"), "data de início")
        data_fim = validar_data_desafio(dados.get("data_fim"), "data de fim")
        if data_fim < data_inicio:
            raise ErroValidacao("A data de fim não pode ser antes da data de início.")

        recompensa_xp = dados.get("recompensa_xp")
        recompensa_xp = validar_inteiro_desafio(recompensa_xp, "recompensa em XP") if recompensa_xp not in (None, "") else 0

        return {
            "nome": nome,
            "descricao": descricao or None,
            "exercicio": exercicio,
            "tipo_metrica": tipo_metrica,
            "valor_objetivo": valor_objetivo,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "recompensa_xp": recompensa_xp,
        }
