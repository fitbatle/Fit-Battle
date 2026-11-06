from services.comum import ErroValidacao, texto_do_cliente
from services.meta.apoio import exigir_dono_meta, meta_com_progresso, validar_data_meta, validar_numero_meta


class AtualizarMetaService:

    @staticmethod
    def executar(id_meta, id_usuario, dados):
        meta = exigir_dono_meta(id_meta, id_usuario)
        dados = dados or {}

        if dados.get("titulo") is not None:
            titulo = texto_do_cliente(dados["titulo"], "título")
            if not titulo:
                raise ErroValidacao("Informe o título da meta.")
            meta.descricao = titulo
        if dados.get("valor_objetivo") is not None:
            meta.valor_objetivo = validar_numero_meta(dados["valor_objetivo"], "valor objetivo")
        if "data_final" in dados:
            meta.data_final = validar_data_meta(dados["data_final"]) if dados["data_final"] else None

        meta.salvar()
        return meta_com_progresso(meta)
