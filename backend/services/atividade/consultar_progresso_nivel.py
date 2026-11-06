from services.atividade.apoio import progresso_de_nivel


class ConsultarProgressoNivelService:

    @staticmethod
    def executar(xp):
        return progresso_de_nivel(xp)
