from models.atividade import Atividade
from models.meta import Meta
from models.atividade import Atividade
from models.compartilhamento import Compartilhamento
from models.meta import Meta
from repositories.repository import ConsentimentoRepository
from services.comum import ErroValidacao, inteiro_do_cliente, texto_do_cliente
from services.medalha.listar_medalhas import ListarMedalhasService

TIPOS_CONTEUDO = {"atividade", "meta", "recorde", "medalha"}
REDES_SOCIAIS = {"whatsapp", "x", "telegram", "web_share", "copiar"}


class RegistrarCompartilhamentoService:

    @staticmethod
    def executar(id_usuario, dados):
        dados = dados or {}
        tipo_conteudo = texto_do_cliente(dados.get("tipo_conteudo"), "tipo de conteúdo")
        rede_social = texto_do_cliente(dados.get("rede_social"), "rede social")

        if tipo_conteudo not in TIPOS_CONTEUDO:
            raise ErroValidacao("Tipo de conteúdo inválido para compartilhamento.")
        if rede_social not in REDES_SOCIAIS:
            raise ErroValidacao("Rede social inválida.")

        consentimento = ConsentimentoRepository.buscar(id_usuario, "compartilhamento")
        if not consentimento or not consentimento["aceito"]:
            raise ErroValidacao(
                "Ative o consentimento de compartilhamento na página de Privacidade para continuar.",
                status=403,
            )

        id_atividade = None
        id_meta = None

        if tipo_conteudo in ("atividade", "recorde"):
            id_atividade = dados.get("id_atividade")
            if not id_atividade:
                raise ErroValidacao("Informe a atividade a compartilhar.")
            id_atividade = inteiro_do_cliente(id_atividade, "id_atividade")
            atividade = Atividade.buscar_por_id(id_atividade)
            if not atividade:
                raise ErroValidacao("Atividade não encontrada.", status=404)
            if atividade.id_usuario != id_usuario:
                raise ErroValidacao("Você só pode compartilhar as suas próprias atividades.", status=403)
        elif tipo_conteudo == "medalha":
            chave_medalha = texto_do_cliente(dados.get("chave_medalha"), "chave_medalha")
            if not chave_medalha:
                raise ErroValidacao("Informe a medalha a compartilhar.")
            medalha = ListarMedalhasService.executar(id_usuario, id_usuario)
            encontrada = next((m for m in medalha if m["chave"] == chave_medalha), None)
            if encontrada is None:
                raise ErroValidacao("Medalha não encontrada.", status=404)
            if not encontrada["conquistada"]:
                raise ErroValidacao("Esta medalha ainda não foi conquistada.")
            return Compartilhamento(
                id_usuario=id_usuario, tipo_conteudo=tipo_conteudo, rede_social=rede_social,
                chave_medalha=chave_medalha,
            ).salvar()
        else:
            id_meta = dados.get("id_meta")
            if not id_meta:
                raise ErroValidacao("Informe a meta a compartilhar.")
            id_meta = inteiro_do_cliente(id_meta, "id_meta")
            meta = Meta.buscar_por_id(id_meta)
            if not meta:
                raise ErroValidacao("Meta não encontrada.", status=404)
            if meta.id_usuario != id_usuario:
                raise ErroValidacao("Você só pode compartilhar as suas próprias metas.", status=403)

        return Compartilhamento(
            id_usuario=id_usuario, tipo_conteudo=tipo_conteudo, id_atividade=id_atividade,
            id_meta=id_meta, rede_social=rede_social,
        ).salvar()
