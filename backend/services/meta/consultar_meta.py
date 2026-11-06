from repositories.repository import AtividadeRepository
from services.meta.apoio import exigir_dono_meta, meta_com_progresso
from utils import iso_utc


class ConsultarMetaService:

    @staticmethod
    def executar(id_meta, id_usuario):
        meta = exigir_dono_meta(id_meta, id_usuario)
        dado = meta_com_progresso(meta)
        dado["historico"] = ConsultarMetaService._historico(meta)
        return dado

    @staticmethod
    def _historico(meta):
        if meta.tipo_metrica != "carga_maxima" or not meta.exercicio:
            return []

        atividades = AtividadeRepository.listar_do_usuario_por_titulo(
            meta.id_usuario, meta.exercicio.strip().lower()
        )
        historico = []
        anterior = None
        for indice, atividade in enumerate(atividades, start=1):
            carga = float(atividade["carga_kg"]) if atividade["carga_kg"] is not None else None
            if anterior is None:
                rotulo = "Registro inicial da meta"
            elif carga == anterior:
                rotulo = "Carga mantida"
            elif carga is not None and anterior is not None and carga > anterior:
                rotulo = f"+{carga - anterior:g} kg em relação ao anterior"
            else:
                rotulo = f"{(carga - anterior):g} kg em relação ao anterior" if carga is not None and anterior is not None else "—"

            historico.append({
                "sessao": indice,
                "carga_kg": carga,
                "repeticoes": atividade["repeticoes"],
                "data_registro": iso_utc(atividade["data_registro"]),
                "rotulo": rotulo,
            })
            anterior = carga
        return historico
