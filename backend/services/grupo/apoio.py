from models.grupo import Grupo
import secrets
import string

from repositories.repository import GrupoRepository
from services.comum import ErroValidacao

CODIGO_CONVITE_ALFABETO = string.ascii_uppercase + string.digits


def buscar_grupo(id_grupo):
    grupo = Grupo.buscar_por_id(id_grupo)
    if not grupo:
        raise ErroValidacao("Grupo não encontrado.", status=404)
    return grupo


def exigir_membro(id_grupo, id_usuario):
    grupo = buscar_grupo(id_grupo)
    membro = GrupoRepository.papel_do_membro(id_grupo, id_usuario)
    papel = membro["papel"] if membro else None
    if papel is None:
        raise ErroValidacao("Você não participa deste grupo.", status=403)
    return grupo, papel


def exigir_admin_grupo(id_grupo, id_usuario):
    grupo, papel = exigir_membro(id_grupo, id_usuario)
    if papel != "admin":
        raise ErroValidacao("Apenas administradores do grupo podem fazer isso.", status=403)
    return grupo


def gerar_codigo_convite():
    for _ in range(10):
        codigo = "".join(secrets.choice(CODIGO_CONVITE_ALFABETO) for _ in range(10))
        if not GrupoRepository.buscar_por_codigo(codigo):
            return codigo
    raise ErroValidacao("Não foi possível gerar um código de convite. Tente novamente.", status=500)


def montar_handles(usuarios):
    raizes = {}
    contagem = {}
    for usuario in usuarios:
        raiz = (usuario["email"].split("@")[0] or "atleta").lower()
        raizes[usuario["id_usuario"]] = raiz
        contagem[raiz] = contagem.get(raiz, 0) + 1

    handles = {}
    for usuario in usuarios:
        raiz = raizes[usuario["id_usuario"]]
        if contagem[raiz] > 1:
            handles[usuario["id_usuario"]] = f"{raiz}{usuario['id_usuario'] % 100:02d}"
        else:
            handles[usuario["id_usuario"]] = raiz
    return handles
