from models.usuario import Usuario
from repositories.repository import UsuarioRepository
from services.comum import ErroValidacao
from services.usuario.apoio import maior_de_idade_pelos_campos


BUSCA_MINIMO_CARACTERES = 2
BUSCA_LIMITE = 20


def buscar_adultos(termo, id_solicitante):
    termo = (termo or "").strip()
    if len(termo) < BUSCA_MINIMO_CARACTERES:
        raise ErroValidacao(
            f"Digite ao menos {BUSCA_MINIMO_CARACTERES} letras para buscar."
        )
    resultados = UsuarioRepository.buscar_publicos(termo, id_solicitante)
    adultos = [u for u in resultados if maior_de_idade_pelos_campos(u["data_nascimento"], u["idade"])]
    return adultos[:BUSCA_LIMITE]


class BuscarPerfisService:

    BUSCA_MINIMO_CARACTERES = 2
    BUSCA_LIMITE = 20

    @staticmethod
    def executar(termo, id_solicitante):
        return [Usuario.formatar_publico(u) for u in buscar_adultos(termo, id_solicitante)]
