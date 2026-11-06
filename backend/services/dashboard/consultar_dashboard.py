from datetime import timedelta

from repositories.repository import AtividadeRepository
from services.usuario.apoio import buscar_usuario
from utils import agora, data_local, inicio_utc_do_dia_local

SEMANAS_JANELA = 8


class ConsultarDashboardService:

    @staticmethod
    def executar(id_usuario, exercicio=None):
        usuario = buscar_usuario(id_usuario)
        hoje = data_local(agora())

        semanas = ConsultarDashboardService._semanas(hoje)
        inicio_janela = semanas[0]

        pontos_por_dia, treinos_por_dia = ConsultarDashboardService._agrupar_por_dia_local(
            [
                (linha["data_registro"], linha["pontuacao"])
                for linha in AtividadeRepository.pontuacoes_desde(id_usuario, inicio_utc_do_dia_local(inicio_janela))
            ]
        )

        xp_por_semana = [
            {"inicio": semana.isoformat(), "xp": ConsultarDashboardService._soma_semana(pontos_por_dia, semana)}
            for semana in semanas
        ]
        treinos_por_semana = [
            {"inicio": semana.isoformat(), "quantidade": ConsultarDashboardService._soma_semana(treinos_por_dia, semana)}
            for semana in semanas
        ]

        distribuicao_por_tipo = AtividadeRepository.distribuicao_por_tipo(id_usuario)

        dias = [data_local(linha["data_registro"]) for linha in AtividadeRepository.datas_registro(id_usuario)]
        sequencia_atual, melhor_sequencia = ConsultarDashboardService._sequencias(dias, hoje)

        totais = AtividadeRepository.totais(id_usuario)
        total_treinos, total_tempo = totais["treinos"], totais["tempo_min"]

        exercicios = [linha["titulo"] for linha in AtividadeRepository.titulos_distintos(id_usuario)]
        exercicio_escolhido = None
        if exercicios:
            exercicio_escolhido = exercicio if exercicio in exercicios else ConsultarDashboardService._exercicio_mais_registrado(id_usuario, exercicios)

        evolucao_carga = []
        if exercicio_escolhido:
            registros = AtividadeRepository.listar_do_usuario_por_titulo(
                id_usuario, exercicio_escolhido.strip().lower()
            )
            maior = None
            for registro in registros:
                if registro["carga_kg"] is None:
                    continue
                valor = float(registro["carga_kg"])
                maior = valor if maior is None else max(maior, valor)
                evolucao_carga.append({
                    "data": registro["data_registro"].date().isoformat(),
                    "carga_maxima": maior,
                })

        return {
            "xp_por_semana": xp_por_semana,
            "treinos_por_semana": treinos_por_semana,
            "distribuicao_por_tipo": distribuicao_por_tipo,
            "sequencia_atual": sequencia_atual,
            "melhor_sequencia": melhor_sequencia,
            "totais": {
                "treinos": total_treinos,
                "tempo_min": total_tempo,
                "xp": usuario.xp,
            },
            "exercicios_disponiveis": exercicios,
            "exercicio_selecionado": exercicio_escolhido,
            "evolucao_carga": evolucao_carga,
        }

    @staticmethod
    def _exercicio_mais_registrado(id_usuario, exercicios):
        contagens = {
            linha["titulo"]: linha["quantidade"]
            for linha in AtividadeRepository.contagem_de_cargas_por_titulo(id_usuario)
        }
        return max(exercicios, key=lambda titulo: (contagens.get(titulo, 0), -exercicios.index(titulo)))

    @staticmethod
    def _agrupar_por_dia_local(linhas):
        pontos_por_dia = {}
        treinos_por_dia = {}
        for data_registro, pontuacao in linhas:
            dia = data_local(data_registro)
            pontos_por_dia[dia] = pontos_por_dia.get(dia, 0) + (pontuacao or 0)
            treinos_por_dia[dia] = treinos_por_dia.get(dia, 0) + 1
        return pontos_por_dia, treinos_por_dia

    @staticmethod
    def _semanas(hoje):
        inicio_semana_atual = hoje - timedelta(days=hoje.weekday())
        return [
            inicio_semana_atual - timedelta(weeks=i)
            for i in range(SEMANAS_JANELA - 1, -1, -1)
        ]

    @staticmethod
    def _soma_semana(mapa_por_dia, inicio_semana):
        fim_semana = inicio_semana + timedelta(days=6)
        return sum(
            valor for dia, valor in mapa_por_dia.items()
            if inicio_semana <= dia <= fim_semana
        )

    @staticmethod
    def _sequencias(dias, hoje):
        if not dias:
            return 0, 0

        dias_ordenados = sorted(set(dias))
        comprimento_do_run_que_termina_em = {dias_ordenados[0]: 1}
        melhor = 1

        for indice in range(1, len(dias_ordenados)):
            anterior = dias_ordenados[indice - 1]
            atual = dias_ordenados[indice]
            if (atual - anterior).days == 1:
                comprimento_do_run_que_termina_em[atual] = comprimento_do_run_que_termina_em[anterior] + 1
            else:
                comprimento_do_run_que_termina_em[atual] = 1
            melhor = max(melhor, comprimento_do_run_que_termina_em[atual])

        ultimo_dia = dias_ordenados[-1]
        if ultimo_dia in (hoje, hoje - timedelta(days=1)):
            sequencia_atual = comprimento_do_run_que_termina_em[ultimo_dia]
        else:
            sequencia_atual = 0

        return sequencia_atual, melhor
