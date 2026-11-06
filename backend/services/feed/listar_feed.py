from models.atividade import Atividade
from models.postagem import Postagem
from models.usuario import Usuario
from repositories.repository import (
    AtividadeRepository,
    ComentarioRepository,
    CurtidaRepository,
    PostagemRepository,
)


class ListarFeedService:

    LIMITE_PADRAO = 30
    LIMITE_MAXIMO = 100

    @staticmethod
    def executar(id_usuario_atual, limite=LIMITE_PADRAO):
        limite = ListarFeedService._limite(limite)

        atividades = AtividadeRepository.listar_publicas(limite, id_usuario_atual)
        postagens = PostagemRepository.listar_publicas(limite, id_usuario_atual)

        itens = []
        for a in atividades:
            itens.append({
                "tipo": "atividade", "id": a["id_atividade"], "id_usuario": a["id_usuario"],
                "data_registro": a["data_registro"], "objeto": a,
            })
        for p in postagens:
            itens.append({
                "tipo": "postagem", "id": p["id_postagem"], "id_usuario": p["id_usuario"],
                "data_registro": p["data_registro"], "objeto": p,
            })

        itens.sort(key=lambda i: i["data_registro"], reverse=True)
        itens = itens[:limite]

        ids_atividade = [i["id"] for i in itens if i["tipo"] == "atividade"]
        ids_postagem = [i["id"] for i in itens if i["tipo"] == "postagem"]

        curtidas_atividade = CurtidaRepository.contar_em_lote("atividade", ids_atividade)
        curtidas_postagem = CurtidaRepository.contar_em_lote("postagem", ids_postagem)
        comentarios_atividade = ComentarioRepository.contar_em_lote("atividade", ids_atividade)
        comentarios_postagem = ComentarioRepository.contar_em_lote("postagem", ids_postagem)

        curti_atividade = set()
        curti_postagem = set()
        if id_usuario_atual:
            curti_atividade = {
                linha["id_alvo"] for linha in CurtidaRepository.curtidos_pelo_usuario(
                    id_usuario_atual, "atividade", ids_atividade
                )
            }
            curti_postagem = {
                linha["id_alvo"] for linha in CurtidaRepository.curtidos_pelo_usuario(
                    id_usuario_atual, "postagem", ids_postagem
                )
            }

        ids_donos = {i["id_usuario"] for i in itens}
        donos = {
            uid: Usuario.buscar_por_id(uid)
            for uid in ids_donos
        }

        resultado = []
        for i in itens:
            dono = donos.get(i["id_usuario"])
            if i["tipo"] == "atividade":
                base = Atividade.formatar(i["objeto"])
            else:
                base = Postagem.formatar(i["objeto"])
            base["tipo_conteudo"] = i["tipo"]
            base["usuario"] = {
                "id": dono.id_usuario if dono else None,
                "nome": dono.nome if dono else "Usuário removido",
                "foto": dono.foto if dono else None,
            }
            if i["tipo"] == "atividade":
                base["curtidas"] = curtidas_atividade.get(i["id"], 0)
                base["comentarios"] = comentarios_atividade.get(i["id"], 0)
                base["curti"] = i["id"] in curti_atividade
            else:
                base["curtidas"] = curtidas_postagem.get(i["id"], 0)
                base["comentarios"] = comentarios_postagem.get(i["id"], 0)
                base["curti"] = i["id"] in curti_postagem
            resultado.append(base)

        return resultado

    @staticmethod
    def _limite(valor):
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            return ListarFeedService.LIMITE_PADRAO
        return max(1, min(numero, ListarFeedService.LIMITE_MAXIMO))
