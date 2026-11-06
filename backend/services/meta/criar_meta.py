from datetime import date

from models.meta import Meta
from repositories.repository import AtividadeRepository
from services.comum import ErroValidacao, texto_do_cliente
from services.meta.apoio import meta_com_progresso, validar_data_meta, validar_numero_meta


class CriarMetaService:

    TIPOS_PRAZO = {"curto_prazo", "longo_prazo"}
    TIPOS_METRICA = {"carga_maxima", "frequencia"}
    TITULO_MAX = 300

    @staticmethod
    def executar(id_usuario, dados):
        dados = dados or {}
        titulo = texto_do_cliente(dados.get("titulo"), "título")
        tipo = texto_do_cliente(dados.get("tipo"), "tipo")
        tipo_metrica = texto_do_cliente(dados.get("tipo_metrica"), "tipo de métrica")
        exercicio = texto_do_cliente(dados.get("exercicio"), "exercício") or None
        data_final = dados.get("data_final")

        if not titulo:
            raise ErroValidacao("Informe o título da meta.")
        if len(titulo) > CriarMetaService.TITULO_MAX:
            raise ErroValidacao(f"O título pode ter no máximo {CriarMetaService.TITULO_MAX} caracteres.")
        if tipo not in CriarMetaService.TIPOS_PRAZO:
            raise ErroValidacao("Tipo de prazo inválido. Use: curto_prazo ou longo_prazo.")
        if tipo_metrica not in CriarMetaService.TIPOS_METRICA:
            raise ErroValidacao("Tipo de métrica inválido. Use: carga_maxima ou frequencia.")
        if tipo_metrica == "carga_maxima" and not exercicio:
            raise ErroValidacao("Informe o exercício vinculado a esta meta.")
        if tipo_metrica == "frequencia":
            exercicio = None

        valor_objetivo = validar_numero_meta(dados.get("valor_objetivo"), "valor objetivo")

        valor_partida = dados.get("valor_partida")
        if valor_partida not in (None, ""):
            valor_partida = validar_numero_meta(valor_partida, "valor de partida")
        elif tipo_metrica == "carga_maxima":
            valor_partida = AtividadeRepository.maior_carga(id_usuario, exercicio.lower())["maior_carga"] or 0
        else:
            valor_partida = 0

        data_final_convertida = None
        if data_final:
            data_final_convertida = validar_data_meta(data_final)
            if data_final_convertida < date.today():
                raise ErroValidacao("O prazo da meta não pode ser uma data no passado.")

        meta = Meta(**{
            "id_usuario": id_usuario,
            "descricao": titulo,
            "tipo": tipo,
            "tipo_metrica": tipo_metrica,
            "exercicio": exercicio,
            "valor_objetivo": valor_objetivo,
            "valor_partida": valor_partida,
            "data_inicio": date.today(),
            "data_final": data_final_convertida,
            "status": "em_andamento",
        }).salvar()
        return meta_com_progresso(meta)
