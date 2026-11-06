from services.comum import ErroValidacao, texto_do_cliente
from services.desafio.apoio import (
    DESCRICAO_MAX,
    buscar_desafio,
    dict_admin_desafio,
    normalizar_exercicio_desafio,
    validar_data_desafio,
    validar_inteiro_desafio,
    validar_nome_desafio,
    validar_numero_desafio,
    validar_tipo_metrica_desafio,
)
from services.usuario.apoio import exigir_admin


class AtualizarDesafioService:

    @staticmethod
    def executar(id_usuario, id_desafio, dados):
        exigir_admin(id_usuario)
        desafio = buscar_desafio(id_desafio)
        dados = dados or {}

        if dados.get("nome") is not None:
            desafio.nome = validar_nome_desafio(dados["nome"])
        if "descricao" in dados:
            descricao = texto_do_cliente(dados["descricao"], "descrição")
            if len(descricao) > DESCRICAO_MAX:
                raise ErroValidacao(f"A descrição pode ter no máximo {DESCRICAO_MAX} caracteres.")
            desafio.descricao = descricao or None
        if "exercicio" in dados:
            desafio.exercicio = normalizar_exercicio_desafio(dados["exercicio"])
        if dados.get("data_inicio") is not None:
            desafio.data_inicio = validar_data_desafio(dados["data_inicio"], "data de início")
        if dados.get("data_fim") is not None:
            desafio.data_fim = validar_data_desafio(dados["data_fim"], "data de fim")
        if dados.get("recompensa_xp") is not None:
            desafio.recompensa_xp = validar_inteiro_desafio(dados["recompensa_xp"], "recompensa em XP")
        if dados.get("tipo_metrica") is not None:
            desafio.tipo_metrica = validar_tipo_metrica_desafio(dados["tipo_metrica"])
        if dados.get("valor_objetivo") is not None:
            desafio.valor_objetivo = validar_numero_desafio(dados["valor_objetivo"], "valor objetivo")

        if desafio.data_fim < desafio.data_inicio:
            raise ErroValidacao("A data de fim não pode ser antes da data de início.")

        desafio.salvar()
        return dict_admin_desafio(desafio)
