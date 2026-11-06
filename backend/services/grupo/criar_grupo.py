from models.grupo import Grupo
from models.grupo_membro import GrupoMembro
from services.comum import ErroValidacao, texto_do_cliente
from services.grupo.apoio import gerar_codigo_convite


class CriarGrupoService:

    NOME_MAX = 50
    DESCRICAO_MAX = 300

    @staticmethod
    def executar(id_usuario, dados):
        dados = dados or {}
        nome = texto_do_cliente(dados.get("nome"), "nome")
        descricao = texto_do_cliente(dados.get("descricao"), "descrição") or None

        if not nome:
            raise ErroValidacao("Informe o nome do grupo.")
        if len(nome) > CriarGrupoService.NOME_MAX:
            raise ErroValidacao(f"O nome do grupo pode ter no máximo {CriarGrupoService.NOME_MAX} caracteres.")
        if descricao and len(descricao) > CriarGrupoService.DESCRICAO_MAX:
            raise ErroValidacao(f"A descrição pode ter no máximo {CriarGrupoService.DESCRICAO_MAX} caracteres.")

        codigo = gerar_codigo_convite()
        with Grupo.transacao():
            grupo = Grupo(
                nome=nome, descricao=descricao, id_criador=id_usuario, codigo_convite=codigo,
            ).salvar()
            GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=id_usuario, papel="admin").salvar()
        return grupo
